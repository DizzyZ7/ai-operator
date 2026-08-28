from __future__ import annotations

import asyncio

from app.audit.models import AuditEvent


class MemoryAuditSink:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def emit(self, event: AuditEvent) -> None:
        async with self._lock:
            self._events.append(event.model_copy(deep=True))

    async def events(self) -> list[AuditEvent]:
        async with self._lock:
            return [event.model_copy(deep=True) for event in self._events]
