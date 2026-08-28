from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class FailedComponent(StrEnum):
    LLM = "LLM"
    STT = "STT"
    TTS = "TTS"
    TELEPHONY = "TELEPHONY"
    SCHEDULING = "SCHEDULING"
    CRM = "CRM"
    MEDICAL_SYSTEM = "MEDICAL_SYSTEM"


class FallbackAction(StrEnum):
    RETRY_ONCE = "RETRY_ONCE"
    BASIC_ROUTING = "BASIC_ROUTING"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    DO_NOT_CONFIRM_MUTATION = "DO_NOT_CONFIRM_MUTATION"
    TERMINATE_CALL = "TERMINATE_CALL"


class FallbackDecision(BaseModel):
    action: FallbackAction
    reason: str


def decide_fallback(
    component: FailedComponent,
    *,
    mutation_may_have_committed: bool = False,
) -> FallbackDecision:
    if mutation_may_have_committed:
        return FallbackDecision(
            action=FallbackAction.DO_NOT_CONFIRM_MUTATION,
            reason="mutation_outcome_unknown",
        )

    if component in {FailedComponent.LLM, FailedComponent.STT, FailedComponent.TTS}:
        return FallbackDecision(
            action=FallbackAction.HUMAN_HANDOFF,
            reason=f"{component.value.lower()}_unavailable",
        )

    if component in {
        FailedComponent.SCHEDULING,
        FailedComponent.CRM,
        FailedComponent.MEDICAL_SYSTEM,
    }:
        return FallbackDecision(
            action=FallbackAction.HUMAN_HANDOFF,
            reason=f"{component.value.lower()}_backend_unavailable",
        )

    return FallbackDecision(
        action=FallbackAction.TERMINATE_CALL,
        reason="telephony_unavailable",
    )
