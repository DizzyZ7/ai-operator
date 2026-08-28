import pytest

from app.appointments.access import (
    AppointmentAuthorizationError,
    build_access_context,
    require_appointment_access,
)
from app.security.identity import IdentityAuthorizationError


def test_unverified_identity_cannot_access_existing_appointment() -> None:
    access = build_access_context(
        patient_id="patient-1",
        identity_verified=False,
        appointment_ids=frozenset({"appointment-1"}),
    )

    with pytest.raises(IdentityAuthorizationError):
        require_appointment_access(
            access,
            patient_id="patient-1",
            appointment_id="appointment-1",
        )


def test_verified_patient_cannot_access_someone_elses_appointment() -> None:
    access = build_access_context(
        patient_id="patient-1",
        identity_verified=True,
        appointment_ids=frozenset({"appointment-1"}),
    )

    with pytest.raises(AppointmentAuthorizationError):
        require_appointment_access(
            access,
            patient_id="patient-1",
            appointment_id="appointment-other",
        )


def test_requested_patient_must_equal_verified_identity() -> None:
    access = build_access_context(
        patient_id="patient-1",
        identity_verified=True,
        appointment_ids=frozenset({"appointment-1"}),
    )

    with pytest.raises(IdentityAuthorizationError):
        require_appointment_access(
            access,
            patient_id="patient-2",
            appointment_id="appointment-1",
        )
