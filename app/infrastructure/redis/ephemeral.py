from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


class RedisEphemeralSessionStore:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def put(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        await self._client.set(key, value, ex=ttl_seconds)

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        if value is None:
            return None
        return str(value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def acquire_lock(
        self,
        key: str,
        *,
        owner: str,
        ttl_seconds: int,
    ) -> bool:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        acquired = await self._client.set(
            f"lock:{key}",
            owner,
            ex=ttl_seconds,
            nx=True,
        )
        return bool(acquired)

    async def release_lock(
        self,
        key: str,
        *,
        owner: str,
    ) -> bool:
        released: Any = await self._client.eval(
            _RELEASE_LOCK_SCRIPT,
            1,
            f"lock:{key}",
            owner,
        )
        return int(released) == 1
