# Initial threat model

This document is an architecture baseline, not a completed security assessment.

## Assets

- patient identity data;
- appointment data;
- call transcripts and recordings where legally permitted;
- business knowledge;
- provider credentials;
- CRM/MIS/scheduling access;
- audit trail.

## Trust boundaries

### 1. Telephony edge

Incoming signalling, media and webhook payloads are untrusted.

Controls to design:
- provider signature validation;
- replay protection;
- rate limiting;
- session correlation;
- strict payload validation.

### 2. LLM boundary

LLM output is untrusted structured input.

The model must never receive:
- database credentials;
- API keys;
- direct SQL access;
- unrestricted internal HTTP access;
- administrator privileges.

LLM proposals pass schema, policy, authorization and business-state validation before execution.

### 3. Tool execution boundary

Critical controls:
- allowlisted tools;
- least-privilege service identities;
- per-tool authorization;
- explicit confirmation for destructive/important mutations;
- idempotency for critical mutations;
- sanitized errors;
- audit events.

### 4. CRM / MIS / Scheduling boundary

Adapters use minimum required scopes. Scheduling access does not imply access to full medical history.

### 5. Supervisor boundary

Supervisor, QA, operator, administrator and auditor capabilities require separate permissions. Transcript/recording access must not be universal.

## Initial abuse cases

- prompt injection asking the agent to ignore domain policy;
- request for system prompts or secrets;
- cancelling another patient's appointment;
- requesting another patient's medical data;
- repeated duplicate booking requests;
- retry after upstream timeout that already committed a booking;
- malicious text embedded in RAG documents;
- forged telephony webhook;
- PII leakage into logs;
- hallucinated backend success.

## Security invariant

No LLM-generated statement is sufficient evidence that a privileged business action is authorized or completed.
