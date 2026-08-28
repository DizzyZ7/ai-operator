from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.knowledge.models import KnowledgeQuery
from app.providers.knowledge import KnowledgeProvider
from app.tools.catalog import TOOL_SPECS_BY_NAME
from app.tools.contracts import ToolExecutionContext, ToolResult


class GetApprovedKnowledgeTool:
    spec = TOOL_SPECS_BY_NAME["get_approved_knowledge"]

    def __init__(self, provider: KnowledgeProvider) -> None:
        self._provider = provider

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: dict[str, Any],
    ) -> ToolResult:
        del context

        try:
            query = KnowledgeQuery.model_validate(arguments)
        except ValidationError:
            return ToolResult(success=False, error_code="invalid_knowledge_query")

        try:
            hits = await self._provider.search(query)
        except TimeoutError:
            return ToolResult(
                success=False,
                error_code="knowledge_timeout",
                retryable=True,
            )

        now = datetime.now(UTC)
        valid_hits = [hit for hit in hits if hit.is_valid_at(now)][: query.max_results]

        return ToolResult(
            success=True,
            data={
                "hits": [
                    {
                        "chunk_id": hit.chunk_id,
                        "source_id": hit.source_id,
                        "document_type": hit.document_type.value,
                        "text": hit.text,
                        "version": hit.version,
                        "clinic_id": hit.clinic_id,
                        "service_id": hit.service_id,
                        "valid_from": (
                            hit.valid_from.isoformat() if hit.valid_from is not None else None
                        ),
                        "valid_to": hit.valid_to.isoformat() if hit.valid_to is not None else None,
                        "metadata": hit.metadata,
                    }
                    for hit in valid_hits
                ]
            },
        )
