from __future__ import annotations

from typing import NoReturn

import pytest
from httpx import ASGITransport, AsyncClient

from app.health.models import DependencyHealth, DependencyState
from app.health.service import ReadinessService, StaticDependencyProbe
from app.main import create_app


class RaisingProbe:
    name = "critical-backend"
    critical = True

    async def check(self) -> NoReturn:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_liveness_stays_healthy_when_runtime_providers_are_unconfigured() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_default_readiness_fails_closed_until_real_providers_exist() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")

    body = response.json()
    assert response.status_code == 503
    assert body["ready"] is False
    assert {item["name"] for item in body["dependencies"]} == {
        "telephony",
        "stt",
        "tts",
        "llm",
        "scheduling",
    }


@pytest.mark.asyncio
async def test_all_critical_dependencies_healthy_makes_instance_ready() -> None:
    service = ReadinessService(
        [
            StaticDependencyProbe(
                name="llm",
                state=DependencyState.HEALTHY,
                critical=True,
            ),
            StaticDependencyProbe(
                name="scheduling",
                state=DependencyState.HEALTHY,
                critical=True,
            ),
            StaticDependencyProbe(
                name="analytics",
                state=DependencyState.UNAVAILABLE,
                critical=False,
            ),
        ]
    )
    app = create_app(service)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["ready"] is True


@pytest.mark.asyncio
async def test_probe_exception_becomes_unavailable_and_blocks_critical_readiness() -> None:
    service = ReadinessService([RaisingProbe()])
    report = await service.check()

    assert report.ready is False
    assert report.dependencies == [
        DependencyHealth(
            name="critical-backend",
            state=DependencyState.UNAVAILABLE,
            critical=True,
            detail="probe_failed",
        )
    ]


@pytest.mark.asyncio
async def test_probe_cannot_change_its_declared_identity() -> None:
    class LyingProbe:
        name = "scheduling"
        critical = True

        async def check(self) -> DependencyHealth:
            return DependencyHealth(
                name="other-system",
                state=DependencyState.HEALTHY,
                critical=False,
            )

    report = await ReadinessService([LyingProbe()]).check()

    assert report.ready is False
    assert report.dependencies[0].state is DependencyState.UNAVAILABLE
    assert report.dependencies[0].detail == "invalid_probe_identity"
