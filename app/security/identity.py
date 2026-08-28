from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class IdentityAssurance(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class IdentityAuthorizationError(ValueError):
    pass


class PatientIdentityContext(BaseModel):
    patient_id: str | None = None
    assurance: IdentityAssurance = IdentityAssurance.UNVERIFIED


def require_verified_patient(
    identity: PatientIdentityContext,
    *,
    requested_patient_id: str,
) -> None:
    if identity.assurance is not IdentityAssurance.VERIFIED:
        raise IdentityAuthorizationError("Patient identity is not verified")
    if identity.patient_id is None or identity.patient_id != requested_patient_id:
        raise IdentityAuthorizationError("Requested patient does not match verified identity")
