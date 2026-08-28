from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.tools.contracts import BackendTool, ToolExecutionContext, ToolResult, ToolRisk


class ToolPolicyError(RuntimeError):
    pass


@dataclass(slots=True)
class ToolRegistry:
    _tools: dict[str, BackendTool] = field(default_factory=dict)

    def register(self, tool: BackendTool) -> None:
        if tool.spec.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.spec.name}")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> BackendTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    async def execute(
        self,
        *,
        name: str,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
        confirmed: bool,
    ) -> ToolResult:
        tool = self.get(name)
        spec = tool.spec

        if spec.required_permission not in context.permissions:
            raise ToolPolicyError("Missing required tool permission")

        if spec.requires_confirmation and not confirmed:
            raise ToolPolicyError("Explicit confirmation required")

        if (
            spec.risk in {ToolRisk.MUTATION, ToolRisk.SENSITIVE_MUTATION}
            and spec.requires_idempotency
            and not context.idempotency_key
        ):
            raise ToolPolicyError("Idempotency key required for mutation")

        return await tool.execute(context, arguments)
