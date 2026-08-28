import pytest

from app.conversations.models import ConversationState, OfferedOption
from app.responses.builder import ResponseEvidenceError, build_tool_response_plan
from app.responses.models import ResponseKind
from app.responses.render import render_response
from app.tools.contracts import ToolResult
from app.tools.execution import ToolActionOutcome, ToolExecutionDirective


def state_with_create_evidence(
    appointment_id: str = "appointment-secret-1",
) -> ConversationState:
    return ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        appointment_id=appointment_id,
        confirmed_fields={"appointment_id": appointment_id},
    )


def outcome(
    *,
    state: ConversationState,
    success: bool,
    appointment_id: str | None,
    directive: ToolExecutionDirective = ToolExecutionDirective.RESPOND,
    error_code: str | None = None,
) -> ToolActionOutcome:
    return ToolActionOutcome(
        state=state,
        result=ToolResult(
            success=success,
            data={"appointment_id": appointment_id} if appointment_id else {},
            error_code=error_code,
        ),
        directive=directive,
        reason="test",
    )


def test_create_success_requires_matching_backend_evidence() -> None:
    plan = build_tool_response_plan(
        tool_name="create_appointment",
        outcome=outcome(
            state=state_with_create_evidence(),
            success=True,
            appointment_id="appointment-secret-1",
        ),
    )

    assert plan.kind is ResponseKind.MUTATION_SUCCESS
    assert plan.business_success is True
    assert render_response(plan) == "Запись создана."


def test_forged_success_without_trusted_state_evidence_is_rejected() -> None:
    current = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
    )

    with pytest.raises(ResponseEvidenceError):
        build_tool_response_plan(
            tool_name="create_appointment",
            outcome=outcome(
                state=current,
                success=True,
                appointment_id="appointment-invented",
            ),
        )


def test_mismatched_tool_and_state_appointment_ids_are_rejected() -> None:
    with pytest.raises(ResponseEvidenceError):
        build_tool_response_plan(
            tool_name="create_appointment",
            outcome=outcome(
                state=state_with_create_evidence("appointment-1"),
                success=True,
                appointment_id="appointment-2",
            ),
        )


def test_handoff_after_unknown_mutation_outcome_cannot_render_success() -> None:
    plan = build_tool_response_plan(
        tool_name="create_appointment",
        outcome=outcome(
            state=state_with_create_evidence(),
            success=False,
            appointment_id=None,
            directive=ToolExecutionDirective.HANDOFF,
            error_code="mutation_outcome_unknown",
        ),
    )

    assert plan.kind is ResponseKind.HANDOFF
    assert plan.business_success is False
    assert "создана" not in render_response(plan).lower()


def test_internal_appointment_id_is_evidence_but_not_spoken() -> None:
    internal_id = "appointment-secret-123"
    plan = build_tool_response_plan(
        tool_name="create_appointment",
        outcome=outcome(
            state=state_with_create_evidence(internal_id),
            success=True,
            appointment_id=internal_id,
        ),
    )

    spoken = render_response(plan)

    assert internal_id in plan.facts.values()
    assert internal_id not in spoken


def test_slot_response_speaks_at_most_three_backend_owned_choices() -> None:
    current = ConversationState(
        call_id="call-1",
        conversation_id="conv-1",
        trace_id="trace-1",
        offered_options=[
            OfferedOption(option_id=f"option-{index}", label=f"time-{index}")
            for index in range(5)
        ],
    )
    plan = build_tool_response_plan(
        tool_name="get_available_slots",
        outcome=outcome(
            state=current,
            success=True,
            appointment_id=None,
        ),
    )

    spoken = render_response(plan)

    assert "time-0" in spoken
    assert "time-1" in spoken
    assert "time-2" in spoken
    assert "time-3" not in spoken
    assert "time-4" not in spoken
