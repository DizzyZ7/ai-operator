from datetime import UTC, datetime

import pytest

from app.appointments.models import PatientAppointment
from app.conversations.models import ConversationState, PatientRef
from app.tools.context import build_tool_execution_context
from app.tools.patient_appointments import GetPatientAppointmentsTool
from app.tools.reducer import apply_tool_result
from tests.fakes.medical_system import FakeMedicalSystemProvider


def appointment(
    *,
    appointment_id: str = "appointment-1",
    patient_id: str = "patient-1",
) -> PatientAppointment:
    return PatientAppointment(
        appointment_id=appointment_id,
        patient_id=patient_id,
        clinic_id="clinic-1",
        service_id="service-1",
        doctor_id="doctor-1",
        starts_at=datetime(2026, 9, 4, 18, 30, tzinfo=UTC),
        status="BOOKED",
    )


def state(*, verified: bool = True) -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        patient=PatientRef(
            external_patient_id="patient-1",
            identity_verified=verified,
        ),
    )


@pytest.mark.asyncio
async def test_verified_patient_appointments_hydrate_ownership_grants() -> None:
    medical = FakeMedicalSystemProvider([appointment()])
    tool = GetPatientAppointmentsTool(medical)
    current = state()
    context = build_tool_execution_context(
        current,
        correlation_id="corr-1",
        permissions=frozenset({"appointments:read"}),
    )

    result = await tool.execute(context, {"patient_id": "patient-1"})
    updated = apply_tool_result(
        current,
        tool_name="get_patient_appointments",
        result=result,
    )

    assert result.success is True
    assert updated.authorized_appointment_ids == frozenset({"appointment-1"})


@pytest.mark.asyncio
async def test_unverified_patient_cannot_query_existing_appointments() -> None:
    medical = FakeMedicalSystemProvider([appointment()])
    tool = GetPatientAppointmentsTool(medical)
    context = build_tool_execution_context(
        state(verified=False),
        correlation_id="corr-1",
        permissions=frozenset({"appointments:read"}),
    )

    result = await tool.execute(context, {"patient_id": "patient-1"})

    assert result.success is False
    assert result.error_code == "patient_identity_not_authorized"
    assert medical.calls == 0


@pytest.mark.asyncio
async def test_verified_patient_cannot_query_different_patient_id() -> None:
    medical = FakeMedicalSystemProvider([appointment()])
    tool = GetPatientAppointmentsTool(medical)
    context = build_tool_execution_context(
        state(),
        correlation_id="corr-1",
        permissions=frozenset({"appointments:read"}),
    )

    result = await tool.execute(context, {"patient_id": "patient-2"})

    assert result.success is False
    assert result.error_code == "patient_identity_not_authorized"
    assert medical.calls == 0
