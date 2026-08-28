# Tool execution lifecycle

`ToolActionExecutor` is the bridge between an orchestrated pending action and an allowlisted backend tool.

## Execution pipeline

```text
PendingAction
  |
build call-scoped ToolExecutionContext
  |
permission check
  |
confirmation check
  |
idempotency check
  |
tool/provider execution
  |
ToolResult
  |
trusted result reducer
  |
RESPOND / REPLAN / HANDOFF
```

## Directives

- `RESPOND`: trusted successful result can be presented to the patient.
- `REPLAN`: recoverable/normal tool failure requires another safe plan; do not claim success.
- `HANDOFF`: policy violation, uncertain mutation outcome, unexpected exception, or malformed trusted result.

## Audit

Every execution attempt emits:
- `TOOL_REQUESTED`;
- `TOOL_COMPLETED`.

This remains true for policy blocks and internal execution errors so audit trails do not have unexplained missing outcomes.

Audit metadata contains tool names/status codes, not raw patient payloads.

## Slot hydration

`get_available_slots` results are validated as typed `AvailableSlot` objects and converted to backend-owned offered options.

Only those options create slot resource grants for later mutations.

## Mutation success

`create_appointment` success updates canonical `appointment_id` only after the validated tool result contains a non-empty canonical identifier.
