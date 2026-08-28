from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.conversations.models import Intent


class NextAction(StrEnum):
    ASK_CLARIFYING_QUESTION = "ASK_CLARIFYING_QUESTION"
    ASK_FOR_MISSING_FIELD = "ASK_FOR_MISSING_FIELD"
    REQUEST_TOOL = "REQUEST_TOOL"
    RESPOND_FROM_APPROVED_KNOWLEDGE = "RESPOND_FROM_APPROVED_KNOWLEDGE"
    REFUSE_OUT_OF_DOMAIN = "REFUSE_OUT_OF_DOMAIN"
    HANDOFF = "HANDOFF"
    CLOSE = "CLOSE"


class ExtractedEntities(BaseModel):
    service: str | None = None
    clinic: str | None = None
    doctor: str | None = None
    date: str | None = None
    time_preference: str | None = None
    appointment_reference: str | None = None


class ToolProposal(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMDecision(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    missing_fields: list[str] = Field(default_factory=list)
    next_action: NextAction
    tool: ToolProposal | None = None

    @model_validator(mode="after")
    def validate_tool_shape(self) -> LLMDecision:
        if self.next_action is NextAction.REQUEST_TOOL and self.tool is None:
            raise ValueError("REQUEST_TOOL requires a tool proposal")
        if self.next_action is not NextAction.REQUEST_TOOL and self.tool is not None:
            raise ValueError("Tool proposal is only valid with REQUEST_TOOL")
        return self
