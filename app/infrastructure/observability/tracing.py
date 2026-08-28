from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Self

from opentelemetry import trace
from opentelemetry.trace import Span, Tracer as OtelTracer


class _SpanAdapter:
    def __init__(self, span: Span) -> None:
        self._span = span

    def set_attribute(self, key: str, value: str | int | float | bool) -> None:
        self._span.set_attribute(key, value)

    def record_error(self, error: BaseException) -> None:
        self._span.record_exception(error)


class _SpanContext:
    def __init__(
        self,
        tracer: OtelTracer,
        name: str,
        attributes: Mapping[str, str] | None,
    ) -> None:
        self._context: AbstractContextManager[Span] = tracer.start_as_current_span(
            name,
            attributes=dict(attributes or {}),
        )
        self._adapter: _SpanAdapter | None = None

    def __enter__(self) -> _SpanAdapter:
        span = self._context.__enter__()
        self._adapter = _SpanAdapter(span)
        return self._adapter

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._context.__exit__(exc_type, exc, traceback)


class OpenTelemetryTracer:
    def __init__(
        self,
        *,
        instrumentation_name: str = "ai-operator",
        tracer: OtelTracer | None = None,
    ) -> None:
        self._tracer = tracer or trace.get_tracer(instrumentation_name)

    def start_span(
        self,
        name: str,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> _SpanContext:
        return _SpanContext(self._tracer, name, attributes)
