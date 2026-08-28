from __future__ import annotations

import os
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.bootstrap import build_runtime_container
from app.config.settings import AppEnvironment, RuntimeSettings
from app.conversations.models import ConversationState
from app.health.models import DependencyState
from app.health.service import StaticDependencyProbe
from app.idempotency.models import IdempotencyStatus


def integration_settings() -> RuntimeSettings:
    database_url = os.getenv("TEST_DATABASE_URL")
    redis_url = os.getenv("TEST_REDIS_URL")
    if not database_url or not redis_url:
        pytest.skip("PostgreSQL/Redis integration services are not configured")

    return RuntimeSettings(
        app_env=AppEnvironment.PRODUCTION,
        llm_provider="integration-llm",
        stt_provider="integration-stt",
        tts_provider="integration-tts",
        telephony_provider="integration-telephony",
        scheduling_provider="integration-scheduling",
        database_url=SecretStr(database_url),
        redis_url=SecretStr(redis_url),
    )


def healthy_provider_probes() -> dict[str, StaticDependencyProbe]:
    return {
        name: StaticDependencyProbe(
            name=name,
            state=DependencyState.HEALTHY,
            critical=True,
        )
        for name in ("telephony", "stt", "tts", "llm", "scheduling")
    }


@pytest.mark.asyncio
async def test_production_container_with_real_postgres_and_redis() -> None:
    container = build_runtime_container(
        integration_settings(),
        provider_probes=healthy_provider_probes(),
    )

    try:
        report = await container.readiness.check()
        assert report.ready is True
        assert {
            dependency.name
            for dependency in report.dependencies
            if dependency.state is DependencyState.HEALTHY
        } >= {
            "database",
            "redis",
            "telephony",
            "stt",
            "tts",
            "llm",
            "scheduling",
        }

        suffix = uuid4().hex
        state = ConversationState(
            call_id=f"call-{suffix}",
            conversation_id=f"conversation-{suffix}",
            trace_id=f"trace-{suffix}",
        )

        created = await container.conversation_states.create(state)
        assert created.version == 1

        loaded = await container.conversation_states.get(state.conversation_id)
        assert loaded is not None
        loaded.state.conversation_summary = "postgres-backed"

        saved = await container.conversation_states.save(
            loaded.state,
            expected_version=loaded.version,
        )
        assert saved.version == 2

        idempotency_key = f"idem-{suffix}"
        claim = await container.idempotency.claim(
            key=idempotency_key,
            operation="create_appointment",
            request_fingerprint=f"fingerprint-{suffix}",
        )
        assert claim.created is True

        completed = await container.idempotency.complete(
            key=idempotency_key,
            result={"success": True, "data": {"appointment_id": f"appointment-{suffix}"}},
        )
        assert completed.status is IdempotencyStatus.COMPLETED

        assert container.ephemeral is not None
        lock_key = f"conversation-{suffix}"
        assert await container.ephemeral.acquire_lock(
            lock_key,
            owner="worker-a",
            ttl_seconds=30,
        )
        assert not await container.ephemeral.acquire_lock(
            lock_key,
            owner="worker-b",
            ttl_seconds=30,
        )
        assert not await container.ephemeral.release_lock(
            lock_key,
            owner="worker-b",
        )
        assert await container.ephemeral.release_lock(
            lock_key,
            owner="worker-a",
        )
    finally:
        await container.close()
