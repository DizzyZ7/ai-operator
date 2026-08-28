from __future__ import annotations

from pydantic import BaseModel, Field

from app.security.identity import (
    IdentityAssurance,
    PatientIdentityContext,
    require_verified_patient,
)


class AppointmentAccessContext(BaseModel):
    identity: PatientIdentityContext
    authorized_appointment_ids: frozenset[str] = Field(default_factory=frozenset)


class AppointmentAuthorizationError(ValueError):
    pass


def require_appointment_access(
    access: AppointmentAccessContext,
    *,
    patient_id: str,
    appointment_id: str,
) -> None:
    require_verified_patient(access.identity, requested_patient_id=patient_id)
    if appointment_id not in access.authorized_appointment_ids:
        raise AppointmentAuthorizationError(
            "Appointment is not authorized for the verified patient context"
        )


def build_access_context(
    *,
    patient_id: str | None,
    identity_verified: bool,
    appointment_ids: frozenset[str],
) -> AppointmentAccessContext:
    return AppointmentAccessContext(
        identity=PatientIdentityContext(
            patient_id=patient_id,
            assurance=(
                IdentityAssurance.VERIFIED
                if identity_verified
                else IdentityAssurance.UNVERIFIED
            ),
        ),
        authorized_appointment_ids=appointment_ids,
    )
