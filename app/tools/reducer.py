from __future__ import annotations

from pydantic import ValidationError

from app.appointments.models import AvailableSlot
from app.appointments.offers import build_slot_options
from app.conversations.models import ConversationState, DialogState
from app.tools.contracts import ToolResult


class TrustedToolResultError(ValueError):
    pass


def apply_tool_result(
    state: ConversationState,
    *,
    tool_name: str,
    result: ToolResult,
) -> ConversationState:
    updated = state.model_copy(deep=True)
    updated.pending_action = None

    if not result.success:
        updated.collected_fields["last_tool_error"] = result.error_code or "tool_failed"
        updated.dialog_state = DialogState.PLANNING
        return updated

    if tool_name == "get_available_slots":
        raw_slots = result.data.get("slots")
        if not isinstance(raw_slots, list):
            raise TrustedToolResultError("Slot tool succeeded without a slots list")

        try:
            slots = [AvailableSlot.model_validate(item) for item in raw_slots]
        except ValidationError as exc:
            raise TrustedToolResultError("Scheduling returned malformed slot data") from exc

        updated.offered_options = build_slot_options(slots)
        updated.dialog_state = DialogState.RESPONDING
        return updated

    if tool_name == "create_appointment":
        appointment_id = result.data.get("appointment_id")
        if not isinstance(appointment_id, str) or not appointment_id:
            raise TrustedToolResultError(
                "Appointment tool succeeded without canonical appointment_id"
            )

        updated.appointment_id = appointment_id
        updated.confirmed_fields["appointment_id"] = appointment_id
        updated.dialog_state = DialogState.RESPONDING
        return updated

    updated.dialog_state = DialogState.RESPONDING
    return updated
