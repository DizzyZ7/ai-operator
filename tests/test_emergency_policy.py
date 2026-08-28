import pytest
from pydantic import ValidationError

from app.conversations.models import ConversationState, Intent
from app.conversations.orchestrator import ConversationOrchestrator, OrchestratorAction
from app.conversations.policy import PolicyDecision, evaluate_domain_intent
from app.llm.schemas import LLMDecision, NextAction
from app.safety.emergency import EmergencyAssessment


def state() -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
    )


def test_emergency_intent_is_forced_to_handoff_even_at_high_confidence() -> None:
    result = evaluate_domain_intent(
        Intent.EMERGENCY_ESCALATION,
        confidence=0.99,
    )

    assert result.decision is PolicyDecision.HANDOFF
    assert result.reason == "emergency_escalation_required"


def test_llm_cannot_turn_emergency_into_normal_knowledge_response() -> None:
    decision = LLMDecision(
        intent=Intent.EMERGENCY_ESCALATION,
        confidence=0.99,
        next_action=NextAction.RESPOND_FROM_APPROVED_KNOWLEDGE,
    )

    result = ConversationOrchestrator().process_decision(state(), decision)

    assert result.action is OrchestratorAction.HANDOFF
    assert result.state.handoff_required is True
    assert result.state.handoff_reason == "emergency_escalation_required"


def test_triggered_emergency_assessment_requires_versioned_approved_rule() -> None:
    with pytest.raises(ValidationError):
        EmergencyAssessment(triggered=True)


def test_triggered_emergency_assessment_carries_auditable_rule_evidence() -> None:
    assessment = EmergencyAssessment(
        triggered=True,
        rule_id="approved-rule-17",
        ruleset_version="clinic-policy-v3",
        reason="approved_policy_triggered",
    )

    assert assessment.triggered is True
    assert assessment.rule_id == "approved-rule-17"
