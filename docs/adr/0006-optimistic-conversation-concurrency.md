# ADR-0006: Optimistic conversation concurrency

Status: Accepted

## DECISION

Every durable conversation-state write supplies the version that the worker originally read. The write succeeds only if that version is still current.

## WHY

Realtime systems can produce overlapping events:
- duplicate/final STT events;
- provider redelivery;
- slow tool completion;
- reconnecting media workers;
- multiple application instances.

Without concurrency control, a stale worker could overwrite newer patient intent, confirmation state or handoff state.

## ALTERNATIVES

- last-write-wins;
- one global process lock;
- store only transcript and reconstruct state;
- pessimistic database locks held across external API calls.

## TRADE-OFFS

Optimistic concurrency adds explicit conflict handling, but avoids long database locks and makes stale writes visible instead of silently corrupting state.

Production repository adapters should implement this with an atomic version predicate/update.
