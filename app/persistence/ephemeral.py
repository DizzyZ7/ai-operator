from __future__ import annotations

from typing import Protocol


class EphemeralSessionStore(Protocol):
    """Redis-like port for short-lived coordination; never a medical source of truth."""

    async def put(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int,
    ) -> None: ...

    async def get(self, key: str) -> str | None: ...

    async def delete(self, key: str) -> None: ...

    async def acquire_lock(
        self,
        key: str,
        *,
        owner: str,
        ttl_seconds: int,
    ) -> bool: ...

    async def release_lock(
        self,
        key: str,
        *,
        owner: str,
    ) -> bool: ...
