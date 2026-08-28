from __future__ import annotations

from enum import StrEnum
from time import monotonic

from pydantic import BaseModel

from app.audit.models import AuditEvent, AuditEventType
from app.audit.sink import AuditSink
from app.conversations.models import ConversationState
from app.observability.metrics import MetricsSink
from app.observability.tracing import Tracer
from app.tools.context import build_tool_execution_context
from app.tools.contracts import ToolResult
from app.tools.reducer import TrustedToolResultError, apply_tool_result
from app.tools.registry import ToolPolicyError, ToolRegistry


class ToolExecutionDirective(StrEnum):
    RESPOND = "RESPOND"
    REPLAN = "REPLAN"
    HANDOFF = "HANDOFF"


class ToolActionOutcome(BaseModel):
    state: ConversationState
    result: ToolResult
    directive: ToolExecutionDirective
    reason: str


class ToolActionExecutor:
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        audit: AuditSink,
        metrics: MetricsSink,
        tracer: Tracer,
        permissions: frozenset[str],
    ) -> None:
        self._registry = registry
        self._audit = audit
        self._metrics = metrics
        self._tracer = tracer
        self._permissions = permissions

    async def execute_pending(
        self,
        state: ConversationState,
        *,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> ToolActionOutcome:
        pending = state.pending_action
        if pending is None:
            raise ValueError("No pending action to execute")

        attributes = {
            "tool": pending.action,
            "call_id": state.call_id,
            "conversation_id": state.conversation_id,
        }
        await self._audit.emit(
            AuditEvent(
                event_type=AuditEventType.TOOL_REQUESTED,
                call_id=state.call_id,
                conversation_id=state.conversation_id,
                correlation_id=correlation_id,
                metadata={"tool": pending.action},
            )
        )

        context = build_tool_execution_context(
            state,
            correlation_id=correlation_id,
            permissions=self._permissions,
            idempotency_key=idempotency_key,
        )

        started = monotonic()
        with self._tracer.start_span("tool.execute", attributes=attributes) as span:
            try:
                result = await self._registry.execute(
                    name=pending.action,
                    context=context,
                    arguments=pending.arguments,
                    confirmed=pending.confirmed,
                )
            except ToolPolicyError as exc:
                span.record_error(exc)
                result = ToolResult(success=False, error_code="tool_policy_violation")
                updated = state.model_copy(deep=True)
                updated.require_handoff("tool_policy_violation")
                outcome = ToolActionOutcome(
                    state=updated,
                    result=result,
                    directive=ToolExecutionDirective.HANDOFF,
                    reason="tool_policy_violation",
                )
            except Exception as exc:
                span.record_error(exc)
                result = ToolResult(success=False, error_code="tool_execution_failure")
                updated = state.model_copy(deep=True)
                updated.require_handoff("tool_execution_failure")
                outcome = ToolActionOutcome(
                    state=updated,
                    result=result,
                    directive=ToolExecutionDirective.HANDOFF,
                    reason="tool_execution_failure",
                )
            else:
                error_code = result.error_code or "tool_failed"
                if error_code in {
                    "mutation_outcome_unknown",
                    "mutation_reconciliation_required",
                    "provider_invalid_success_response",
                }:
                    updated = state.model_copy(deep=True)
                    updated.require_handoff(error_code)
                    outcome = ToolActionOutcome(
                        state=updated,
                        result=result,
                        directive=ToolExecutionDirective.HANDOFF,
                        reason=error_code,
                    )
                else:
                    try:
                        updated = apply_tool_result(
                            state,
                            tool_name=pending.action,
                            result=result,
                        )
                    except TrustedToolResultError as exc:
                        span.record_error(exc)
                        result = ToolResult(
                            success=False,
                            error_code="invalid_trusted_tool_result",
                        )
                        updated = state.model_copy(deep=True)
                        updated.require_handoff("invalid_trusted_tool_result")
                        outcome = ToolActionOutcome(
                            state=updated,
                            result=result,
                            directive=ToolExecutionDirective.HANDOFF,
                            reason="invalid_trusted_tool_result",
                        )
                    else:
                        outcome = ToolActionOutcome(
                            state=updated,
                            result=result,
                            directive=(
                                ToolExecutionDirective.RESPOND
                                if result.success
                                else ToolExecutionDirective.REPLAN
                            ),
                            reason="tool_completed" if result.success else error_code,
                        )
            finally:
                self._metrics.observe(
                    "tool_latency_seconds",
                    monotonic() - started,
                    attributes=attributes,
                )

        await self._audit.emit(
            AuditEvent(
                event_type=AuditEventType.TOOL_COMPLETED,
                call_id=state.call_id,
                conversation_id=state.conversation_id,
                correlation_id=correlation_id,
                metadata={
                    "tool": pending.action,
                    "success": outcome.result.success,
                    "error_code": outcome.result.error_code,
                    "directive": outcome.directive.value,
                },
            )
        )

        if outcome.directive is ToolExecutionDirective.HANDOFF:
            self._metrics.increment("handoffs_total", attributes=attributes)
        elif outcome.result.success:
            self._metrics.increment("tool_success_total", attributes=attributes)
        else:
            self._metrics.increment("tool_failure_total", attributes=attributes)

        return outcome
