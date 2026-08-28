# ADR-0009: Approved knowledge is data, never policy

Status: Accepted

## DECISION

RAG/knowledge documents are passed through typed retrieval contracts and treated as business data only. Retrieved text cannot modify system policy, authorization, tool availability, confirmation rules or security boundaries.

## WHY

Knowledge corpora can contain accidental instructions, malicious prompt injection, stale content or copied external text. If retrieval content is allowed to behave as system instructions, an attacker could move from document text to privileged actions.

## ALTERNATIVES

- concatenate retrieved text directly into a system prompt without trust separation;
- let RAG documents define tools/policies;
- rely only on model instruction-following to ignore malicious content.

## TRADE-OFFS

Backend-enforced policy limits model flexibility, but gives deterministic protection against RAG-based privilege escalation.

The model may still use approved retrieved facts to phrase a natural response, subject to version/scope/validity checks.
