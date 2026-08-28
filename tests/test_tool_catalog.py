from app.tools.catalog import TOOL_SPECS, TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolRisk


def test_tool_names_are_unique() -> None:
    assert len(TOOL_SPECS) == len(TOOL_SPECS_BY_NAME)


def test_critical_appointment_mutations_are_guarded() -> None:
    for name in ("create_appointment", "reschedule_appointment", "cancel_appointment"):
        spec = TOOL_SPECS_BY_NAME[name]
        assert spec.risk in {ToolRisk.MUTATION, ToolRisk.SENSITIVE_MUTATION}
        assert spec.requires_confirmation is True
        assert spec.requires_idempotency is True
