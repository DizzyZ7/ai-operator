# Tool contract rules

Tools are the only path from conversation planning to business-system actions.

## Required metadata

Every tool has:
- stable name;
- risk class;
- required permission;
- typed request/response at implementation time;
- timeout policy;
- retry policy;
- audit event;
- correlation ID;
- sanitized error mapping.

Mutating tools additionally require idempotency where duplicate execution could create a duplicate or inconsistent business effect.

## Critical mutation flow

```text
LLM tool proposal
      |
schema validation
      |
tool allowlist
      |
permission check
      |
conversation-state precondition
      |
explicit confirmation (when required)
      |
idempotency key
      |
provider adapter
      |
validated provider response
      |
audit/result
```

## Retry rule

Read operations can usually retry on transient failures.

Mutation retries are never blind. The implementation must use provider idempotency support or reconcile by idempotency key/external reference before retrying.

## Error rule

Provider exceptions are not exposed directly to the patient or model. Adapters map them to sanitized domain error codes and retryability.

## No fake success

A tool timeout is not success. If the provider may have committed before the timeout, the orchestrator enters reconciliation/fallback; it never announces completion based on probability.
