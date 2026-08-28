# ADR-0004: Provider abstractions

Status: Accepted

## DECISION

Telephony, STT, TTS, LLM, CRM, medical-system, scheduling and notification vendors are accessed behind explicit provider interfaces.

## WHY

The core conversation domain must not contain Voximplant-, SIP-, Bitrix-, vendor-LLM- or dental-MIS-specific behavior. Provider capabilities, latency and legal constraints may change after discovery.

## ALTERNATIVES

- bind directly to one vendor SDK;
- create separate application forks per provider.

## TRADE-OFFS

Benefits:
- test doubles for CI;
- lower vendor lock-in;
- controlled provider failover later;
- isolated authentication/error mapping.

Costs:
- adapter layer;
- lowest-common-denominator risk.

Provider-specific capabilities may be exposed through explicit optional capability interfaces rather than leaking SDK types into the core.
