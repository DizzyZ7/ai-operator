from __future__ import annotations

from typing import Any, cast

import pytest
from redis.asyncio import Redis

from app.infrastructure.redis.ephemeral import RedisEphemeralSessionStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool | None:
        del ex
        if nx and key in self.values:
            return None
        self.values[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, key: str) -> int:
        return int(self.values.pop(key, None) is not None)

    async def eval(
        self,
        script: str,
        numkeys: int,
        key: str,
        owner: str,
    ) -> int:
        del script, numkeys
        if self.values.get(key) != owner:
            return 0
        del self.values[key]
        return 1

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


def store() -> RedisEphemeralSessionStore:
    client = cast(Redis, cast(Any, FakeRedis()))
    return RedisEphemeralSessionStore(client)


@pytest.mark.asyncio
async def test_ephemeral_values_round_trip_and_delete() -> None:
    ephemeral = store()

    await ephemeral.put("session:1", "payload", ttl_seconds=30)
    assert await ephemeral.get("session:1") == "payload"

    await ephemeral.delete("session:1")
    assert await ephemeral.get("session:1") is None


@pytest.mark.asyncio
async def test_lock_can_only_be_released_by_owner() -> None:
    ephemeral = store()

    assert await ephemeral.acquire_lock("conversation:1", owner="worker-a", ttl_seconds=10)
    assert not await ephemeral.acquire_lock(
        "conversation:1",
        owner="worker-b",
        ttl_seconds=10,
    )

    assert not await ephemeral.release_lock("conversation:1", owner="worker-b")
    assert await ephemeral.release_lock("conversation:1", owner="worker-a")


@pytest.mark.asyncio
async def test_ephemeral_ttl_must_be_positive() -> None:
    ephemeral = store()

    with pytest.raises(ValueError, match="positive"):
        await ephemeral.put("key", "value", ttl_seconds=0)

    with pytest.raises(ValueError, match="positive"):
        await ephemeral.acquire_lock("key", owner="worker", ttl_seconds=0)
