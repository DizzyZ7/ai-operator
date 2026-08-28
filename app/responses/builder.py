from __future__ import annotations

from app.responses.models import ResponseKind, ResponsePlan
from app.tools.execution import ToolActionOutcome, ToolExecutionDirective


class ResponseEvidenceError(ValueError):
    pass


_MUTATION_TEMPLATES: dict[str, str] = {
    "create_appointment": "appointment_created",
    "reschedule_appointment": "appointment_rescheduled",
    "cancel_appointment": "appointment_cancelled",
    "confirm_appointment": "appointment_confirmed",
}


def _require_mutation_evidence(
    outcome: ToolActionOutcome,
    *,
    tool_name: str,
) -> str:
    if not outcome.result.success:
        raise ResponseEvidenceError("Mutation success claim requires successful tool result")

    result_appointment_id = outcome.result.data.get("appointment_id")
    if not isinstance(result_appointment_id, str) or not result_appointment_id:
        raise ResponseEvidenceError("Mutation success claim requires canonical appointment_id")

    state = outcome.state
    expected_field = (
        "appointment_id"
        if tool_name == "create_appointment"
        else f"{tool_name}.appointment_id"
    )
    confirmed_appointment_id = state.confirmed_fields.get(expected_field)

    if (
        state.appointment_id != result_appointment_id
        or confirmed_appointment_id != result_appointment_id
    ):
        raise ResponseEvidenceError(
            "Mutation success claim is not backed by trusted conversation state"
        )

    return result_appointment_id


def build_tool_response_plan(
    *,
    tool_name: str,
    outcome: ToolActionOutcome,
) -> ResponsePlan:
    if outcome.directive is ToolExecutionDirective.HANDOFF:
        return ResponsePlan(
            kind=ResponseKind.HANDOFF,
            template_key="handoff_required",
            source_tool=tool_name,
            business_success=False,
            facts={"reason": outcome.reason},
        )

    if outcome.directive is ToolExecutionDirective.REPLAN:
        return ResponsePlan(
            kind=ResponseKind.MUTATION_FAILURE,
            template_key="action_not_completed",
            source_tool=tool_name,
            business_success=False,
            facts={"error_code": outcome.result.error_code},
        )

    if tool_name in _MUTATION_TEMPLATES:
        appointment_id = _require_mutation_evidence(
            outcome,
            tool_name=tool_name,
        )
        return ResponsePlan(
            kind=ResponseKind.MUTATION_SUCCESS,
            template_key=_MUTATION_TEMPLATES[tool_name],
            source_tool=tool_name,
            business_success=True,
            facts={"appointment_id": appointment_id},
        )

    if tool_name == "get_available_slots":
        return ResponsePlan(
            kind=ResponseKind.INFORMATION,
            template_key="slots_available",
            source_tool=tool_name,
            facts={
                "options": [
                    option.label for option in outcome.state.offered_options[:3]
                ]
            },
        )

    return ResponsePlan(
        kind=ResponseKind.INFORMATION,
        template_key="approved_information_available",
        source_tool=tool_name,
    )
