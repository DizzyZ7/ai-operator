from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.conversations.models import ConversationState
from app.idempotency.models import IdempotencyStatus
from app.idempotency.store import IdempotencyConflict
from app.infrastructure.database.base import Base
from app.infrastructure.database.conversations import (
    SqlAlchemyConversationStateRepository,
)
from app.infrastructure.database.idempotency import SqlAlchemyIdempotencyStore
from app.infrastructure.database.session import create_session_factory
from app.persistence.conversations import ConversationConcurrencyConflict


async def database() -> tuple[
    AsyncEngine,
    async_sessionmaker[AsyncSession],
]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, create_session_factory(engine)


def state() -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conversation-1",
        trace_id="trace-1",
    )


@pytest.mark.asyncio
async def test_sqlalchemy_conversation_repository_preserves_version_contract() -> None:
    engine, sessions = await database()
    repository = SqlAlchemyConversationStateRepository(sessions)

    created = await repository.create(state())
    loaded = await repository.get("conversation-1")
    assert loaded is not None
    assert loaded.version == 1
    assert loaded.state == created.state

    updated_state = loaded.state.model_copy(deep=True)
    updated_state.conversation_summary = "updated"
    saved = await repository.save(updated_state, expected_version=1)

    assert saved.version == 2

    with pytest.raises(ConversationConcurrencyConflict):
        await repository.save(updated_state, expected_version=1)

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_conversation_repository_rejects_duplicate_create() -> None:
    engine, sessions = await database()
    repository = SqlAlchemyConversationStateRepository(sessions)

    await repository.create(state())

    with pytest.raises(ConversationConcurrencyConflict):
        await repository.create(state())

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_idempotency_store_is_durable_and_conflict_safe() -> None:
    engine, sessions = await database()
    store = SqlAlchemyIdempotencyStore(sessions)

    first = await store.claim(
        key="idem-1",
        operation="create_appointment",
        request_fingerprint="fingerprint-1",
    )
    replay = await store.claim(
        key="idem-1",
        operation="create_appointment",
        request_fingerprint="fingerprint-1",
    )

    assert first.created is True
    assert replay.created is False
    assert replay.record.status is IdempotencyStatus.IN_PROGRESS

    completed = await store.complete(
        key="idem-1",
        result={"success": True, "data": {"appointment_id": "appointment-1"}},
    )
    assert completed.status is IdempotencyStatus.COMPLETED

    loaded = await store.get("idem-1")
    assert loaded is not None
    assert loaded.result["success"] is True

    with pytest.raises(IdempotencyConflict):
        await store.claim(
            key="idem-1",
            operation="create_appointment",
            request_fingerprint="different-fingerprint",
        )

    await engine.dispose()
