from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ToolRisk(StrEnum):
    READ = "READ"
    MUTATION = "MUTATION"
    SENSITIVE_MUTATION = "SENSITIVE_MUTATION"


class ToolExecutionContext(BaseModel):
    call_id: str
    conversation_id: str
    correlation_id: str
    actor: str = "ai_operator"
    permissions: frozenset[str] = Field(default_factory=frozenset)
    idempotency_key: str | None = None
    resource_grants: dict[str, frozenset[str]] = Field(default_factory=dict)


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    retryable: bool = False
    external_reference: str | None = None


class ToolSpec(BaseModel):
    name: str
    risk: ToolRisk
    required_permission: str
    requires_confirmation: bool = False
    requires_idempotency: bool = False


class BackendTool(Protocol):
    spec: ToolSpec

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult: ...
