from __future__ import annotations

from app.audit.models import AuditEvent
from app.audit.sink import AuditSink
from app.security.pii import sanitize_mapping


class SafeAuditSink:
    """Sanitizes audit metadata before delegating to durable storage."""

    def __init__(self, sink: AuditSink) -> None:
        self._sink = sink

    async def emit(self, event: AuditEvent) -> None:
        sanitized = event.model_copy(
            update={"metadata": sanitize_mapping(event.metadata)},
            deep=True,
        )
        await self._sink.emit(sanitized)
