from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DependencyState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class DependencyHealth(BaseModel):
    name: str
    state: DependencyState
    critical: bool
    detail: str | None = None


class ReadinessReport(BaseModel):
    ready: bool
    dependencies: list[DependencyHealth] = Field(default_factory=list)
