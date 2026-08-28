from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class AppointmentOperationStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"


class SlotQuery(BaseModel):
    service_id: str = Field(min_length=1)
    starts_after: datetime
    ends_before: datetime
    clinic_id: str | None = None
    doctor_id: str | None = None
    limit: int = Field(default=3, ge=1, le=20)

    @model_validator(mode="after")
    def validate_window(self) -> SlotQuery:
        if self.ends_before <= self.starts_after:
            raise ValueError("ends_before must be later than starts_after")
        return self


class AvailableSlot(BaseModel):
    slot_id: str = Field(min_length=1)
    clinic_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    doctor_id: str | None = None
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_window(self) -> AvailableSlot:
        if self.ends_at <= self.starts_at:
            raise ValueError("slot end must be later than slot start")
        return self


class CreateAppointmentRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    slot_id: str = Field(min_length=1)
    clinic_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    doctor_id: str | None = None


class RescheduleAppointmentRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    appointment_id: str = Field(min_length=1)
    target_slot_id: str = Field(min_length=1)


class CancelAppointmentRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    appointment_id: str = Field(min_length=1)


class AppointmentOperationResult(BaseModel):
    status: AppointmentOperationStatus
    appointment_id: str | None = None
    external_reference: str | None = None
    error_code: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status is AppointmentOperationStatus.SUCCEEDED
