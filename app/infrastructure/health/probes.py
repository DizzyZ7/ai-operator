from __future__ import annotations

from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.health.models import DependencyHealth, DependencyState


class DatabaseDependencyProbe:
    name = "database"
    critical = True

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def check(self) -> DependencyHealth:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return DependencyHealth(
            name=self.name,
            state=DependencyState.HEALTHY,
            critical=self.critical,
        )


class RedisDependencyProbe:
    name = "redis"

    def __init__(self, client: Redis, *, critical: bool) -> None:
        self._client = client
        self.critical = critical

    async def check(self) -> DependencyHealth:
        healthy = bool(await self._client.ping())
        return DependencyHealth(
            name=self.name,
            state=(
                DependencyState.HEALTHY
                if healthy
                else DependencyState.UNAVAILABLE
            ),
            critical=self.critical,
        )


class CallableDependencyProbe:
    def __init__(
        self,
        *,
        name: str,
        critical: bool,
        check: Callable[[], Awaitable[bool]],
    ) -> None:
        self.name = name
        self.critical = critical
        self._check = check

    async def check(self) -> DependencyHealth:
        healthy = await self._check()
        return DependencyHealth(
            name=self.name,
            state=(
                DependencyState.HEALTHY
                if healthy
                else DependencyState.UNAVAILABLE
            ),
            critical=self.critical,
        )
