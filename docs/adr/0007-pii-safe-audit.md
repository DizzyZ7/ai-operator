# ADR-0007: PII-safe audit and logging

Status: Accepted

## DECISION

Audit/log metadata is minimized and sanitized before persistence. Raw transcript text is not included in routine turn audit events.

## WHY

Call-center traces are operationally valuable but can easily become an uncontrolled copy of patient data. Debugging convenience is not sufficient justification for replicating PII into every telemetry backend.

## ALTERNATIVES

- log full prompts/transcripts by default;
- rely only on provider-side redaction;
- store everything and restrict access later.

## TRADE-OFFS

Aggressive minimization can reduce debugging detail. Approved transcript/recording storage, if legally and operationally required, should therefore be a separate explicitly governed data product with access control and retention policy rather than incidental application logs.

The included sanitizer is a baseline defense, not a substitute for a clinic-approved PII inventory and data-loss-prevention policy.
