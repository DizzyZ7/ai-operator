import pytest

from app.audit.memory import MemoryAuditSink
from app.audit.models import AuditEventType
from app.audit.safe import SafeAuditSink
from app.calls.session import CallSessionCoordinator
from app.conversations.models import ConversationState, Intent
from app.conversations.orchestrator import ConversationOrchestrator, OrchestratorAction
from app.llm.schemas import ExtractedEntities, LLMDecision, NextAction
from app.observability.memory import MemoryMetricsSink
from app.observability.tracing import NoopTracer
from app.persistence.memory import MemoryConversationStateRepository
from app.voice.playback import PlaybackController
from tests.fakes.llm import FakeLLMProvider
from tests.fakes.voice import FakeTelephonyProvider, FakeTTSProvider


def initial_state() -> ConversationState:
    return ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")


def coordinator(
    *,
    llm: FakeLLMProvider,
    repository: MemoryConversationStateRepository,
    audit: MemoryAuditSink,
    metrics: MemoryMetricsSink,
    telephony: FakeTelephonyProvider | None = None,
) -> CallSessionCoordinator:
    telephony = telephony or FakeTelephonyProvider()
    playback = PlaybackController(tts=FakeTTSProvider(), telephony=telephony)

    return CallSessionCoordinator(
        state_repository=repository,
        llm=llm,
        orchestrator=ConversationOrchestrator(),
        playback=playback,
        audit=SafeAuditSink(audit),
        metrics=metrics,
        tracer=NoopTracer(),
    )


@pytest.mark.asyncio
async def test_final_turn_updates_version_and_preserves_untrusted_entity_boundary() -> None:
    repository = MemoryConversationStateRepository()
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    llm = FakeLLMProvider(
        decision=LLMDecision(
            intent=Intent.NEW_APPOINTMENT,
            confidence=0.98,
            entities=ExtractedEntities(service="чистка"),
            next_action=NextAction.ASK_FOR_MISSING_FIELD,
            missing_fields=["date"],
        )
    )
    session = coordinator(
        llm=llm,
        repository=repository,
        audit=audit,
        metrics=metrics,
    )

    assert await session.initialize(initial_state()) == 1

    result = await session.process_final_transcript(
        conversation_id="conv-1",
        transcript="Хочу записаться на чистку",
        correlation_id="corr-1",
    )

    assert result.state_version == 2
    assert result.orchestration.action is OrchestratorAction.ASK
    assert result.orchestration.state.service_id is None
    assert result.orchestration.state.collected_fields["candidate.service"] == "чистка"
    assert metrics.counters["conversation_turns_total"] == 1
    assert len(metrics.observations["llm_decision_latency_seconds"]) == 1

    events = await audit.events()
    event_types = [event.event_type for event in events]
    assert AuditEventType.CALL_STARTED in event_types
    assert AuditEventType.TURN_RECEIVED in event_types
    assert AuditEventType.LLM_DECISION in event_types


@pytest.mark.asyncio
async def test_llm_failure_becomes_persisted_handoff_instead_of_uncaught_call_failure() -> None:
    repository = MemoryConversationStateRepository()
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    llm = FakeLLMProvider(error=TimeoutError("provider timeout"))
    session = coordinator(
        llm=llm,
        repository=repository,
        audit=audit,
        metrics=metrics,
    )
    await session.initialize(initial_state())

    result = await session.process_final_transcript(
        conversation_id="conv-1",
        transcript="Алло",
        correlation_id="corr-2",
    )

    assert result.orchestration.action is OrchestratorAction.HANDOFF
    assert result.orchestration.state.handoff_reason == "llm_unavailable"
    assert result.state_version == 2
    assert metrics.counters["llm_errors_total"] == 1
    assert metrics.counters["handoffs_total"] == 1

    stored = await repository.get("conv-1")
    assert stored is not None
    assert stored.state.handoff_required is True


@pytest.mark.asyncio
async def test_speech_start_interrupts_active_playback() -> None:
    repository = MemoryConversationStateRepository()
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    telephony = FakeTelephonyProvider()
    llm = FakeLLMProvider(
        decision=LLMDecision(
            intent=Intent.FIND_CLINIC,
            confidence=0.99,
            next_action=NextAction.ASK_CLARIFYING_QUESTION,
        )
    )
    playback = PlaybackController(tts=FakeTTSProvider(), telephony=telephony)
    session = CallSessionCoordinator(
        state_repository=repository,
        llm=llm,
        orchestrator=ConversationOrchestrator(),
        playback=playback,
        audit=SafeAuditSink(audit),
        metrics=metrics,
        tracer=NoopTracer(),
    )

    await playback.start(call_id="call-1", text="long response")
    await telephony.send_started.wait()

    interrupted = await session.on_patient_speech_started(call_id="call-1")

    assert interrupted is True
    assert metrics.counters["barge_ins_total"] == 1
