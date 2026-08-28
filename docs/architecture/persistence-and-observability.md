# Persistence and observability boundaries

## Durable state

Conversation state is backend-owned and requires optimistic concurrency.

Production implementations should persist:
- calls;
- versioned conversation state/snapshots;
- tool/audit events;
- call summaries;
- idempotency records where provider-native idempotency is insufficient.

The `ConversationStateRepository` contract uses `expected_version` so concurrent workers cannot silently overwrite a newer turn.

PostgreSQL is the intended default durable store, but the core package does not import a PostgreSQL driver.

## Ephemeral coordination

The `EphemeralSessionStore` represents Redis-like capabilities:
- short-lived values;
- TTLs;
- distributed locks;
- active realtime-session coordination.

Redis is not a source of truth for patient, appointment or medical data.

Losing Redis must not redefine business truth.

## Audit

Audit events contain stable IDs, event type, correlation ID, timestamp and minimal metadata.

Raw transcripts, phone numbers, e-mail addresses and other PII must not be copied into audit/log metadata by default.

`SafeAuditSink` sanitizes metadata before delegating to storage. Provider/application logging must apply the same sanitization policy.

## Observability

Core code emits provider-neutral:
- counters;
- latency observations;
- spans.

Concrete OpenTelemetry/Prometheus exporters are infrastructure adapters.

Initial metrics include:
- `calls_started_total`;
- `conversation_turns_total`;
- `barge_ins_total`;
- `llm_errors_total`;
- `handoffs_total`;
- `llm_decision_latency_seconds`.

Production should additionally instrument VAD, STT, tool, TTS, end-to-end response latency and mutation reconciliation.

## Cardinality warning

Call/conversation IDs are useful trace attributes but should not be exported as high-cardinality Prometheus labels. Concrete metrics adapters must map only bounded dimensions to labels and keep per-call identifiers in traces/log correlation.
