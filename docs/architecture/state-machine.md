# Conversation state machine

Intent and dialog state are separate concepts.

```text
NEW
 |
INITIALIZING
 |
GREETING
 |
LISTENING
 |
UNDERSTANDING
 |
POLICY_CHECK
 |
PLANNING
 +--> COLLECTING_INFO ---------> LISTENING
 +--> AWAITING_CONFIRMATION ---> LISTENING / TOOL_EXECUTION
 +--> TOOL_EXECUTION ----------> PLANNING
 +--> RESPONDING --------------> LISTENING
 +--> HANDOFF
 +--> FALLBACK
 +--> CLOSING -----------------> ENDED
```

## Invariants

1. A business mutation is never executed from free-form assistant text.
2. A confirmation-required action cannot execute before explicit confirmation.
3. A selected option must come from the currently offered option set.
4. A backend failure cannot be converted into a spoken success.
5. Low confidence, repeated misunderstanding, policy conflicts, or direct human request can transition to HANDOFF.
6. OUT_OF_DOMAIN never opens a business mutation path.
7. State is backend-owned and survives LLM context truncation.
8. Barge-in marks the assistant turn interrupted and invalidates continuation of the old spoken response.

## Corrections

Patient corrections supersede earlier slot values.

Example:

```text
"Tomorrow... no, Friday after six."
```

The authoritative state must retain Friday/after-18, not both competing preferences.

Correction semantics will be implemented in the entity/state reducer after real transcript examples are collected.
