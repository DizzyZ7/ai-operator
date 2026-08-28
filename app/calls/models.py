from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CallOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    HANDED_OFF = "HANDED_OFF"
    ABANDONED = "ABANDONED"
    FAILED = "FAILED"


class AppointmentSummary(BaseModel):
    appointment_id: str | None = None
    clinic_id: str | None = None
    service_id: str | None = None
    doctor_id: str | None = None
    starts_at: str | None = None


class CallSummary(BaseModel):
    reason: str
    patient_request: str
    result: str
    appointment: AppointmentSummary | None = None
    unresolved_questions: list[str] = Field(default_factory=list)
    handoff: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
