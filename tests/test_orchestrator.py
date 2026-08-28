from app.conversations.models import ConversationState, DialogState, Intent
from app.conversations.orchestrator import ConversationOrchestrator, OrchestratorAction
from app.llm.schemas import LLMDecision, NextAction, ToolProposal


def state() -> ConversationState:
    return ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")


def test_out_of_domain_cannot_smuggle_tool_request() -> None:
    decision = LLMDecision(
        intent=Intent.OUT_OF_DOMAIN,
        confidence=0.99,
        next_action=NextAction.REQUEST_TOOL,
        tool=ToolProposal(
            tool_name="create_appointment",
            arguments={"slot_id": "invented-slot"},
        ),
    )

    result = ConversationOrchestrator().process_decision(state(), decision)

    assert result.action is OrchestratorAction.RESPOND
    assert result.state.pending_action is None
    assert result.state.dialog_state is DialogState.RESPONDING


def test_critical_mutation_is_staged_for_confirmation() -> None:
    decision = LLMDecision(
        intent=Intent.NEW_APPOINTMENT,
        confidence=0.99,
        next_action=NextAction.REQUEST_TOOL,
        tool=ToolProposal(
            tool_name="create_appointment",
            arguments={"slot_id": "slot-1"},
        ),
    )

    result = ConversationOrchestrator().process_decision(state(), decision)

    assert result.action is OrchestratorAction.REQUEST_CONFIRMATION
    assert result.state.dialog_state is DialogState.AWAITING_CONFIRMATION
    assert result.state.pending_action is not None
    assert result.state.pending_action.action == "create_appointment"


def test_unknown_tool_proposal_handoffs() -> None:
    decision = LLMDecision(
        intent=Intent.NEW_APPOINTMENT,
        confidence=0.99,
        next_action=NextAction.REQUEST_TOOL,
        tool=ToolProposal(tool_name="drop_database", arguments={}),
    )

    result = ConversationOrchestrator().process_decision(state(), decision)

    assert result.action is OrchestratorAction.HANDOFF
    assert result.state.handoff_required is True
    assert result.state.handoff_reason == "unknown_tool_proposal"
