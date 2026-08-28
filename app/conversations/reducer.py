from __future__ import annotations

from app.conversations.models import ConversationState
from app.llm.schemas import ExtractedEntities

_ENTITY_FIELDS: tuple[str, ...] = (
    "service",
    "clinic",
    "doctor",
    "date",
    "time_preference",
    "appointment_reference",
)


def apply_extracted_entities(
    state: ConversationState,
    entities: ExtractedEntities,
) -> ConversationState:
    """Apply model-extracted candidates without promoting them to trusted IDs."""
    updated = state.model_copy(deep=True)

    for field_name in _ENTITY_FIELDS:
        value = getattr(entities, field_name)
        if value is not None:
            updated.collected_fields[f"candidate.{field_name}"] = value

    return updated
