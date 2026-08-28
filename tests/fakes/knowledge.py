from __future__ import annotations

from app.knowledge.models import KnowledgeHit, KnowledgeQuery


class FakeKnowledgeProvider:
    def __init__(self, hits: list[KnowledgeHit]) -> None:
        self._hits = hits

    async def search(self, query: KnowledgeQuery) -> list[KnowledgeHit]:
        return [
            hit
            for hit in self._hits
            if (query.clinic_id is None or hit.clinic_id == query.clinic_id)
            and (query.service_id is None or hit.service_id == query.service_id)
            and (not query.document_types or hit.document_type in query.document_types)
        ]
