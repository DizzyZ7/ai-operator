# ADR-0011: Backend-owned response evidence

Status: Accepted

## DECISION

Statements that a real business mutation succeeded are generated only from backend-owned response plans backed by validated tool results and trusted conversation state.

The LLM does not have authority to independently say that an appointment was created, moved, cancelled or confirmed.

## WHY

Even if tool execution is safe, a model can still hallucinate the outcome in natural language. A production call-center system must prevent the phrase "готово" from becoming detached from transactional truth.

## FLOW

```text
tool/provider result
      |
trusted result reducer
      |
canonical state evidence
      |
ResponsePlan
      |
safe renderer / constrained NLG
      |
TTS
```

## SUCCESS EVIDENCE

For appointment mutations, a success claim requires:
- successful ToolResult;
- canonical appointment_id in the ToolResult;
- the same appointment_id recorded by the trusted state reducer;
- a response directive that is RESPOND, not REPLAN/HANDOFF.

If any evidence is absent or inconsistent, a success response cannot be built.

## TRADE-OFFS

This reduces unconstrained model freedom for high-risk business statements. Natural language can still be used for tone and low-risk phrasing, but the semantic claim itself is backend-owned.
