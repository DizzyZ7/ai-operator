# AI Operator

Production-oriented voice AI call-center operator for a dental clinic network.

This repository is intentionally not a general-purpose assistant. The product is a bounded virtual call-center employee that handles approved clinic workflows and safely transfers anything outside its authority to a human operator.

## Current phase

Phase 0/1 — discovery, architecture foundation and production-hardening primitives.

Implemented foundation:
- backend-owned, versioned conversation state;
- explicit intent and dialog-state models;
- deterministic conversation orchestrator;
- candidate-entity reducer that never promotes LLM text directly to canonical business IDs;
- domain-lock policy boundary;
- emergency intent fail-safe;
- schema-constrained LLM decisions;
- typed provider interfaces for LLM, voice, scheduling, CRM/MIS, notifications and approved knowledge;
- typed appointment/scheduling schemas;
- allowlisted tools with permissions, confirmation and idempotency;
- call-scoped slot resource grants;
- verified-patient appointment ownership grants;
- safe create/reschedule/cancel/confirm appointment tools;
- idempotency replay/conflict/uncertain-outcome handling;
- trusted tool-result reduction;
- backend-owned response evidence for business-success claims;
- cancellable realtime playback and barge-in primitives;
- structured handoff and call-summary models;
- deterministic failure fallback;
- versioned conversation persistence with optimistic concurrency;
- async SQLAlchemy/PostgreSQL conversation repository;
- durable PostgreSQL idempotency repository;
- PostgreSQL audit sink;
- Alembic migration foundation;
- Redis-backed TTL/session coordination and owner-safe distributed locks;
- PII sanitization and safe audit sink;
- Prometheus metrics adapter with bounded labels;
- OpenTelemetry tracing adapter;
- database/Redis/provider health probes;
- dependency-aware liveness/readiness;
- production configuration validation with secret-safe summaries;
- approved knowledge/RAG trust boundary with validity windows;
- runtime composition root and managed FastAPI lifespan;
- non-root Docker image;
- local PostgreSQL/Redis Docker Compose stack;
- `CallSessionCoordinator` for finalized-turn orchestration;
- regression/adversarial tests for safety, state, authorization, concurrency, realtime and mutation invariants;
- real PostgreSQL 17 + Redis 8 integration tests in CI;
- real `alembic upgrade head` against PostgreSQL in CI;
- architecture, operations, ADR and threat-model documentation;
- CI with Ruff, strict mypy, pytest and Docker image build validation.

Not implemented yet:
- concrete production telephony/STT/TTS/LLM providers;
- concrete clinic CRM/MIS/scheduling APIs;
- provider-specific mutation reconciliation;
- clinic-approved identity-verification mechanism;
- clinic-approved emergency ruleset;
- real production knowledge corpus;
- production secret-manager integration;
- OpenTelemetry exporter/backend configuration;
- Kubernetes manifests and production deployment policy;
- medical advice logic.

Those items remain UNKNOWN or intentionally blocked until the clinic provides approved systems, policies and contracts.

## Architecture rule

LLM output is a proposal, never the source of truth.

```text
Telephony -> Realtime Voice -> Call Session Coordinator
                                 |
                         Conversation Orchestrator
                            |       |       |
                          State   Policy   LLM
                            \       |      /
                             Tool Execution
                                   |
                            CRM / MIS / Schedule
                                   |
                           Trusted Result Reducer
                                   |
                             Response Evidence
                                   |
                                  TTS
```

Critical mutations are validated, authorized, explicitly confirmed, idempotent, resource-scoped, audited, and executed only through backend tools.

Natural-language entities extracted by the LLM remain candidates until a trusted provider resolves them to canonical business identifiers.

Existing appointment mutations require both verified patient identity and trusted ownership of the concrete appointment resource.

Statements such as "appointment created", "cancelled", "rescheduled" or "confirmed" require backend evidence from a successful validated tool result and trusted state reduction.

## Persistence and coordination

PostgreSQL is the durable runtime store for conversation state, audit data and critical mutation idempotency.

Redis is intentionally limited to ephemeral coordination such as TTL-backed session values and distributed locks. Losing Redis must not erase transactional evidence required to prevent duplicate patient mutations.

The initial schema is managed by Alembic:

```bash
alembic upgrade head
```

## Health and observability

`/health/live` answers whether the process is alive.

`/health/ready` answers whether the instance can safely receive the core production call path.

The repository default intentionally returns HTTP 503 from readiness because real critical providers are not configured. A provider name alone is not enough: a real health probe must be bound.

A runtime application exposes `/metrics` through a dedicated Prometheus registry. High-cardinality call/conversation identifiers are kept out of Prometheus labels and belong in tracing/log correlation.

## Local development

Requires Python 3.12+.

Application-only development:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

Infrastructure-backed development:

```bash
docker compose up --build
docker compose exec app alembic upgrade head
```

The runtime Docker entrypoint is `app.runtime:app`.

## Core principles

1. Domain lock: clinic business only.
2. No medical diagnosis, prescription or improvised triage.
3. Emergency intent always leaves the normal conversation path and escalates.
4. No hallucinated prices, doctors, slots, addresses, appointments, promotions or rules.
5. Server-side state is authoritative and versioned.
6. LLM never writes SQL or mutates business systems directly.
7. LLM text is never automatically promoted to trusted business IDs.
8. Existing patient resources require verified identity plus trusted ownership.
9. Critical actions require confirmation, idempotency, policy checks and resource authorization.
10. Business-success speech requires backend evidence.
11. Stale concurrent workers cannot silently overwrite newer conversation state.
12. Human handoff is a first-class successful outcome.
13. Patient PII is minimized and sanitized in audit/log metadata.
14. Provider abstractions prevent vendor lock-in.
15. PostgreSQL owns durable application truth; Redis is ephemeral coordination.
16. Production configuration cannot silently retain unconfigured critical providers.
17. Readiness is evidence-based and fails closed.
18. Infrastructure SDKs stay behind adapters/composition root.
19. Start as a modular monolith; split only when evidence justifies it.
