from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from app.conversations.models import ConversationState, DialogState, PendingAction
from app.conversations.policy import PolicyDecision, evaluate_domain_intent
from app.conversations.reducer import apply_extracted_entities
from app.llm.schemas import LLMDecision, NextAction
from app.tools.catalog import TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolRisk


class OrchestratorAction(StrEnum):
    RESPOND = "RESPOND"
    ASK = "ASK"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION"
    HANDOFF = "HANDOFF"
    CLOSE = "CLOSE"


class OrchestrationResult(BaseModel):
    state: ConversationState
    action: OrchestratorAction
    reason: str


class ConversationOrchestrator:
    def process_decision(
        self,
        state: ConversationState,
        decision: LLMDecision,
    ) -> OrchestrationResult:
        updated = apply_extracted_entities(state, decision.entities)
        updated.intent = decision.intent
        updated.intent_confidence = decision.confidence

        policy = evaluate_domain_intent(decision.intent, decision.confidence)
        if policy.decision is PolicyDecision.REFUSE_OUT_OF_DOMAIN:
            updated.dialog_state = DialogState.RESPONDING
            updated.pending_action = None
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.RESPOND,
                reason=policy.reason,
            )

        if policy.decision is PolicyDecision.HANDOFF:
            updated.require_handoff(policy.reason)
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.HANDOFF,
                reason=policy.reason,
            )

        if decision.next_action is NextAction.HANDOFF:
            updated.require_handoff("model_requested_handoff")
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.HANDOFF,
                reason="model_requested_handoff",
            )

        if decision.next_action is NextAction.CLOSE:
            updated.dialog_state = DialogState.CLOSING
            updated.pending_action = None
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.CLOSE,
                reason="close_requested",
            )

        if decision.next_action in {
            NextAction.ASK_CLARIFYING_QUESTION,
            NextAction.ASK_FOR_MISSING_FIELD,
        }:
            updated.dialog_state = DialogState.COLLECTING_INFO
            updated.pending_action = None
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.ASK,
                reason="more_information_required",
            )

        if decision.next_action in {
            NextAction.RESPOND_FROM_APPROVED_KNOWLEDGE,
            NextAction.REFUSE_OUT_OF_DOMAIN,
        }:
            updated.dialog_state = DialogState.RESPONDING
            updated.pending_action = None
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.RESPOND,
                reason="bounded_response",
            )

        if decision.next_action is NextAction.REQUEST_TOOL:
            assert decision.tool is not None
            spec = TOOL_SPECS_BY_NAME.get(decision.tool.tool_name)
            if spec is None:
                updated.require_handoff("unknown_tool_proposal")
                return OrchestrationResult(
                    state=updated,
                    action=OrchestratorAction.HANDOFF,
                    reason="unknown_tool_proposal",
                )

            updated.pending_action = PendingAction(
                action=spec.name,
                arguments=decision.tool.arguments,
                requires_confirmation=spec.requires_confirmation,
                confirmed=False,
            )

            if spec.risk is not ToolRisk.READ and spec.requires_confirmation:
                updated.dialog_state = DialogState.AWAITING_CONFIRMATION
                return OrchestrationResult(
                    state=updated,
                    action=OrchestratorAction.REQUEST_CONFIRMATION,
                    reason="mutation_requires_confirmation",
                )

            updated.dialog_state = DialogState.TOOL_EXECUTION
            return OrchestrationResult(
                state=updated,
                action=OrchestratorAction.EXECUTE_TOOL,
                reason="allowlisted_tool",
            )

        updated.require_handoff("unsupported_next_action")
        return OrchestrationResult(
            state=updated,
            action=OrchestratorAction.HANDOFF,
            reason="unsupported_next_action",
        )
