from app.conversations.models import ConversationState, DialogState, PendingAction
from app.conversations.orchestrator import ConversationOrchestrator, OrchestratorAction


def state_with_pending() -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        dialog_state=DialogState.AWAITING_CONFIRMATION,
        pending_action=PendingAction(
            action="create_appointment",
            arguments={"slot_id": "slot-1"},
            requires_confirmation=True,
            confirmed=False,
        ),
    )


def test_explicit_yes_unlocks_only_existing_pending_mutation() -> None:
    result = ConversationOrchestrator().process_confirmation(
        state_with_pending(),
        confirmed=True,
    )

    assert result.action is OrchestratorAction.EXECUTE_TOOL
    assert result.state.dialog_state is DialogState.TOOL_EXECUTION
    assert result.state.pending_action is not None
    assert result.state.pending_action.confirmed is True


def test_explicit_no_clears_pending_mutation_without_execution() -> None:
    result = ConversationOrchestrator().process_confirmation(
        state_with_pending(),
        confirmed=False,
    )

    assert result.action is OrchestratorAction.RESPOND
    assert result.reason == "mutation_declined"
    assert result.state.pending_action is None
    assert result.state.dialog_state is DialogState.RESPONDING


def test_unexpected_confirmation_handoffs_instead_of_guessing_target_action() -> None:
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
    )

    result = ConversationOrchestrator().process_confirmation(state, confirmed=True)

    assert result.action is OrchestratorAction.HANDOFF
    assert result.state.handoff_reason == "unexpected_confirmation"
