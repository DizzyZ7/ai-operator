# ADR-0013: Production configuration and secret boundary

Status: Accepted

## DECISION

Production startup configuration is validated separately from application logic.

Critical voice/booking providers cannot remain `unconfigured` in production, and durable database configuration is required.

Secret-bearing values use secret types and are excluded from safe runtime summaries.

## WHY

A service that boots successfully with missing critical providers is not a production-ready call-center instance. Likewise, dumping runtime settings into logs must not expose database/Redis credentials.

## RULES

- development/test may intentionally run with unconfigured providers;
- production rejects missing LLM/STT/TTS/telephony/scheduling configuration;
- production requires a durable database URL;
- provider names may be logged; secret URLs/tokens may not;
- provider-specific API secrets will be owned by concrete adapters/secret manager integration;
- no secrets are committed to the repository.

## TRADE-OFFS

The core settings model does not attempt to invent provider-specific credential fields before vendor selection.
