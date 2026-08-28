from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.appointments.models import (
    AppointmentOperationStatus,
    CreateAppointmentRequest,
    SlotQuery,
)
from app.idempotency.models import IdempotencyStatus
from app.idempotency.store import IdempotencyConflict, IdempotencyStore
from app.providers.scheduling import SchedulingProvider
from app.tools.catalog import TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolExecutionContext, ToolResult
from app.tools.fingerprint import stable_request_fingerprint


class GetAvailableSlotsTool:
    spec = TOOL_SPECS_BY_NAME["get_available_slots"]

    def __init__(self, scheduling: SchedulingProvider) -> None:
        self._scheduling = scheduling

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        del context
        try:
            query = SlotQuery.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_slot_query")

        try:
            slots = await self._scheduling.get_available_slots(query)
        except TimeoutError:
            return ToolResult(
                success=False,
                error_code="scheduling_timeout",
                retryable=True,
            )

        return ToolResult(
            success=True,
            data={"slots": [slot.model_dump(mode="json") for slot in slots]},
        )


class CreateAppointmentTool:
    spec = TOOL_SPECS_BY_NAME["create_appointment"]

    def __init__(
        self,
        scheduling: SchedulingProvider,
        idempotency: IdempotencyStore,
    ) -> None:
        self._scheduling = scheduling
        self._idempotency = idempotency

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        if context.idempotency_key is None:
            return ToolResult(success=False, error_code="idempotency_key_missing")

        try:
            request = CreateAppointmentRequest.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_create_appointment_request")

        allowed_slot_ids = context.resource_grants.get("slot_id", frozenset())
        if request.slot_id not in allowed_slot_ids:
            return ToolResult(success=False, error_code="slot_not_authorized_for_call")

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
            result = await self._scheduling.create_appointment(
                request,
                idempotency_key=context.idempotency_key,
            )
        except TimeoutError:
            return ToolResult(
                success=False,
                error_code="mutation_outcome_unknown",
                retryable=False,
            )

        default_errors = {
            AppointmentOperationStatus.NOT_FOUND: "appointment_target_not_found",
            AppointmentOperationStatus.CONFLICT: "slot_conflict",
            AppointmentOperationStatus.REJECTED: "appointment_rejected",
        }
        error_code = result.error_code or default_errors.get(result.status)

        tool_result = ToolResult(
            success=result.status is AppointmentOperationStatus.SUCCEEDED,
            data={"appointment_id": result.appointment_id} if result.appointment_id else {},
            error_code=error_code,
            retryable=False,
            external_reference=result.external_reference,
        )
        await self._idempotency.complete(
            key=context.idempotency_key,
            result=tool_result.model_dump(mode="json"),
        )
        return tool_result
