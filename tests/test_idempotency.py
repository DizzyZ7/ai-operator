import pytest

from app.idempotency.memory import MemoryIdempotencyStore
from app.idempotency.models import IdempotencyStatus
from app.idempotency.store import IdempotencyConflict


@pytest.mark.asyncio
async def test_same_key_same_request_replays_existing_claim() -> None:
    store = MemoryIdempotencyStore()

    first = await store.claim(
        key="key-1",
        operation="create_appointment",
        request_fingerprint="fingerprint-1",
    )
    replay = await store.claim(
        key="key-1",
        operation="create_appointment",
        request_fingerprint="fingerprint-1",
    )

    assert first.created is True
    assert replay.created is False
    assert replay.record.status is IdempotencyStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_same_key_different_request_is_conflict() -> None:
    store = MemoryIdempotencyStore()
    await store.claim(
        key="key-1",
        operation="create_appointment",
        request_fingerprint="fingerprint-1",
    )

    with pytest.raises(IdempotencyConflict):
        await store.claim(
            key="key-1",
            operation="create_appointment",
            request_fingerprint="fingerprint-2",
        )
