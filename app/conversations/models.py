from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Intent(StrEnum):
    NEW_APPOINTMENT = "NEW_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    CONFIRM_APPOINTMENT = "CONFIRM_APPOINTMENT"
    CHECK_APPOINTMENT = "CHECK_APPOINTMENT"
    FIND_DOCTOR = "FIND_DOCTOR"
    FIND_CLINIC = "FIND_CLINIC"
    SERVICE_INFORMATION = "SERVICE_INFORMATION"
    PRICE_INFORMATION = "PRICE_INFORMATION"
    CLINIC_INFORMATION = "CLINIC_INFORMATION"
    PREPARATION_INFORMATION = "PREPARATION_INFORMATION"
    COMPLAINT = "COMPLAINT"
    CALLBACK_REQUEST = "CALLBACK_REQUEST"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"
    EMERGENCY_ESCALATION = "EMERGENCY_ESCALATION"
    UNKNOWN_CLINIC_INTENT = "UNKNOWN_CLINIC_INTENT"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


class DialogState(StrEnum):
    NEW = "NEW"
    INITIALIZING = "INITIALIZING"
    GREETING = "GREETING"
    LISTENING = "LISTENING"
    UNDERSTANDING = "UNDERSTANDING"
    POLICY_CHECK = "POLICY_CHECK"
    PLANNING = "PLANNING"
    COLLECTING_INFO = "COLLECTING_INFO"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    RESPONDING = "RESPONDING"
    HANDOFF = "HANDOFF"
    FALLBACK = "FALLBACK"
    CLOSING = "CLOSING"
    ENDED = "ENDED"


class PatientRef(BaseModel):
    external_patient_id: str | None = None
    phone: str | None = None
    identity_verified: bool = False


class PendingAction(BaseModel):
    action: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = True
    confirmed: bool = False


class OfferedOption(BaseModel):
    option_id: str
    label: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    call_id: str
    conversation_id: str
    trace_id: str

    dialog_state: DialogState = DialogState.NEW
    intent: Intent | None = None
    intent_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    patient: PatientRef = Field(default_factory=PatientRef)

    clinic_id: str | None = None
    service_id: str | None = None
    doctor_id: str | None = None
    appointment_id: str | None = None
    authorized_appointment_ids: frozenset[str] = Field(default_factory=frozenset)

    preferred_date: str | None = None
    preferred_time: str | None = None

    collected_fields: dict[str, Any] = Field(default_factory=dict)
    confirmed_fields: dict[str, Any] = Field(default_factory=dict)

    offered_options: list[OfferedOption] = Field(default_factory=list)
    selected_option_id: str | None = None

    pending_action: PendingAction | None = None

    understanding_attempts: int = Field(default=0, ge=0)
    tool_attempts: int = Field(default=0, ge=0)

    conversation_summary: str = ""
    handoff_required: bool = False
    handoff_reason: str | None = None

    def require_handoff(self, reason: str) -> None:
        self.handoff_required = True
        self.handoff_reason = reason
        self.dialog_state = DialogState.HANDOFF

    def select_offered_option(self, option_id: str) -> OfferedOption:
        for option in self.offered_options:
            if option.option_id == option_id:
                self.selected_option_id = option_id
                return option
        raise ValueError("Unknown offered option")
