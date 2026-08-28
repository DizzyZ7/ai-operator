# ADR-0003: Tool-mediated business actions

Status: Accepted

## DECISION

The LLM may propose an allowlisted tool call, but only the backend tool layer can authorize and execute business actions.

## WHY

Natural-language output is not sufficient authorization. Appointment creation, rescheduling, cancellation, CRM changes and notifications require typed validation, permissions, idempotency and auditability.

## ALTERNATIVES

- unrestricted agent tool calling;
- direct HTTP access from the model runtime;
- parsing action commands out of assistant prose.

## TRADE-OFFS

Benefits:
- no direct model access to credentials;
- deterministic policy checks;
- independent testing;
- safer retries and error handling.

Costs:
- explicit schemas/contracts for each action;
- more backend code than a demo agent.

The safety/reliability gain outweighs the implementation cost.
