from __future__ import annotations

from typing import Protocol

from app.knowledge.models import KnowledgeHit, KnowledgeQuery


class KnowledgeProvider(Protocol):
    async def search(self, query: KnowledgeQuery) -> list[KnowledgeHit]: ...
