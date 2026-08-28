# Discovery: UNKNOWN and assumptions

This document is deliberately explicit. Unknown company details must not be invented in code, prompts, fixtures, or architecture diagrams.

## Business UNKNOWN

- clinic list and canonical clinic identifiers;
- service catalogue and canonical service identifiers;
- doctor directory and canonical doctor identifiers;
- approved prices and source of truth;
- promotions and loyalty rules;
- operator scripts;
- complaint escalation rules;
- emergency policy;
- preparation instructions;
- patient identification and verification policy;
- criteria for mandatory human transfer.

## Integration UNKNOWN

- telephony provider and SIP topology;
- CRM product and API contract;
- medical information system and API contract;
- scheduling source of truth;
- authentication mechanisms;
- webhook capabilities;
- rate limits;
- notification provider;
- human transfer API/protocol;
- sandbox environments.

## Infrastructure UNKNOWN

- hosting environment;
- production region;
- expected concurrent calls;
- peak calls per second;
- network/private connectivity requirements;
- existing Kubernetes availability;
- existing secrets manager;
- existing observability stack;
- disaster recovery requirements.

## Security / legal UNKNOWN

- lawful basis and consent flow for call recording;
- retention periods;
- data-localization constraints;
- exact PII classification;
- permitted cloud AI providers;
- internal security standards;
- patient verification requirements for appointment mutations.

## Temporary architecture assumptions

These are not business facts.

1. Russian is the first supported language.
2. MVP handles inbound calls only.
3. Scheduling/MIS remains the appointment source of truth.
4. AI Operator PostgreSQL does not become a shadow medical system.
5. Redis, if introduced, is ephemeral infrastructure only.
6. External providers are replaceable adapters.
7. Initial deployment is a modular monolith.
8. Payments are outside MVP.
9. Only minimum necessary PII is sent to AI providers.

Every assumption must be confirmed or removed during discovery.
