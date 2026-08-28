# ADR-0002: Backend-owned conversation state

Status: Accepted

## DECISION

The authoritative call state is stored and reduced by backend code. LLM chat history is context, not state.

## WHY

Production call flows require deterministic recovery, auditability, handoff, regression testing and protection from context truncation or model reinterpretation.

## ALTERNATIVES

- use only LLM conversation history;
- rebuild state from transcript on every turn;
- store only a free-form conversation summary.

## TRADE-OFFS

Benefits:
- explicit invariants;
- resumable/replayable calls;
- deterministic handoff context;
- safer mutations.

Costs:
- more domain modeling;
- entity correction/reduction logic must be implemented explicitly.

This cost is intentional for a system that can change real appointments.
