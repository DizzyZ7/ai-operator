import pytest

from app.conversations.models import DialogState
from app.conversations.transitions import (
    InvalidStateTransition,
    can_transition,
    require_transition,
)


def test_expected_transition_is_allowed() -> None:
    assert can_transition(DialogState.LISTENING, DialogState.UNDERSTANDING)


def test_skipping_directly_to_tool_execution_is_rejected() -> None:
    assert not can_transition(DialogState.LISTENING, DialogState.TOOL_EXECUTION)

    with pytest.raises(InvalidStateTransition):
        require_transition(DialogState.LISTENING, DialogState.TOOL_EXECUTION)


def test_ended_state_is_terminal() -> None:
    assert not can_transition(DialogState.ENDED, DialogState.LISTENING)
