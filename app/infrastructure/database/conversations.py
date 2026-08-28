from __future__ import annotations

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.conversations.models import ConversationState
from app.infrastructure.database.models import ConversationStateRow
from app.persistence.conversations import (
    ConversationConcurrencyConflict,
    VersionedConversationState,
)


class SqlAlchemyConversationStateRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(self, state: ConversationState) -> VersionedConversationState:
        payload = state.model_dump(mode="json")
        async with self._sessions() as session:
            try:
                await session.execute(
                    insert(ConversationStateRow).values(
                        conversation_id=state.conversation_id,
                        call_id=state.call_id,
                        state_json=payload,
                        version=1,
                    )
                )
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise ConversationConcurrencyConflict(
                    "Conversation already exists"
                ) from exc

        return VersionedConversationState(state=state.model_copy(deep=True), version=1)

    async def get(self, conversation_id: str) -> VersionedConversationState | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(ConversationStateRow).where(
                    ConversationStateRow.conversation_id == conversation_id
                )
            )

        if row is None:
            return None

        return VersionedConversationState(
            state=ConversationState.model_validate(row.state_json),
            version=row.version,
        )

    async def save(
        self,
        state: ConversationState,
        *,
        expected_version: int,
    ) -> VersionedConversationState:
        next_version = expected_version + 1
        async with self._sessions() as session:
            execution = await session.execute(
                update(ConversationStateRow)
                .where(
                    ConversationStateRow.conversation_id == state.conversation_id,
                    ConversationStateRow.version == expected_version,
                )
                .values(
                    call_id=state.call_id,
                    state_json=state.model_dump(mode="json"),
                    version=next_version,
                )
                .returning(ConversationStateRow.conversation_id)
            )
            updated_id = execution.scalar_one_or_none()

            if updated_id is None:
                await session.rollback()
                exists = await session.scalar(
                    select(ConversationStateRow.conversation_id).where(
                        ConversationStateRow.conversation_id == state.conversation_id
                    )
                )
                if exists is None:
                    raise KeyError("Conversation does not exist")
                raise ConversationConcurrencyConflict(
                    "Conversation state version changed before save"
                )

            await session.commit()

        return VersionedConversationState(
            state=state.model_copy(deep=True),
            version=next_version,
        )
