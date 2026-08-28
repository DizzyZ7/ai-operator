# ADR-0012: Dependency-aware readiness

Status: Accepted

## DECISION

Liveness and readiness are separate.

- liveness answers whether the application process is alive;
- readiness answers whether the instance can safely serve the core production call path.

The default repository configuration is intentionally NOT ready because real telephony/STT/TTS/LLM/scheduling providers are not configured.

## WHY

Returning HTTP 200 from readiness while critical providers are absent would let Kubernetes/load balancers route real patient calls to an instance that cannot complete them.

## RULES

- /health/live remains independent of downstream availability;
- /health/ready returns HTTP 503 when any critical dependency is not healthy;
- optional/degraded dependencies do not automatically fail readiness;
- probe exceptions are converted to UNAVAILABLE;
- a probe cannot lie about its configured identity/criticality;
- concrete provider adapters supply real health probes later.

## TRADE-OFFS

Local default readiness is red until dependencies are injected. That is intentional: "application starts" and "production traffic is safe" are different claims.
