from app.conversations.models import Intent
from app.conversations.policy import PolicyDecision, evaluate_domain_intent


def test_out_of_domain_is_refused() -> None:
    result = evaluate_domain_intent(Intent.OUT_OF_DOMAIN, confidence=0.99)
    assert result.decision is PolicyDecision.REFUSE_OUT_OF_DOMAIN


def test_low_confidence_clinic_intent_handoffs() -> None:
    result = evaluate_domain_intent(Intent.NEW_APPOINTMENT, confidence=0.40)
    assert result.decision is PolicyDecision.HANDOFF


def test_confident_clinic_intent_is_allowed() -> None:
    result = evaluate_domain_intent(Intent.NEW_APPOINTMENT, confidence=0.95)
    assert result.decision is PolicyDecision.ALLOW
