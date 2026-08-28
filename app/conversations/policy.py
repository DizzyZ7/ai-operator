from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.conversations.models import Intent


class PolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    REFUSE_OUT_OF_DOMAIN = "REFUSE_OUT_OF_DOMAIN"
    HANDOFF = "HANDOFF"


@dataclass(frozen=True, slots=True)
class DomainPolicyResult:
    decision: PolicyDecision
    reason: str


ALLOWED_INTENTS: frozenset[Intent] = frozenset(
    intent for intent in Intent if intent is not Intent.OUT_OF_DOMAIN
)


def evaluate_domain_intent(intent: Intent, confidence: float) -> DomainPolicyResult:
    if intent is Intent.OUT_OF_DOMAIN:
        return DomainPolicyResult(
            decision=PolicyDecision.REFUSE_OUT_OF_DOMAIN,
            reason="intent_out_of_domain",
        )

    if confidence < 0.55:
        return DomainPolicyResult(
            decision=PolicyDecision.HANDOFF,
            reason="intent_confidence_too_low",
        )

    if intent not in ALLOWED_INTENTS:
        return DomainPolicyResult(
            decision=PolicyDecision.HANDOFF,
            reason="intent_not_allowlisted",
        )

    return DomainPolicyResult(
        decision=PolicyDecision.ALLOW,
        reason="allowed_clinic_intent",
    )


def safe_out_of_domain_response() -> str:
    return (
        "С этим я не смогу помочь — я занимаюсь вопросами нашей клиники. "
        "Могу помочь с записью, подобрать врача или ответить на вопросы по услугам."
    )
