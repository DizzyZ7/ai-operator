from __future__ import annotations

import asyncio
from typing import Protocol

from app.health.models import DependencyHealth, DependencyState, ReadinessReport


class DependencyProbe(Protocol):
    name: str
    critical: bool

    async def check(self) -> DependencyHealth: ...


class StaticDependencyProbe:
    def __init__(
        self,
        *,
        name: str,
        state: DependencyState,
        critical: bool,
        detail: str | None = None,
    ) -> None:
        self.name = name
        self.critical = critical
        self._state = state
        self._detail = detail

    async def check(self) -> DependencyHealth:
        return DependencyHealth(
            name=self.name,
            state=self._state,
            critical=self.critical,
            detail=self._detail,
        )


class ReadinessService:
    def __init__(self, probes: list[DependencyProbe]) -> None:
        self._probes = list(probes)

    async def check(self) -> ReadinessReport:
        results = await asyncio.gather(
            *(self._safe_check(probe) for probe in self._probes)
        )
        ready = all(
            not health.critical or health.state is DependencyState.HEALTHY
            for health in results
        )
        return ReadinessReport(ready=ready, dependencies=results)

    async def _safe_check(self, probe: DependencyProbe) -> DependencyHealth:
        try:
            health = await probe.check()
        except Exception:
            return DependencyHealth(
                name=probe.name,
                state=DependencyState.UNAVAILABLE,
                critical=probe.critical,
                detail="probe_failed",
            )

        if health.name != probe.name or health.critical != probe.critical:
            return DependencyHealth(
                name=probe.name,
                state=DependencyState.UNAVAILABLE,
                critical=probe.critical,
                detail="invalid_probe_identity",
            )
        return health


def default_unconfigured_readiness_service() -> ReadinessService:
    critical_names = [
        "telephony",
        "stt",
        "tts",
        "llm",
        "scheduling",
    ]
    return ReadinessService(
        [
            StaticDependencyProbe(
                name=name,
                state=DependencyState.NOT_CONFIGURED,
                critical=True,
                detail="provider_not_configured",
            )
            for name in critical_names
        ]
    )
