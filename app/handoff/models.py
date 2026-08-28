from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.conversations.models import ConversationState, Intent


class HandoffPatient(BaseModel):
    external_patient_id: str | None = None
    phone: str | None = None
    identity_verified: bool = False


class HandoffPackage(BaseModel):
    call_id: str
    conversation_id: str
    patient: HandoffPatient
    intent: Intent | None = None
    summary: str
    collected_information: dict[str, Any] = Field(default_factory=dict)
    actions_already_attempted: list[str] = Field(default_factory=list)
    reason_for_handoff: str


def build_handoff_package(
    state: ConversationState,
    *,
    actions_already_attempted: list[str] | None = None,
) -> HandoffPackage:
    reason = state.handoff_reason or "unspecified_handoff"
    return HandoffPackage(
        call_id=state.call_id,
        conversation_id=state.conversation_id,
        patient=HandoffPatient(
            external_patient_id=state.patient.external_patient_id,
            phone=state.patient.phone,
            identity_verified=state.patient.identity_verified,
        ),
        intent=state.intent,
        summary=state.conversation_summary,
        collected_information=dict(state.collected_fields),
        actions_already_attempted=actions_already_attempted or [],
        reason_for_handoff=reason,
    )
