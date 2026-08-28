from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bootstrap import RuntimeContainer, build_runtime_container
from app.config.settings import RuntimeSettings
from app.health.service import DependencyProbe
from app.main import create_app


def create_runtime_app(
    settings: RuntimeSettings | None = None,
    *,
    provider_probes: Mapping[str, DependencyProbe] | None = None,
) -> FastAPI:
    runtime_settings = settings or RuntimeSettings()
    container = build_runtime_container(
        runtime_settings,
        provider_probes=provider_probes,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.runtime_container = container
        try:
            yield
        finally:
            await container.close()

    application = create_app(
        container.readiness,
        metrics_registry=container.prometheus_registry,
        lifespan=lifespan,
    )
    application.state.runtime_container = container
    return application


def get_runtime_container(application: FastAPI) -> RuntimeContainer:
    container = application.state.runtime_container
    if not isinstance(container, RuntimeContainer):
        raise RuntimeError("Runtime container is not initialized")
    return container


app = create_runtime_app()
