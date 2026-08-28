from app.reliability.fallback import (
    FailedComponent,
    FallbackAction,
    decide_fallback,
)


def test_unknown_mutation_outcome_is_never_confirmed() -> None:
    decision = decide_fallback(
        FailedComponent.SCHEDULING,
        mutation_may_have_committed=True,
    )

    assert decision.action is FallbackAction.DO_NOT_CONFIRM_MUTATION
    assert decision.reason == "mutation_outcome_unknown"


def test_llm_failure_routes_to_human_instead_of_hanging_call() -> None:
    decision = decide_fallback(FailedComponent.LLM)

    assert decision.action is FallbackAction.HUMAN_HANDOFF
