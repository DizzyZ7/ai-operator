from datetime import UTC, datetime, timedelta

import pytest

from app.conversations.models import ConversationState
from app.tools.contracts import ToolResult
from app.tools.reducer import TrustedToolResultError, apply_tool_result


def state() -> ConversationState:
    return ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")


def test_slot_result_becomes_backend_owned_offered_options() -> None:
    starts_at = datetime(2026, 9, 4, 18, 30, tzinfo=UTC)
    result = ToolResult(
        success=True,
        data={
            "slots": [
                {
                    "slot_id": "slot-1",
                    "clinic_id": "clinic-1",
                    "service_id": "service-1",
                    "doctor_id": "doctor-1",
                    "starts_at": starts_at.isoformat(),
                    "ends_at": (starts_at + timedelta(minutes=30)).isoformat(),
                }
            ]
        },
    )

    updated = apply_tool_result(state(), tool_name="get_available_slots", result=result)

    assert len(updated.offered_options) == 1
    assert updated.offered_options[0].payload["slot_id"] == "slot-1"


def test_malformed_successful_slot_result_is_rejected() -> None:
    with pytest.raises(TrustedToolResultError):
        apply_tool_result(
            state(),
            tool_name="get_available_slots",
            result=ToolResult(success=True, data={"slots": [{"slot_id": "broken"}]}),
        )


def test_successful_booking_requires_canonical_appointment_id() -> None:
    with pytest.raises(TrustedToolResultError):
        apply_tool_result(
            state(),
            tool_name="create_appointment",
            result=ToolResult(success=True),
        )
