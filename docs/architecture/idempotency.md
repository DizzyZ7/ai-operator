# Idempotency and uncertain outcomes

Critical business mutations require idempotency keys.

## Normal flow

```text
claim key
  |
provider mutation
  |
validated result
  |
persist completed idempotency result
```

A replay of the same key + same request returns the original stored result without repeating the provider mutation.

A replay of the same key with different request data is a conflict.

## Timeout after provider request

The dangerous case is:

```text
AI Operator -> create appointment -> Scheduling
                                Scheduling commits
AI Operator <- connection timeout
```

The application cannot infer whether the provider committed.

Therefore:

1. do not announce success;
2. do not blindly retry the mutation;
3. leave the idempotency record unresolved/in-progress;
4. return a reconciliation-required outcome;
5. production provider adapters must implement a provider-supported reconciliation strategy before retry.

The in-memory idempotency implementation in this repository is only for deterministic tests and single-process development. Production requires durable/shared storage or native provider idempotency guarantees.
