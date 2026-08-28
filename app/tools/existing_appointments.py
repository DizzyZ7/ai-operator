from __future__ import annotations

from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ValidationError

from app.appointments.access import (
    AppointmentAuthorizationError,
    build_access_context,
    require_appointment_access,
)
from app.appointments.models import (
    AppointmentOperationResult,
    AppointmentOperationStatus,
    CancelAppointmentRequest,
    ConfirmAppointmentRequest,
    RescheduleAppointmentRequest,
)
from app.idempotency.models import IdempotencyStatus
from app.idempotency.store import IdempotencyConflict, IdempotencyStore
from app.providers.scheduling import SchedulingProvider
from app.security.identity import IdentityAuthorizationError
from app.tools.catalog import TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolExecutionContext, ToolResult
from app.tools.fingerprint import stable_request_fingerprint

MutationRequest = RescheduleAppointmentRequest | CancelAppointmentRequest | ConfirmAppointmentRequest
MutationCall = Callable[[MutationRequest, str], Awaitable[AppointmentOperationResult]]


def _authorize_existing_appointment(
    context: ToolExecutionContext,
    *,
    patient_id: str,
    appointment_id: str,
) -> ToolResult | None:
    access = build_access_context(
        patient_id=context.verified_patient_id,
        identity_verified=context.identity_verified,
        appointment_ids=context.resource_grants.get("appointment_id", frozenset()),
    )
    try:
        require_appointment_access(
            access,
            patient_id=patient_id,
            appointment_id=appointment_id,
        )
    except (AppointmentAuthorizationError, IdentityAuthorizationError):
        return ToolResult(
            success=False,
            error_code="appointment_not_authorized_for_patient",
        )
    return None


def _authorize_slot(
    context: ToolExecutionContext,
    *,
    slot_id: str,
) -> ToolResult | None:
    if slot_id not in context.resource_grants.get("slot_id", frozenset()):
        return ToolResult(success=False, error_code="slot_not_authorized_for_call")
    return None


def _map_operation_result(result: AppointmentOperationResult) -> ToolResult:
    default_errors = {
        AppointmentOperationStatus.NOT_FOUND: "appointment_target_not_found",
        AppointmentOperationStatus.CONFLICT: "appointment_conflict",
        AppointmentOperationStatus.REJECTED: "appointment_rejected",
    }
    return ToolResult(
        success=result.succeeded,
        data={"appointment_id": result.appointment_id} if result.appointment_id else {},
        error_code=result.error_code or default_errors.get(result.status),
        retryable=False,
        external_reference=result.external_reference,
    )


class _ExistingAppointmentMutation:
    spec_name: str
    request_model: type[BaseModel]

    def __init__(
        self,
        scheduling: SchedulingProvider,
        idempotency: IdempotencyStore,
    ) -> None:
        self._scheduling = scheduling
        self._idempotency = idempotency
        self.spec = TOOL_SPECS_BY_NAME[self.spec_name]

    async def _execute_mutation(
        self,
        context: ToolExecutionContext,
        request: MutationRequest,
        call: MutationCall,
    ) -> ToolResult:
        if context.idempotency_key is None:
            return ToolResult(success=False, error_code="idempotency_key_missing")

        patient_id = request.patient_id
        appointment_id = request.appointment_id
        unauthorized = _authorize_existing_appointment(
            context,
            patient_id=patient_id,
            appointment_id=appointment_id,
        )
        if unauthorized is not None:
            return unauthorized

        if isinstance(request, RescheduleAppointmentRequest):
            unauthorized_slot = _authorize_slot(
                context,
                slot_id=request.target_slot_id,
            )
            if unauthorized_slot is not None:
                return unauthorized_slot

        fingerprint = stable_request_fingerprint(request.model_dump(mode="json"))
        try:
            claim = await self._idempotency.claim(
                key=context.idempotency_key,
                operation=self.spec.name,
                request_fingerprint=fingerprint,
            )
        except IdempotencyConflict:
            return ToolResult(success=False, error_code="idempotency_conflict")

        if not claim.created:
            if claim.record.status is IdempotencyStatus.COMPLETED:
                return ToolResult.model_validate(claim.record.result)
            return ToolResult(
                success=False,
                error_code="mutation_reconciliation_required",
                retryable=False,
            )

        try:
            result = await call(request, context.idempotency_key)
        except TimeoutError:
            return ToolResult(
                success=False,
                error_code="mutation_outcome_unknown",
                retryable=False,
            )

        tool_result = _map_operation_result(result)
        await self._idempotency.complete(
            key=context.idempotency_key,
            result=tool_result.model_dump(mode="json"),
        )
        return tool_result


class RescheduleAppointmentTool(_ExistingAppointmentMutation):
    spec_name = "reschedule_appointment"
    request_model = RescheduleAppointmentRequest

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        try:
            request = RescheduleAppointmentRequest.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_reschedule_request")

        async def call(
            mutation_request: MutationRequest,
            idempotency_key: str,
        ) -> AppointmentOperationResult:
            assert isinstance(mutation_request, RescheduleAppointmentRequest)
            return await self._scheduling.reschedule_appointment(
                mutation_request,
                idempotency_key=idempotency_key,
            )

        return await self._execute_mutation(context, request, call)


class CancelAppointmentTool(_ExistingAppointmentMutation):
    spec_name = "cancel_appointment"
    request_model = CancelAppointmentRequest

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        try:
            request = CancelAppointmentRequest.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_cancel_request")

        async def call(
            mutation_request: MutationRequest,
            idempotency_key: str,
        ) -> AppointmentOperationResult:
            assert isinstance(mutation_request, CancelAppointmentRequest)
            return await self._scheduling.cancel_appointment(
                mutation_request,
                idempotency_key=idempotency_key,
            )

        return await self._execute_mutation(context, request, call)


class ConfirmAppointmentTool(_ExistingAppointmentMutation):
    spec_name = "confirm_appointment"
    request_model = ConfirmAppointmentRequest

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        try:
            request = ConfirmAppointmentRequest.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_confirm_request")

        async def call(
            mutation_request: MutationRequest,
            idempotency_key: str,
        ) -> AppointmentOperationResult:
            assert isinstance(mutation_request, ConfirmAppointmentRequest)
            return await self._scheduling.confirm_appointment(
                mutation_request,
                idempotency_key=idempotency_key,
            )

        return await self._execute_mutation(context, request, call)
