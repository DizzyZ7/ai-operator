from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.conversations.models import ConversationState


class ConversationConcurrencyConflict(RuntimeError):
    pass


class VersionedConversationState(BaseModel):
    state: ConversationState
    version: int = Field(ge=1)


class ConversationStateRepository(Protocol):
    async def create(self, state: ConversationState) -> VersionedConversationState: ...

    async def get(self, conversation_id: str) -> VersionedConversationState | None: ...

    async def save(
        self,
        state: ConversationState,
        *,
        expected_version: int,
    ) -> VersionedConversationState: ...
