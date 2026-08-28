from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from starlette.types import Lifespan

from app.health.service import ReadinessService, default_unconfigured_readiness_service


def create_app(
    readiness_service: ReadinessService | None = None,
    *,
    metrics_registry: CollectorRegistry | None = None,
    lifespan: Lifespan[FastAPI] | None = None,
) -> FastAPI:
    application = FastAPI(
        title="AI Operator",
        version="0.1.0",
        description="Bounded voice AI call-center operator backend",
        lifespan=lifespan,
    )
    readiness_checks = readiness_service or default_unconfigured_readiness_service()

    @application.get("/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    async def readiness(response: Response) -> dict[str, Any]:
        report = await readiness_checks.check()
        response.status_code = (
            status.HTTP_200_OK
            if report.ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return report.model_dump(mode="json")

    if metrics_registry is not None:

        @application.get("/metrics", include_in_schema=False)
        async def metrics() -> Response:
            return Response(
                content=generate_latest(metrics_registry),
                media_type=CONTENT_TYPE_LATEST,
            )

    return application


app = create_app()
