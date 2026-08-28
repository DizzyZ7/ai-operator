# ADR-0005: Call-scoped resource grants

Status: Accepted

## DECISION

Critical tools validate not only tool permission but also the concrete business resource against backend-owned call-scoped grants.

For appointment creation, `slot_id` must belong to a trusted slot actually offered during the current conversation.

## WHY

An allowlisted tool can still be abused if the LLM can invent arbitrary resource identifiers. Tool-name authorization alone cannot prove that a slot, appointment, patient, or other resource was legitimately selected in this call.

## ALTERNATIVES

- trust tool arguments produced by the LLM;
- rely only on global RBAC;
- validate only that the resource exists in the provider.

## TRADE-OFFS

Benefits:
- prevents hallucinated/unseen slot booking;
- creates a basis for patient/appointment-scoped authorization;
- keeps resource authorization outside prompts.

Costs:
- the backend must maintain trusted offered resources;
- grants must expire with conversation/task context;
- future tools need resource-specific grant rules.

This is intentional defense in depth.
