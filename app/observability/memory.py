from __future__ import annotations

from collections.abc import Mapping


class MemoryMetricsSink:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.observations: dict[str, list[float]] = {}

    def increment(
        self,
        name: str,
        *,
        value: int = 1,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        del attributes
        self.counters[name] = self.counters.get(name, 0) + value

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        del attributes
        self.observations.setdefault(name, []).append(value)
