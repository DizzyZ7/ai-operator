import pytest

from app.conversations.models import ConversationState
from app.persistence.conversations import ConversationConcurrencyConflict
from app.persistence.memory import MemoryConversationStateRepository


def state() -> ConversationState:
    return ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")


@pytest.mark.asyncio
async def test_optimistic_concurrency_rejects_stale_write() -> None:
    repository = MemoryConversationStateRepository()
    created = await repository.create(state())

    first_copy = created.state.model_copy(deep=True)
    second_copy = created.state.model_copy(deep=True)

    first_copy.conversation_summary = "first writer"
    saved = await repository.save(first_copy, expected_version=created.version)

    assert saved.version == 2

    second_copy.conversation_summary = "stale writer"
    with pytest.raises(ConversationConcurrencyConflict):
        await repository.save(second_copy, expected_version=created.version)


@pytest.mark.asyncio
async def test_repository_returns_defensive_copies() -> None:
    repository = MemoryConversationStateRepository()
    await repository.create(state())

    loaded = await repository.get("conv-1")
    assert loaded is not None
    loaded.state.conversation_summary = "mutated outside repository"

    loaded_again = await repository.get("conv-1")
    assert loaded_again is not None
    assert loaded_again.state.conversation_summary == ""
