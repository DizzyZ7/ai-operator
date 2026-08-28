from __future__ import annotations

import asyncio

from app.conversations.models import ConversationState
from app.persistence.conversations import (
    ConversationConcurrencyConflict,
    VersionedConversationState,
)


class MemoryConversationStateRepository:
    """Process-local repository for tests/dev; not a production persistence backend."""

    def __init__(self) -> None:
        self._items: dict[str, VersionedConversationState] = {}
        self._lock = asyncio.Lock()

    async def create(self, state: ConversationState) -> VersionedConversationState:
        async with self._lock:
            if state.conversation_id in self._items:
                raise ConversationConcurrencyConflict("Conversation already exists")

            item = VersionedConversationState(state=state.model_copy(deep=True), version=1)
            self._items[state.conversation_id] = item
            return item.model_copy(deep=True)

    async def get(self, conversation_id: str) -> VersionedConversationState | None:
        async with self._lock:
            item = self._items.get(conversation_id)
            return None if item is None else item.model_copy(deep=True)

    async def save(
        self,
        state: ConversationState,
        *,
        expected_version: int,
    ) -> VersionedConversationState:
        async with self._lock:
            current = self._items.get(state.conversation_id)
            if current is None:
                raise KeyError("Conversation does not exist")
            if current.version != expected_version:
                raise ConversationConcurrencyConflict(
                    f"Expected version {expected_version}, current version {current.version}"
                )

            updated = VersionedConversationState(
                state=state.model_copy(deep=True),
                version=current.version + 1,
            )
            self._items[state.conversation_id] = updated
            return updated.model_copy(deep=True)
