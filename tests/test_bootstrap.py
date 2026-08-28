from __future__ import annotations

import pytest
from pydantic import SecretStr

from app.bootstrap import build_runtime_container
from app.config.settings import AppEnvironment, RuntimeSettings
from app.health.models import DependencyState
from app.health.service import StaticDependencyProbe
from app.persistence.memory import MemoryConversationStateRepository


@pytest.mark.asyncio
async def test_development_bootstrap_uses_memory_without_database_configuration() -> None:
    container = build_runtime_container(RuntimeSettings(app_env=AppEnvironment.TEST))

    assert isinstance(
        container.conversation_states,
        MemoryConversationStateRepository,
    )
    report = await container.readiness.check()
    assert report.ready is False

    await container.close()


@pytest.mark.asyncio
async def test_configured_provider_without_real_probe_is_not_marked_healthy() -> None:
    settings = RuntimeSettings(
        app_env=AppEnvironment.TEST,
        llm_provider="configured-adapter",
    )
    container = build_runtime_container(settings)

    report = await container.readiness.check()
    llm = next(item for item in report.dependencies if item.name == "llm")

    assert llm.state is DependencyState.DEGRADED
    assert llm.detail == "health_probe_not_bound"

    await container.close()


@pytest.mark.asyncio
async def test_bound_provider_probe_controls_readiness_state() -> None:
    probe = StaticDependencyProbe(
        name="llm",
        state=DependencyState.HEALTHY,
        critical=True,
    )
    container = build_runtime_container(
        RuntimeSettings(app_env=AppEnvironment.TEST),
        provider_probes={"llm": probe},
    )

    report = await container.readiness.check()
    llm = next(item for item in report.dependencies if item.name == "llm")

    assert llm.state is DependencyState.HEALTHY

    await container.close()


def test_production_database_factory_refuses_non_postgres_database() -> None:
    settings = RuntimeSettings(
        app_env=AppEnvironment.PRODUCTION,
        llm_provider="llm",
        stt_provider="stt",
        tts_provider="tts",
        telephony_provider="telephony",
        scheduling_provider="scheduling",
        database_url=SecretStr("sqlite+aiosqlite:///:memory:"),
    )

    with pytest.raises(ValueError, match="must use PostgreSQL"):
        build_runtime_container(settings)
