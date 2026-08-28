import pytest
from pydantic import ValidationError

from app.conversations.models import Intent
from app.llm.schemas import LLMDecision, NextAction


def test_tool_request_requires_tool_proposal() -> None:
    with pytest.raises(ValidationError):
        LLMDecision(
            intent=Intent.NEW_APPOINTMENT,
            confidence=0.95,
            next_action=NextAction.REQUEST_TOOL,
        )


def test_non_tool_action_rejects_tool_proposal() -> None:
    with pytest.raises(ValidationError):
        LLMDecision(
            intent=Intent.FIND_CLINIC,
            confidence=0.95,
            next_action=NextAction.HANDOFF,
            tool={"tool_name": "search_clinics", "arguments": {}},
        )


def test_confidence_is_schema_constrained() -> None:
    with pytest.raises(ValidationError):
        LLMDecision(
            intent=Intent.FIND_CLINIC,
            confidence=1.5,
            next_action=NextAction.ASK_CLARIFYING_QUESTION,
        )
