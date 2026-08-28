# Inbound call lifecycle

The lifecycle is designed around low perceived latency without giving the LLM authority over business state.

```text
1. incoming call
2. validate telephony provider request
3. allocate call_id / conversation_id / trace_id
4. establish media stream
5. start VAD and streaming STT
6. greet once
7. receive partial transcript
8. endpoint detection finalizes patient turn
9. normalize transcript
10. produce schema-constrained LLM decision
11. validate schema
12. apply domain / medical / authorization policies
13. reduce approved entities into backend conversation state
14. decide whether information, confirmation, tool execution or handoff is required
15. execute allowlisted backend tool if permitted
16. validate tool result
17. build bounded response plan
18. stream TTS
19. if patient barges in, cancel TTS and playback buffer immediately
20. continue from the newly completed patient turn
21. before critical mutation, require explicit confirmation
22. execute mutation with idempotency key
23. verify backend result before speaking success
24. close or hand off
25. persist structured summary, audit events and metrics
```

## Barge-in invariant

The old response becomes invalid once the patient interrupts. The realtime layer must stop playback and must not resume the previous audio after the interrupting turn ends.

## Backend failure invariant

A timeout, malformed response or unavailable scheduling/CRM/MIS system never maps to "your appointment is created". A mutation is successful only when the authoritative provider returns a validated success result or an idempotency reconciliation proves the earlier request succeeded.

## Latency spans

Measure separately:
- VAD endpoint latency;
- STT partial latency;
- STT finalization latency;
- LLM time to first token / structured decision latency;
- tool latency;
- TTS time to first audio;
- end-to-end patient-stop to assistant-first-audio latency.

Track p50, p95 and p99.
