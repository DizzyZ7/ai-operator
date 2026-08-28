from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.providers.business import MedicalSystemProvider
from app.security.identity import (
    IdentityAssurance,
    IdentityAuthorizationError,
    PatientIdentityContext,
    require_verified_patient,
)
from app.tools.catalog import TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolExecutionContext, ToolResult


class GetPatientAppointmentsTool:
    spec = TOOL_SPECS_BY_NAME["get_patient_appointments"]

    def __init__(self, medical_system: MedicalSystemProvider) -> None:
        self._medical_system = medical_system

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        patient_id = arguments.get("patient_id")
        if not isinstance(patient_id, str) or not patient_id:
            return ToolResult(success=False, error_code="invalid_patient_id")

        identity = PatientIdentityContext(
            patient_id=context.verified_patient_id,
            assurance=(
                IdentityAssurance.VERIFIED
                if context.identity_verified
                else IdentityAssurance.UNVERIFIED
            ),
        )
        try:
            require_verified_patient(identity, requested_patient_id=patient_id)
        except IdentityAuthorizationError:
            return ToolResult(success=False, error_code="patient_identity_not_authorized")

        try:
            appointments = await self._medical_system.get_patient_appointments(patient_id)
        except TimeoutError:
            return ToolResult(
                success=False,
                error_code="medical_system_timeout",
                retryable=True,
            )
        except ValidationError:
            return ToolResult(
                success=False,
                error_code="invalid_patient_appointments_response",
            )

        if any(appointment.patient_id != patient_id for appointment in appointments):
            return ToolResult(
                success=False,
                error_code="provider_patient_scope_violation",
            )

        return ToolResult(
            success=True,
            data={
                "appointments": [
                    appointment.model_dump(mode="json") for appointment in appointments
                ]
            },
        )
