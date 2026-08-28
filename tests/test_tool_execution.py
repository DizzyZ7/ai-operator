from datetime import UTC, datetime, timedelta

import pytest

from app.appointments.models import AvailableSlot
from app.appointments.offers import build_slot_options
from app.audit.memory import MemoryAuditSink
from app.audit.models import AuditEventType
from app.audit.safe import SafeAuditSink
from app.conversations.models import ConversationState, DialogState, PendingAction
from app.idempotency.memory import MemoryIdempotencyStore
from app.observability.memory import MemoryMetricsSink
from app.observability.tracing import NoopTracer
from app.tools.appointments import CreateAppointmentTool, GetAvailableSlotsTool
from app.tools.execution import ToolActionExecutor, ToolExecutionDirective
from app.tools.registry import ToolRegistry
from tests.fakes.scheduling import FakeSchedulingProvider


def slot() -> AvailableSlot:
    starts_at = datetime(2026, 9, 4, 18, 30, tzinfo=UTC)
    return AvailableSlot(
        slot_id="slot-1",
        clinic_id="clinic-1",
        service_id="service-1",
        doctor_id="doctor-1",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
    )


def executor(
    registry: ToolRegistry,
    audit: MemoryAuditSink,
    metrics: MemoryMetricsSink,
) -> ToolActionExecutor:
    return ToolActionExecutor(
        registry=registry,
        audit=SafeAuditSink(audit),
        metrics=metrics,
        tracer=NoopTracer(),
        permissions=frozenset({"appointments:read", "appointments:create"}),
    )


@pytest.mark.asyncio
async def test_read_slot_tool_hydrates_trusted_offered_options() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot])
    registry = ToolRegistry()
    registry.register(GetAvailableSlotsTool(scheduling))
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        dialog_state=DialogState.TOOL_EXECUTION,
        pending_action=PendingAction(
            action="get_available_slots",
            arguments={
                "service_id": "service-1",
                "starts_after": "2026-09-04T00:00:00Z",
                "ends_before": "2026-09-05T00:00:00Z",
            },
            requires_confirmation=False,
        ),
    )

    outcome = await executor(registry, audit, metrics).execute_pending(
        state,
        correlation_id="corr-1",
    )

    assert outcome.directive is ToolExecutionDirective.RESPOND
    assert outcome.result.success is True
    assert outcome.state.offered_options[0].payload["slot_id"] == "slot-1"
    assert outcome.state.pending_action is None

    events = await audit.events()
    assert [event.event_type for event in events] == [
        AuditEventType.TOOL_REQUESTED,
        AuditEventType.TOOL_COMPLETED,
    ]


@pytest.mark.asyncio
async def test_confirmed_booking_executes_and_sets_canonical_appointment_id() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot])
    registry = ToolRegistry()
    registry.register(CreateAppointmentTool(scheduling, MemoryIdempotencyStore()))
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        dialog_state=DialogState.TOOL_EXECUTION,
        offered_options=build_slot_options([trusted_slot]),
        pending_action=PendingAction(
            action="create_appointment",
            arguments={
                "patient_id": "patient-1",
                "slot_id": "slot-1",
                "clinic_id": "clinic-1",
                "service_id": "service-1",
                "doctor_id": "doctor-1",
            },
            requires_confirmation=True,
            confirmed=True,
        ),
    )

    outcome = await executor(registry, audit, metrics).execute_pending(
        state,
        correlation_id="corr-2",
        idempotency_key="idem-1",
    )

    assert outcome.directive is ToolExecutionDirective.RESPOND
    assert outcome.state.appointment_id == "appointment-test-1"
    assert outcome.state.confirmed_fields["appointment_id"] == "appointment-test-1"
    assert scheduling.create_calls == 1


@pytest.mark.asyncio
async def test_unconfirmed_mutation_is_blocked_and_handed_off() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot])
    registry = ToolRegistry()
    registry.register(CreateAppointmentTool(scheduling, MemoryIdempotencyStore()))
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        offered_options=build_slot_options([trusted_slot]),
        pending_action=PendingAction(
            action="create_appointment",
            arguments={
                "patient_id": "patient-1",
                "slot_id": "slot-1",
                "clinic_id": "clinic-1",
                "service_id": "service-1",
            },
            requires_confirmation=True,
            confirmed=False,
        ),
    )

    outcome = await executor(registry, audit, metrics).execute_pending(
        state,
        correlation_id="corr-3",
        idempotency_key="idem-2",
    )

    assert outcome.directive is ToolExecutionDirective.HANDOFF
    assert outcome.reason == "tool_policy_violation"
    assert scheduling.create_calls == 0


@pytest.mark.asyncio
async def test_uncertain_mutation_outcome_forces_handoff_without_retry() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot], timeout_on_create=True)
    registry = ToolRegistry()
    registry.register(CreateAppointmentTool(scheduling, MemoryIdempotencyStore()))
    audit = MemoryAuditSink()
    metrics = MemoryMetricsSink()
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        offered_options=build_slot_options([trusted_slot]),
        pending_action=PendingAction(
            action="create_appointment",
            arguments={
                "patient_id": "patient-1",
                "slot_id": "slot-1",
                "clinic_id": "clinic-1",
                "service_id": "service-1",
            },
            requires_confirmation=True,
            confirmed=True,
        ),
    )

    outcome = await executor(registry, audit, metrics).execute_pending(
        state,
        correlation_id="corr-4",
        idempotency_key="idem-timeout",
    )

    assert outcome.directive is ToolExecutionDirective.HANDOFF
    assert outcome.reason == "mutation_outcome_unknown"
    assert scheduling.create_calls == 1
