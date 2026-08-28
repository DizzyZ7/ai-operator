from __future__ import annotations

from pydantic import ValidationError

from app.appointments.models import AvailableSlot, PatientAppointment
from app.appointments.offers import build_slot_options
from app.conversations.models import ConversationState, DialogState
from app.tools.contracts import ToolResult


class TrustedToolResultError(ValueError):
    pass


def _require_appointment_id(result: ToolResult, *, tool_name: str) -> str:
    appointment_id = result.data.get("appointment_id")
    if not isinstance(appointment_id, str) or not appointment_id:
        raise TrustedToolResultError(
            f"{tool_name} succeeded without canonical appointment_id"
        )
    return appointment_id


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

    if tool_name == "get_patient_appointments":
        raw_appointments = result.data.get("appointments")
        if not isinstance(raw_appointments, list):
            raise TrustedToolResultError(
                "Patient appointments tool succeeded without an appointments list"
            )

        try:
            appointments = [
                PatientAppointment.model_validate(item) for item in raw_appointments
            ]
        except ValidationError as exc:
            raise TrustedToolResultError(
                "Medical system returned malformed appointment data"
            ) from exc

        verified_patient_id = updated.patient.external_patient_id
        if (
            not updated.patient.identity_verified
            or verified_patient_id is None
            or any(
                appointment.patient_id != verified_patient_id
                for appointment in appointments
            )
        ):
            raise TrustedToolResultError(
                "Patient appointment result does not match verified patient context"
            )

        updated.authorized_appointment_ids = frozenset(
            appointment.appointment_id for appointment in appointments
        )
        updated.dialog_state = DialogState.RESPONDING
        return updated

    if tool_name == "create_appointment":
        appointment_id = _require_appointment_id(result, tool_name=tool_name)
        updated.appointment_id = appointment_id
        updated.confirmed_fields["appointment_id"] = appointment_id
        updated.authorized_appointment_ids = (
            updated.authorized_appointment_ids | {appointment_id}
        )
        updated.dialog_state = DialogState.RESPONDING
        return updated

    if tool_name in {
        "reschedule_appointment",
        "confirm_appointment",
        "cancel_appointment",
    }:
        appointment_id = _require_appointment_id(result, tool_name=tool_name)
        updated.appointment_id = appointment_id
        updated.confirmed_fields[f"{tool_name}.appointment_id"] = appointment_id
        updated.dialog_state = DialogState.RESPONDING

        if tool_name == "cancel_appointment":
            updated.authorized_appointment_ids = frozenset(
                current_id
                for current_id in updated.authorized_appointment_ids
                if current_id != appointment_id
            )

        return updated

    updated.dialog_state = DialogState.RESPONDING
    return updated
