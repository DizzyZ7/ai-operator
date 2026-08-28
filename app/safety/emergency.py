from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, model_validator

from app.conversations.models import ConversationState


class EmergencyAssessment(BaseModel):
    triggered: bool
    rule_id: str | None = None
    ruleset_version: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_triggered_evidence(self) -> EmergencyAssessment:
        if self.triggered and (
            not self.rule_id
            or not self.ruleset_version
            or not self.reason
        ):
            raise ValueError(
                "Triggered emergency assessment requires approved rule evidence"
            )
        return self


class EmergencyPolicyProvider(Protocol):
    async def assess(
        self,
        *,
        transcript: str,
        state: ConversationState,
    ) -> EmergencyAssessment: ...
