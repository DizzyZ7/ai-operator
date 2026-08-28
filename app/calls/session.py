from __future__ import annotations

from time import monotonic

from pydantic import BaseModel

from app.audit.models import AuditEvent, AuditEventType
from app.audit.sink import AuditSink
from app.conversations.models import ConversationState
from app.conversations.orchestrator import (
    ConversationOrchestrator,
    OrchestrationResult,
    OrchestratorAction,
)
from app.observability.metrics import MetricsSink
from app.observability.tracing import Tracer
from app.persistence.conversations import ConversationStateRepository
from app.providers.llm import LLMProvider
from app.voice.playback import PlaybackController


class SessionTurnResult(BaseModel):
    orchestration: OrchestrationResult
    state_version: int


class ConversationNotFound(KeyError):
    pass


class CallSessionCoordinator:
    """Coordinates one finalized patient turn without owning vendor-specific media."""

    def __init__(
        self,
        *,
        state_repository: ConversationStateRepository,
        llm: LLMProvider,
        orchestrator: ConversationOrchestrator,
        playback: PlaybackController,
        audit: AuditSink,
        metrics: MetricsSink,
        tracer: Tracer,
    ) -> None:
        self._states = state_repository
        self._llm = llm
        self._orchestrator = orchestrator
        self._playback = playback
        self._audit = audit
        self._metrics = metrics
        self._tracer = tracer

    async def initialize(self, state: ConversationState) -> int:
        created = await self._states.create(state)
        await self._audit.emit(
            AuditEvent(
                event_type=AuditEventType.CALL_STARTED,
                call_id=state.call_id,
                conversation_id=state.conversation_id,
                correlation_id=state.trace_id,
            )
        )
        self._metrics.increment("calls_started_total")
        return created.version

    async def on_patient_speech_started(self, *, call_id: str) -> bool:
        interrupted = await self._playback.interrupt()
        if interrupted:
            self._metrics.increment(
                "barge_ins_total",
                attributes={"call_id": call_id},
            )
        return interrupted

    async def process_final_transcript(
        self,
        *,
        conversation_id: str,
        transcript: str,
        correlation_id: str,
    ) -> SessionTurnResult:
        stored = await self._states.get(conversation_id)
        if stored is None:
            raise ConversationNotFound(conversation_id)

        state = stored.state
        attributes = {
            "call_id": state.call_id,
            "conversation_id": state.conversation_id,
        }

        await self._audit.emit(
            AuditEvent(
                event_type=AuditEventType.TURN_RECEIVED,
                call_id=state.call_id,
                conversation_id=state.conversation_id,
                correlation_id=correlation_id,
                metadata={"transcript_chars": len(transcript)},
            )
        )
        self._metrics.increment("conversation_turns_total", attributes=attributes)

        with self._tracer.start_span("conversation.turn", attributes=attributes) as span:
            llm_started = monotonic()
            try:
                decision = await self._llm.decide(transcript=transcript, state=state)
            except Exception as exc:
                span.record_error(exc)
                self._metrics.increment("llm_errors_total", attributes=attributes)

                fallback_state = state.model_copy(deep=True)
                fallback_state.require_handoff("llm_unavailable")
                saved = await self._states.save(
                    fallback_state,
                    expected_version=stored.version,
                )
                await self._audit.emit(
                    AuditEvent(
                        event_type=AuditEventType.HANDOFF_REQUESTED,
                        call_id=state.call_id,
                        conversation_id=state.conversation_id,
                        correlation_id=correlation_id,
                        metadata={"reason": "llm_unavailable"},
                    )
                )
                self._metrics.increment("handoffs_total", attributes=attributes)

                return SessionTurnResult(
                    orchestration=OrchestrationResult(
                        state=fallback_state,
                        action=OrchestratorAction.HANDOFF,
                        reason="llm_unavailable",
                    ),
                    state_version=saved.version,
                )
            finally:
                self._metrics.observe(
                    "llm_decision_latency_seconds",
                    monotonic() - llm_started,
                    attributes=attributes,
                )

            span.set_attribute("intent", decision.intent.value)
            span.set_attribute("next_action", decision.next_action.value)

            await self._audit.emit(
                AuditEvent(
                    event_type=AuditEventType.LLM_DECISION,
                    call_id=state.call_id,
                    conversation_id=state.conversation_id,
                    correlation_id=correlation_id,
                    metadata={
                        "intent": decision.intent.value,
                        "confidence": decision.confidence,
                        "next_action": decision.next_action.value,
                    },
                )
            )

            orchestration = self._orchestrator.process_decision(state, decision)
            saved = await self._states.save(
                orchestration.state,
                expected_version=stored.version,
            )

            if orchestration.action is OrchestratorAction.HANDOFF:
                await self._audit.emit(
                    AuditEvent(
                        event_type=AuditEventType.HANDOFF_REQUESTED,
                        call_id=state.call_id,
                        conversation_id=state.conversation_id,
                        correlation_id=correlation_id,
                        metadata={"reason": orchestration.reason},
                    )
                )
                self._metrics.increment("handoffs_total", attributes=attributes)

            return SessionTurnResult(
                orchestration=orchestration,
                state_version=saved.version,
            )
