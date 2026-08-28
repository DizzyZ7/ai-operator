from datetime import UTC, datetime, timedelta

import pytest

from app.appointments.models import AvailableSlot
from app.appointments.offers import build_slot_options
from app.conversations.models import ConversationState
from app.idempotency.memory import MemoryIdempotencyStore
from app.tools.appointments import CreateAppointmentTool
from app.tools.context import build_tool_execution_context
from tests.fakes.scheduling import FakeSchedulingProvider


def slot(slot_id: str = "slot-1") -> AvailableSlot:
    starts_at = datetime(2026, 9, 4, 18, 30, tzinfo=UTC)
    return AvailableSlot(
        slot_id=slot_id,
        clinic_id="clinic-1",
        service_id="service-1",
        doctor_id="doctor-1",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
    )


def state_with_slots(*slots: AvailableSlot) -> ConversationState:
    state = ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")
    state.offered_options = build_slot_options(list(slots))
    return state


def arguments(slot_id: str = "slot-1") -> dict[str, str]:
    return {
        "patient_id": "patient-1",
        "slot_id": slot_id,
        "clinic_id": "clinic-1",
        "service_id": "service-1",
        "doctor_id": "doctor-1",
    }


@pytest.mark.asyncio
async def test_unoffered_slot_cannot_be_booked() -> None:
    scheduling = FakeSchedulingProvider(slots=[slot("slot-1"), slot("slot-evil")])
    tool = CreateAppointmentTool(scheduling, MemoryIdempotencyStore())
    context = build_tool_execution_context(
        state_with_slots(slot("slot-1")),
        correlation_id="corr-1",
        permissions=frozenset({"appointments:create"}),
        idempotency_key="idem-1",
    )

    result = await tool.execute(context, arguments("slot-evil"))

    assert result.success is False
    assert result.error_code == "slot_not_authorized_for_call"
    assert scheduling.create_calls == 0


@pytest.mark.asyncio
async def test_duplicate_replay_returns_original_result_without_second_booking() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot])
    tool = CreateAppointmentTool(scheduling, MemoryIdempotencyStore())
    context = build_tool_execution_context(
        state_with_slots(trusted_slot),
        correlation_id="corr-1",
        permissions=frozenset({"appointments:create"}),
        idempotency_key="idem-1",
    )

    first = await tool.execute(context, arguments())
    second = await tool.execute(context, arguments())

    assert first.success is True
    assert second == first
    assert scheduling.create_calls == 1


@pytest.mark.asyncio
async def test_timeout_never_becomes_spoken_success_or_blind_retry() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot], timeout_on_create=True)
    tool = CreateAppointmentTool(scheduling, MemoryIdempotencyStore())
    context = build_tool_execution_context(
        state_with_slots(trusted_slot),
        correlation_id="corr-1",
        permissions=frozenset({"appointments:create"}),
        idempotency_key="idem-timeout",
    )

    first = await tool.execute(context, arguments())
    replay = await tool.execute(context, arguments())

    assert first.success is False
    assert first.error_code == "mutation_outcome_unknown"
    assert replay.success is False
    assert replay.error_code == "mutation_reconciliation_required"
    assert scheduling.create_calls == 1
