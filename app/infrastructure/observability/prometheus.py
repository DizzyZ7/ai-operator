from __future__ import annotations

from collections.abc import Mapping
from threading import Lock

from prometheus_client import CollectorRegistry, Counter, Histogram

_TOOL_LABELS = ("tool",)


class PrometheusMetricsSink:
    """Prometheus adapter with bounded label cardinality."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._registry = registry
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = Lock()

    def increment(
        self,
        name: str,
        *,
        value: int = 1,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        counter = self._get_counter(name)
        labels = self._labels_for(name, attributes)
        counter.labels(**labels).inc(value) if labels else counter.inc(value)

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, str] | None = None,
    ) -> None:
        histogram = self._get_histogram(name)
        labels = self._labels_for(name, attributes)
        histogram.labels(**labels).observe(value) if labels else histogram.observe(value)

    def _get_counter(self, name: str) -> Counter:
        with self._lock:
            existing = self._counters.get(name)
            if existing is not None:
                return existing
            created = Counter(
                name,
                f"AI Operator counter: {name}",
                labelnames=self._label_names(name),
                registry=self._registry,
            )
            self._counters[name] = created
            return created

    def _get_histogram(self, name: str) -> Histogram:
        with self._lock:
            existing = self._histograms.get(name)
            if existing is not None:
                return existing
            created = Histogram(
                name,
                f"AI Operator latency/value histogram: {name}",
                labelnames=self._label_names(name),
                registry=self._registry,
            )
            self._histograms[name] = created
            return created

    @staticmethod
    def _label_names(name: str) -> tuple[str, ...]:
        return _TOOL_LABELS if name.startswith("tool_") else ()

    def _labels_for(
        self,
        name: str,
        attributes: Mapping[str, str] | None,
    ) -> dict[str, str]:
        if not attributes:
            return {}
        return {
            label: attributes[label]
            for label in self._label_names(name)
            if label in attributes
        }
