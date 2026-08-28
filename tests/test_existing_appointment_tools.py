from datetime import UTC, datetime, timedelta

import pytest

from app.appointments.models import AvailableSlot
from app.appointments.offers import build_slot_options
from app.conversations.models import ConversationState, PatientRef
from app.idempotency.memory import MemoryIdempotencyStore
from app.tools.context import build_tool_execution_context
from app.tools.existing_appointments import (
    CancelAppointmentTool,
    ConfirmAppointmentTool,
    RescheduleAppointmentTool,
)
from tests.fakes.scheduling import FakeSchedulingProvider


def slot(slot_id: str = "slot-2") -> AvailableSlot:
    starts_at = datetime(2026, 9, 5, 19, 0, tzinfo=UTC)
    return AvailableSlot(
        slot_id=slot_id,
        clinic_id="clinic-1",
        service_id="service-1",
        doctor_id="doctor-1",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
    )


def state(
    *,
    verified: bool = True,
    patient_id: str = "patient-1",
    appointment_ids: frozenset[str] = frozenset({"appointment-1"}),
    with_slot: bool = True,
) -> ConversationState:
    current = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        patient=PatientRef(
            external_patient_id=patient_id,
            identity_verified=verified,
        ),
        authorized_appointment_ids=appointment_ids,
    )
    if with_slot:
        current.offered_options = build_slot_options([slot()])
    return current


def context(
    current: ConversationState,
    *,
    idempotency_key: str = "idem-1",
):
    return build_tool_execution_context(
        current,
        correlation_id="corr-1",
        permissions=frozenset(
            {
                "appointments:update",
                "appointments:cancel",
                "appointments:confirm",
            }
        ),
        idempotency_key=idempotency_key,
    )


@pytest.mark.asyncio
async def test_cancel_rejects_unverified_patient_before_provider_call() -> None:
    scheduling = FakeSchedulingProvider()
    tool = CancelAppointmentTool(scheduling, MemoryIdempotencyStore())

    result = await tool.execute(
        context(state(verified=False)),
        {"patient_id": "patient-1", "appointment_id": "appointment-1"},
    )

    assert result.success is False
    assert result.error_code == "appointment_not_authorized_for_patient"
    assert scheduling.cancel_calls == 0


@pytest.mark.asyncio
async def test_cancel_rejects_foreign_appointment_id() -> None:
    scheduling = FakeSchedulingProvider()
    tool = CancelAppointmentTool(scheduling, MemoryIdempotencyStore())

    result = await tool.execute(
        context(state()),
        {"patient_id": "patient-1", "appointment_id": "appointment-other"},
    )

    assert result.success is False
    assert result.error_code == "appointment_not_authorized_for_patient"
    assert scheduling.cancel_calls == 0


@pytest.mark.asyncio
async def test_cancel_rejects_mismatched_patient_id() -> None:
    scheduling = FakeSchedulingProvider()
    tool = CancelAppointmentTool(scheduling, MemoryIdempotencyStore())

    result = await tool.execute(
        context(state()),
        {"patient_id": "patient-2", "appointment_id": "appointment-1"},
    )

    assert result.success is False
    assert result.error_code == "appointment_not_authorized_for_patient"
    assert scheduling.cancel_calls == 0


@pytest.mark.asyncio
async def test_reschedule_rejects_slot_not_offered_in_current_call() -> None:
    scheduling = FakeSchedulingProvider(slots=[slot("slot-secret")])
    tool = RescheduleAppointmentTool(scheduling, MemoryIdempotencyStore())

    result = await tool.execute(
        context(state(with_slot=False)),
        {
            "patient_id": "patient-1",
            "appointment_id": "appointment-1",
            "target_slot_id": "slot-secret",
        },
    )

    assert result.success is False
    assert result.error_code == "slot_not_authorized_for_call"
    assert scheduling.reschedule_calls == 0


@pytest.mark.asyncio
async def test_verified_reschedule_uses_owned_appointment_and_offered_slot() -> None:
    trusted_slot = slot()
    scheduling = FakeSchedulingProvider(slots=[trusted_slot])
    tool = RescheduleAppointmentTool(scheduling, MemoryIdempotencyStore())

    result = await tool.execute(
        context(state()),
        {
            "patient_id": "patient-1",
            "appointment_id": "appointment-1",
            "target_slot_id": trusted_slot.slot_id,
        },
    )

    assert result.success is True
    assert result.data["appointment_id"] == "appointment-1"
    assert scheduling.reschedule_calls == 1


@pytest.mark.asyncio
async def test_verified_confirm_and_cancel_execute_once() -> None:
    scheduling = FakeSchedulingProvider()
    store = MemoryIdempotencyStore()

    confirm_result = await ConfirmAppointmentTool(scheduling, store).execute(
        context(state(), idempotency_key="confirm-1"),
        {"patient_id": "patient-1", "appointment_id": "appointment-1"},
    )
    cancel_result = await CancelAppointmentTool(scheduling, store).execute(
        context(state(), idempotency_key="cancel-1"),
        {"patient_id": "patient-1", "appointment_id": "appointment-1"},
    )

    assert confirm_result.success is True
    assert cancel_result.success is True
    assert scheduling.confirm_calls == 1
    assert scheduling.cancel_calls == 1
