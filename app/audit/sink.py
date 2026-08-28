from __future__ import annotations

from typing import Protocol

from app.audit.models import AuditEvent


class AuditSink(Protocol):
    async def emit(self, event: AuditEvent) -> None: ...
