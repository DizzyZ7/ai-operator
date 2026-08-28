# ADR-0015: Durable idempotency, ephemeral Redis

Status: Accepted

## DECISION

Critical mutation idempotency records are durable PostgreSQL state.

Redis is used for short-lived coordination:
- realtime/session TTL values;
- distributed locks;
- deduplication windows that are not themselves the source of transactional truth.

## WHY

If an appointment provider commits a mutation and the application loses the response, the idempotency/reconciliation record must survive Redis eviction, restart or cache loss.

Redis remains valuable for low-latency coordination, but losing it must not erase evidence needed to prevent a duplicate patient mutation.

## TRADE-OFFS

PostgreSQL adds a durable write to critical mutation flows. This is intentional: correctness has priority over shaving a few milliseconds from booking/cancellation state.
