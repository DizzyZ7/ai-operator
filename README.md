# AI Operator

Production-oriented voice AI call-center operator for a dental clinic network.

This repository is intentionally not a general-purpose assistant. The core product is a bounded call-center employee that handles approved clinic workflows and safely transfers anything else to a human operator.

## Current phase

Phase 0/1 — discovery, architecture foundation and production-hardening primitives.

Implemented foundation:
- backend-owned conversation state;
- explicit intent and dialog-state models;
- deterministic conversation orchestrator;
- candidate-entity reducer that does not promote LLM text to trusted IDs;
- domain-lock policy boundary;
- schema-constrained LLM decisions;
- typed provider interfaces for LLM, voice, scheduling, CRM/MIS and notifications;
- typed appointment/scheduling schemas;
- allowlisted tool contracts with permissions, confirmation and idempotency;
- call-scoped resource grants for trusted offered slots;
- safe create-appointment reference tool;
- idempotency replay/conflict/uncertain-outcome handling;
- cancellable realtime playback and barge-in primitives;
- structured handoff and call-summary models;
- deterministic failure fallback;
- versioned conversation persistence contract with optimistic concurrency;
- Redis-like ephemeral coordination contract;
- PII sanitization and safe audit sink;
- provider-neutral metrics and tracing ports;
- `CallSessionCoordinator` for finalized-turn orchestration;
- FastAPI service skeleton;
- regression tests for safety, state, concurrency, realtime and mutation invariants;
- architecture, discovery, ADR and threat-model documentation;
- CI baseline.

Not implemented yet:
- real telephony provider;
- real STT/TTS/LLM provider;
- real CRM/MIS/scheduling integration;
- PostgreSQL/Redis concrete adapters;
- OpenTelemetry/Prometheus concrete exporters;
- durable production idempotency/reconciliation;
- clinic-specific knowledge base;
- patient identity policy.

Those integrations remain UNKNOWN until the clinic provides approved systems and contracts.

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
```

Critical mutations are validated, authorized, explicitly confirmed where required, idempotent, resource-scoped, audited, and executed only through backend tools.

Natural-language entities extracted by the LLM remain candidates until a trusted provider resolves them to canonical business identifiers.

## Local development

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

## Core principles

1. Domain lock: clinic business only.
2. No medical diagnosis or treatment advice.
3. No hallucinated prices, doctors, slots, addresses, appointments, promotions, or rules.
4. Server-side state is authoritative and versioned.
5. LLM never writes SQL or mutates business systems directly.
6. LLM text is never automatically promoted to trusted business IDs.
7. Critical actions require idempotency, explicit policy checks and resource authorization.
8. Stale concurrent workers cannot silently overwrite newer conversation state.
9. Human handoff is a first-class successful outcome.
10. Patient PII is minimized and sanitized in audit/log metadata.
11. Provider abstractions prevent vendor lock-in.
12. Redis-like state is ephemeral coordination, never business truth.
13. Start as a modular monolith; split only when evidence justifies it.
