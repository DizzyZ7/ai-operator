from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from prometheus_client import CollectorRegistry
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.audit.safe import SafeAuditSink
from app.audit.sink import AuditSink
from app.config.settings import RuntimeSettings
from app.health.models import DependencyState
from app.health.service import DependencyProbe, ReadinessService, StaticDependencyProbe
from app.idempotency.memory import MemoryIdempotencyStore
from app.idempotency.store import IdempotencyStore
from app.infrastructure.database.audit import SqlAlchemyAuditSink
from app.infrastructure.database.conversations import SqlAlchemyConversationStateRepository
from app.infrastructure.database.idempotency import SqlAlchemyIdempotencyStore
from app.infrastructure.database.session import (
    create_engine_from_settings,
    create_session_factory,
)
from app.infrastructure.health.probes import (
    DatabaseDependencyProbe,
    RedisDependencyProbe,
)
from app.infrastructure.observability.prometheus import PrometheusMetricsSink
from app.infrastructure.observability.tracing import OpenTelemetryTracer
from app.infrastructure.redis.client import create_redis_client
from app.infrastructure.redis.ephemeral import RedisEphemeralSessionStore
from app.observability.metrics import MetricsSink
from app.observability.tracing import Tracer
from app.persistence.conversations import ConversationStateRepository
from app.persistence.ephemeral import EphemeralSessionStore
from app.persistence.memory import MemoryConversationStateRepository
from app.audit.memory import MemoryAuditSink

_CRITICAL_PROVIDER_NAMES = ("telephony", "stt", "tts", "llm", "scheduling")


@dataclass(slots=True)
class RuntimeContainer:
    conversation_states: ConversationStateRepository
    audit: AuditSink
    idempotency: IdempotencyStore
    ephemeral: EphemeralSessionStore | None
    metrics: MetricsSink
    tracer: Tracer
    readiness: ReadinessService
    prometheus_registry: CollectorRegistry
    database_engine: AsyncEngine | None = None
    redis_client: Redis | None = None

    async def close(self) -> None:
        if self.redis_client is not None:
            await self.redis_client.aclose()
        if self.database_engine is not None:
            await self.database_engine.dispose()


def build_runtime_container(
    settings: RuntimeSettings,
    *,
    provider_probes: Mapping[str, DependencyProbe] | None = None,
) -> RuntimeContainer:
    probes: list[DependencyProbe] = []
    provider_probes = provider_probes or {}

    database_engine: AsyncEngine | None = None
    if settings.database_url is not None:
        database_engine = create_engine_from_settings(settings)
        sessions = create_session_factory(database_engine)
        conversation_states: ConversationStateRepository = (
            SqlAlchemyConversationStateRepository(sessions)
        )
        raw_audit: AuditSink = SqlAlchemyAuditSink(sessions)
        idempotency: IdempotencyStore = SqlAlchemyIdempotencyStore(sessions)
        probes.append(DatabaseDependencyProbe(database_engine))
    else:
        conversation_states = MemoryConversationStateRepository()
        raw_audit = MemoryAuditSink()
        idempotency = MemoryIdempotencyStore()

    redis_client: Redis | None = None
    ephemeral: EphemeralSessionStore | None = None
    if settings.redis_url is not None:
        redis_client = create_redis_client(settings)
        ephemeral = RedisEphemeralSessionStore(redis_client)
        probes.append(
            RedisDependencyProbe(
                redis_client,
                critical=settings.app_env.value == "production",
            )
        )

    configured_provider_names = {
        "telephony": settings.telephony_provider,
        "stt": settings.stt_provider,
        "tts": settings.tts_provider,
        "llm": settings.llm_provider,
        "scheduling": settings.scheduling_provider,
    }
    for name in _CRITICAL_PROVIDER_NAMES:
        bound_probe = provider_probes.get(name)
        if bound_probe is not None:
            probes.append(bound_probe)
            continue

        configured = configured_provider_names[name]
        probes.append(
            StaticDependencyProbe(
                name=name,
                state=(
                    DependencyState.NOT_CONFIGURED
                    if configured == "unconfigured"
                    else DependencyState.DEGRADED
                ),
                critical=True,
                detail=(
                    "provider_not_configured"
                    if configured == "unconfigured"
                    else "health_probe_not_bound"
                ),
            )
        )

    registry = CollectorRegistry()
    return RuntimeContainer(
        conversation_states=conversation_states,
        audit=SafeAuditSink(raw_audit),
        idempotency=idempotency,
        ephemeral=ephemeral,
        metrics=PrometheusMetricsSink(registry),
        tracer=OpenTelemetryTracer(),
        readiness=ReadinessService(probes),
        prometheus_registry=registry,
        database_engine=database_engine,
        redis_client=redis_client,
    )
