from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class MetricsSink(Protocol):
    def increment(
        self,
        name: str,
        *,
        value: int = 1,
        attributes: Mapping[str, str] | None = None,
    ) -> None: ...

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> None: ...


class NoopMetricsSink:
    def increment(
        self,
        name: str,
        *,
        value: int = 1,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        del name, value, attributes

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        del name, value, attributes
