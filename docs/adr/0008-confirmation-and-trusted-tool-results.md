# ADR-0008: Explicit confirmation and trusted tool-result reduction

Status: Accepted

## DECISION

Confirmation is bound to one backend-owned pending action. A patient confirmation unlocks only that action; it does not grant generic mutation authority.

After tool execution, the provider response is validated and reduced into conversation state by backend code before the system may announce success.

## WHY

Two separate risks exist:

1. A model may reinterpret a generic "yes" as approval for the wrong action.
2. A provider/tool may return malformed or incomplete success data.

Both can create incorrect real-world actions or hallucinated confirmations.

## FLOW

```text
LLM proposes mutation
       |
backend creates PendingAction
       |
patient hears exact action
       |
explicit confirmation
       |
PendingAction.confirmed = true
       |
ToolRegistry policy checks
       |
provider mutation
       |
trusted-result validation
       |
canonical state update
       |
response may confirm success
```

## INVARIANTS

- confirmation with no confirmation-required pending action is invalid;
- a declined mutation is cleared and never executed;
- a tool cannot bypass its confirmation requirement;
- malformed successful slot/appointment responses are rejected;
- successful appointment mutation requires canonical `appointment_id`;
- uncertain mutation outcome goes to reconciliation/handoff, never spoken success.

## TRADE-OFFS

This adds explicit state transitions and reducers, but keeps approval semantics auditable and independent of prompt wording.
