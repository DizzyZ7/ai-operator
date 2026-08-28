from app.conversations.models import ConversationState, Intent, PatientRef
from app.handoff.models import build_handoff_package


def test_handoff_package_preserves_context_for_human_operator() -> None:
    state = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        intent=Intent.RESCHEDULE_APPOINTMENT,
        patient=PatientRef(
            external_patient_id="patient-1",
            phone="+70000000000",
            identity_verified=True,
        ),
        collected_fields={"candidate.date": "2026-09-04"},
        conversation_summary="Patient wants to move an existing appointment.",
    )
    state.require_handoff("scheduling_backend_unavailable")

    package = build_handoff_package(
        state,
        actions_already_attempted=["get_patient_appointments", "get_available_slots"],
    )

    assert package.intent is Intent.RESCHEDULE_APPOINTMENT
    assert package.patient.external_patient_id == "patient-1"
    assert package.collected_information["candidate.date"] == "2026-09-04"
    assert package.reason_for_handoff == "scheduling_backend_unavailable"
    assert package.actions_already_attempted == [
        "get_patient_appointments",
        "get_available_slots",
    ]
