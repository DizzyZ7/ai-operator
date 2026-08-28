# ADR-0001: Start as a modular monolith

Status: Accepted

## DECISION

Start AI Operator as one deployable modular monolith with explicit domain/provider boundaries.

## WHY

The first product scope is one bounded call-center system. Conversation state, policy, tool authorization, idempotency and realtime orchestration are tightly related. Premature service boundaries would increase latency, distributed failure modes and operational cost before traffic patterns are known.

## ALTERNATIVES

- microservices from day one;
- serverless functions;
- fully event-driven services.

## TRADE-OFFS

Advantages:
- simpler local development and debugging;
- lower realtime latency;
- easier transactional consistency;
- less infrastructure during discovery/MVP.

Costs:
- one deployment unit initially;
- component ownership must remain disciplined.

Likely future extraction candidates, only when justified:
- realtime media gateway;
- async analytics workers;
- knowledge ingestion/indexing;
- high-volume outbound calling.
