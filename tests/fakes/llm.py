from __future__ import annotations

from app.conversations.models import ConversationState
from app.llm.schemas import LLMDecision


class FakeLLMProvider:
    def __init__(
        self,
        *,
        decision: LLMDecision | None = None,
        error: Exception | None = None,
    ) -> None:
        self._decision = decision
        self._error = error
        self.calls = 0

    async def decide(
        self,
        *,
        transcript: str,
        state: ConversationState,
    ) -> LLMDecision:
        del transcript, state
        self.calls += 1
        if self._error is not None:
            raise self._error
        if self._decision is None:
            raise RuntimeError("FakeLLMProvider has no configured decision")
        return self._decision
