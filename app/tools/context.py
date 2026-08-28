from __future__ import annotations

from app.conversations.models import ConversationState
from app.tools.contracts import ToolExecutionContext


def build_tool_execution_context(
    state: ConversationState,
    *,
    correlation_id: str,
    permissions: frozenset[str],
    idempotency_key: str | None = None,
) -> ToolExecutionContext:
    allowed_slot_ids = frozenset(
        slot_id
        for option in state.offered_options
        if isinstance((slot_id := option.payload.get("slot_id")), str)
    )

    return ToolExecutionContext(
        call_id=state.call_id,
        conversation_id=state.conversation_id,
        correlation_id=correlation_id,
        permissions=permissions,
        idempotency_key=idempotency_key,
        identity_verified=state.patient.identity_verified,
        verified_patient_id=state.patient.external_patient_id,
        resource_grants={
            "slot_id": allowed_slot_ids,
            "appointment_id": state.authorized_appointment_ids,
        },
    )
