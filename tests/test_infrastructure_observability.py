from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import CollectorRegistry, generate_latest
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.base import Base
from app.infrastructure.health.probes import DatabaseDependencyProbe
from app.infrastructure.observability.prometheus import PrometheusMetricsSink
from app.infrastructure.observability.tracing import OpenTelemetryTracer
from app.main import create_app


def test_prometheus_adapter_drops_high_cardinality_call_identifiers() -> None:
    registry = CollectorRegistry()
    metrics = PrometheusMetricsSink(registry)

    metrics.increment(
        "tool_success_total",
        attributes={
            "tool": "create_appointment",
            "call_id": "call-secret-1",
            "conversation_id": "conversation-secret-1",
        },
    )
    metrics.increment(
        "calls_started_total",
        attributes={"call_id": "call-secret-2"},
    )
    metrics.observe(
        "tool_latency_seconds",
        0.2,
        attributes={
            "tool": "create_appointment",
            "call_id": "call-secret-3",
        },
    )

    payload = generate_latest(registry).decode("utf-8")

    assert 'tool="create_appointment"' in payload
    assert "call-secret" not in payload
    assert "conversation-secret" not in payload


def test_opentelemetry_adapter_satisfies_core_span_operations() -> None:
    tracer = OpenTelemetryTracer()

    with tracer.start_span(
        "test.operation",
        attributes={"component": "test"},
    ) as span:
        span.set_attribute("success", True)
        span.record_error(RuntimeError("synthetic"))

        
@pytest.mark.asyncio
async def test_database_probe_executes_real_query() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    health = await DatabaseDependencyProbe(engine).check()

    assert health.name == "database"
    assert health.state.value == "HEALTHY"
    assert health.critical is True

    await engine.dispose()


@pytest.mark.asyncio
async def test_metrics_endpoint_exports_supplied_registry() -> None:
    registry = CollectorRegistry()
    metrics = PrometheusMetricsSink(registry)
    metrics.increment("calls_started_total")

    application = create_app(metrics_registry=registry)
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert "calls_started_total" in response.text
