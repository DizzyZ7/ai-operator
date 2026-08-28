# AI Operator

Production-oriented voice AI call-center operator for a dental clinic network.

This repository is intentionally not a general-purpose assistant. The core product is a bounded call-center employee that handles approved clinic workflows and safely transfers anything else to a human operator.

## Current phase

Phase 0/1 — discovery and architecture foundation.

Implemented foundation:
- backend-owned conversation state;
- explicit intent and dialog-state models;
- domain-lock policy boundary;
- typed tool contracts with idempotency/confirmation metadata;
- FastAPI service skeleton;
- regression tests for core safety/state rules;
- architecture, discovery, ADR and threat-model documentation;
- CI baseline.

Not implemented yet:
- real telephony provider;
- real STT/TTS/LLM provider;
- CRM/MIS/scheduling integration;
- clinic-specific knowledge base;
- patient identity policy.

Those integrations remain UNKNOWN until the clinic provides approved systems and contracts.

## Architecture rule

LLM output is a proposal, never the source of truth.

```text
Telephony -> Realtime Voice -> Conversation Orchestrator
                                  |       |       |
                                State   Policy   LLM
                                  \       |      /
                                   Tool Execution
                                         |
                                  CRM / MIS / Schedule
```

Critical mutations are validated, authorized, explicitly confirmed where required, idempotent, audited, and executed only through backend tools.

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
4. Server-side state is authoritative.
5. LLM never writes SQL or mutates business systems directly.
6. Critical actions require idempotency and explicit policy checks.
7. Human handoff is a first-class successful outcome.
8. Patient PII is minimized and masked in logs.
9. Provider abstractions prevent vendor lock-in.
10. Start as a modular monolith; split only when evidence justifies it.
