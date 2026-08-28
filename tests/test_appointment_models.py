import pytest
from pydantic import ValidationError

from app.appointments.models import AppointmentOperationResult, AppointmentOperationStatus


def test_successful_appointment_operation_requires_canonical_id() -> None:
    with pytest.raises(ValidationError):
        AppointmentOperationResult(status=AppointmentOperationStatus.SUCCEEDED)


def test_non_success_operation_may_have_no_appointment_id() -> None:
    result = AppointmentOperationResult(status=AppointmentOperationStatus.CONFLICT)
    assert result.succeeded is False
