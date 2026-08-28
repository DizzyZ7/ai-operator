from typing import Any

import pytest

from app.tools.contracts import (
    ToolExecutionContext,
    ToolResult,
    ToolRisk,
    ToolSpec,
)
from app.tools.registry import ToolPolicyError, ToolRegistry


class FakeMutationTool:
    spec = ToolSpec(
        name="create_appointment",
        risk=ToolRisk.MUTATION,
        required_permission="appointments:create",
        requires_confirmation=True,
        requires_idempotency=True,
    )

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        return ToolResult(success=True, external_reference="appt-1")


def context(*, idempotency_key: str | None = "idem-1") -> ToolExecutionContext:
    return ToolExecutionContext(
        call_id="call-1",
        conversation_id="conv-1",
        correlation_id="corr-1",
        permissions=frozenset({"appointments:create"}),
        idempotency_key=idempotency_key,
    )


@pytest.mark.asyncio
async def test_mutation_requires_explicit_confirmation() -> None:
    registry = ToolRegistry()
    registry.register(FakeMutationTool())

    with pytest.raises(ToolPolicyError):
        await registry.execute(
            name="create_appointment",
            context=context(),
            arguments={"slot_id": "slot-1"},
            confirmed=False,
        )


@pytest.mark.asyncio
async def test_mutation_requires_idempotency_key() -> None:
    registry = ToolRegistry()
    registry.register(FakeMutationTool())

    with pytest.raises(ToolPolicyError):
        await registry.execute(
            name="create_appointment",
            context=context(idempotency_key=None),
            arguments={"slot_id": "slot-1"},
            confirmed=True,
        )


@pytest.mark.asyncio
async def test_mutation_executes_after_policy_checks() -> None:
    registry = ToolRegistry()
    registry.register(FakeMutationTool())

    result = await registry.execute(
        name="create_appointment",
        context=context(),
        arguments={"slot_id": "slot-1"},
        confirmed=True,
    )
    assert result.success is True
    assert result.external_reference == "appt-1"
