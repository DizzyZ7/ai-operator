from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ResponseKind(StrEnum):
    ASK = "ASK"
    INFORMATION = "INFORMATION"
    MUTATION_SUCCESS = "MUTATION_SUCCESS"
    MUTATION_FAILURE = "MUTATION_FAILURE"
    HANDOFF = "HANDOFF"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


class ResponsePlan(BaseModel):
    kind: ResponseKind
    template_key: str
    source_tool: str | None = None
    business_success: bool = False
    facts: dict[str, Any] = Field(default_factory=dict)
