# ADR-0016: Infrastructure SDKs behind a composition root

Status: Accepted

## DECISION

SQLAlchemy, Redis, Prometheus and OpenTelemetry SDK types remain in infrastructure adapters and the bootstrap/composition layer.

Business/domain modules depend only on internal protocols.

## WHY

Provider/vendor SDK types leaking into orchestration would couple safety logic to deployment choices and make deterministic tests harder.

## TRADE-OFFS

The bootstrap layer contains more wiring code, but infrastructure replacement and tests remain localized.
