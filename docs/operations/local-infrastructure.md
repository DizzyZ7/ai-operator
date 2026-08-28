# Local infrastructure

The repository includes a development-only Docker Compose stack with PostgreSQL and Redis.

## Start

```bash
docker compose up --build
```

Then apply the schema:

```bash
docker compose exec app alembic upgrade head
```

The API is available on port 8000.

## Expected readiness

`/health/live` should be healthy.

`/health/ready` intentionally remains HTTP 503 because real telephony/STT/TTS/LLM/scheduling adapters and their health probes are not configured in the development stack.

Do not "fix" this by marking placeholder providers healthy.

## Credentials

Compose credentials are development-only values committed for local containers. They are not production secrets.

Production credentials must come from the deployment secret manager/environment and must never be committed.
