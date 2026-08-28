from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Protocol, Self


class TraceSpan(Protocol):
    def set_attribute(self, key: str, value: str | int | float | bool) -> None: ...

    def record_error(self, error: BaseException) -> None: ...


class SpanContext(Protocol):
    def __enter__(self) -> TraceSpan: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class Tracer(Protocol):
    def start_span(
        self,
        name: str,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> SpanContext: ...


class _NoopSpan:
    def set_attribute(self, key: str, value: str | int | float | bool) -> None:
        del key, value

    def record_error(self, error: BaseException) -> None:
        del error


class _NoopSpanContext:
    def __init__(self) -> None:
        self._span = _NoopSpan()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc_type, exc, traceback
        return None

    def set_attribute(self, key: str, value: str | int | float | bool) -> None:
        self._span.set_attribute(key, value)

    def record_error(self, error: BaseException) -> None:
        self._span.record_error(error)


class NoopTracer:
    def start_span(
        self,
        name: str,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> SpanContext:
        del name, attributes
        return _NoopSpanContext()
