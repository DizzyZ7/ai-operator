from __future__ import annotations

from app.conversations.models import DialogState

_ALLOWED_TRANSITIONS: dict[DialogState, frozenset[DialogState]] = {
    DialogState.NEW: frozenset({DialogState.INITIALIZING}),
    DialogState.INITIALIZING: frozenset({DialogState.GREETING, DialogState.FALLBACK}),
    DialogState.GREETING: frozenset({DialogState.LISTENING, DialogState.HANDOFF}),
    DialogState.LISTENING: frozenset(
        {DialogState.UNDERSTANDING, DialogState.CLOSING, DialogState.HANDOFF}
    ),
    DialogState.UNDERSTANDING: frozenset(
        {DialogState.POLICY_CHECK, DialogState.COLLECTING_INFO, DialogState.HANDOFF}
    ),
    DialogState.POLICY_CHECK: frozenset(
        {
            DialogState.PLANNING,
            DialogState.RESPONDING,
            DialogState.HANDOFF,
            DialogState.FALLBACK,
        }
    ),
    DialogState.PLANNING: frozenset(
        {
            DialogState.COLLECTING_INFO,
            DialogState.AWAITING_CONFIRMATION,
            DialogState.TOOL_EXECUTION,
            DialogState.RESPONDING,
            DialogState.HANDOFF,
            DialogState.CLOSING,
        }
    ),
    DialogState.COLLECTING_INFO: frozenset({DialogState.RESPONDING, DialogState.LISTENING}),
    DialogState.AWAITING_CONFIRMATION: frozenset(
        {DialogState.TOOL_EXECUTION, DialogState.LISTENING, DialogState.HANDOFF}
    ),
    DialogState.TOOL_EXECUTION: frozenset(
        {DialogState.PLANNING, DialogState.RESPONDING, DialogState.FALLBACK, DialogState.HANDOFF}
    ),
    DialogState.RESPONDING: frozenset(
        {DialogState.LISTENING, DialogState.CLOSING, DialogState.HANDOFF}
    ),
    DialogState.HANDOFF: frozenset({DialogState.CLOSING, DialogState.ENDED}),
    DialogState.FALLBACK: frozenset(
        {DialogState.LISTENING, DialogState.HANDOFF, DialogState.CLOSING}
    ),
    DialogState.CLOSING: frozenset({DialogState.ENDED}),
    DialogState.ENDED: frozenset(),
}


class InvalidStateTransition(ValueError):
    pass


def can_transition(source: DialogState, target: DialogState) -> bool:
    return target in _ALLOWED_TRANSITIONS[source]


def require_transition(source: DialogState, target: DialogState) -> None:
    if not can_transition(source, target):
        raise InvalidStateTransition(f"Invalid dialog transition: {source} -> {target}")
