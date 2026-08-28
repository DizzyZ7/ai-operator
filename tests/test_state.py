import pytest

from app.conversations.models import ConversationState, DialogState, OfferedOption


def make_state() -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conversation-1",
        trace_id="trace-1",
    )


def test_handoff_changes_authoritative_state() -> None:
    state = make_state()
    state.require_handoff("patient_requested_human")

    assert state.handoff_required is True
    assert state.handoff_reason == "patient_requested_human"
    assert state.dialog_state is DialogState.HANDOFF


def test_selected_option_must_have_been_offered() -> None:
    state = make_state()
    state.offered_options = [
        OfferedOption(option_id="slot-1", label="18:30"),
        OfferedOption(option_id="slot-2", label="20:00"),
    ]

    selected = state.select_offered_option("slot-1")
    assert selected.option_id == "slot-1"
    assert state.selected_option_id == "slot-1"

    with pytest.raises(ValueError):
        state.select_offered_option("slot-never-offered")
