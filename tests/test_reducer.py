from app.conversations.models import ConversationState
from app.conversations.reducer import apply_extracted_entities
from app.llm.schemas import ExtractedEntities


def state() -> ConversationState:
    return ConversationState(call_id="call-1", conversation_id="conv-1", trace_id="trace-1")


def test_extracted_candidates_do_not_become_trusted_ids() -> None:
    updated = apply_extracted_entities(
        state(),
        ExtractedEntities(service="чистка", clinic="Невский"),
    )

    assert updated.service_id is None
    assert updated.clinic_id is None
    assert updated.collected_fields["candidate.service"] == "чистка"
    assert updated.collected_fields["candidate.clinic"] == "Невский"


def test_patient_correction_supersedes_previous_candidate() -> None:
    first = apply_extracted_entities(state(), ExtractedEntities(date="tomorrow"))
    corrected = apply_extracted_entities(first, ExtractedEntities(date="2026-09-04"))

    assert corrected.collected_fields["candidate.date"] == "2026-09-04"
