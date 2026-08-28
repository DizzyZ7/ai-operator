# Infrastructure composition

Concrete SDKs live under `app/infrastructure`.

Core/domain modules depend on ports such as:
- `ConversationStateRepository`;
- `IdempotencyStore`;
- `EphemeralSessionStore`;
- `MetricsSink`;
- `Tracer`;
- provider protocols.

`build_runtime_container()` is the composition root that selects concrete adapters from runtime configuration.

## Development

If no database URL is configured, deterministic in-memory persistence is used.

Critical voice/business provider readiness remains red until real provider probes are bound.

## Production

Runtime settings require PostgreSQL plus concrete critical provider configuration.

The composition root uses:
- SQLAlchemy async engine / asyncpg;
- durable PostgreSQL conversation/audit/idempotency adapters;
- Redis when configured for ephemeral coordination;
- Prometheus metrics;
- OpenTelemetry tracing;
- dependency-aware readiness.

Provider name configuration alone does not mark a provider healthy. A real probe must be bound; otherwise the dependency is DEGRADED and readiness remains false.

## Lifecycle

The runtime container owns infrastructure resources and closes Redis/database clients explicitly during application shutdown.
