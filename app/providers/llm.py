from __future__ import annotations

from typing import Protocol

from app.conversations.models import ConversationState
from app.llm.schemas import LLMDecision


class LLMProvider(Protocol):
    async def decide(
        self,
        *,
        transcript: str,
        state: ConversationState,
    ) -> LLMDecision: ...
