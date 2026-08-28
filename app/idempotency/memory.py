from __future__ import annotations

import asyncio
from typing import Any

from app.idempotency.models import (
    IdempotencyClaim,
    IdempotencyRecord,
    IdempotencyStatus,
)
from app.idempotency.store import IdempotencyConflict


class MemoryIdempotencyStore:
    """Process-local implementation for tests/dev only, never multi-instance production."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    async def claim(
        self,
        *,
        key: str,
        operation: str,
        request_fingerprint: str,
    ) -> IdempotencyClaim:
        async with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                if (
                    existing.operation != operation
                    or existing.request_fingerprint != request_fingerprint
                ):
                    raise IdempotencyConflict(
                        "Idempotency key reused for a different operation or request"
                    )
                return IdempotencyClaim(created=False, record=existing.model_copy(deep=True))

            record = IdempotencyRecord(
                key=key,
                operation=operation,
                request_fingerprint=request_fingerprint,
                status=IdempotencyStatus.IN_PROGRESS,
            )
            self._records[key] = record
            return IdempotencyClaim(created=True, record=record.model_copy(deep=True))

    async def complete(
        self,
        *,
        key: str,
        result: dict[str, Any],
    ) -> IdempotencyRecord:
        async with self._lock:
            existing = self._records.get(key)
            if existing is None:
                raise KeyError("Cannot complete an idempotency key that was not claimed")

            completed = existing.model_copy(
                update={
                    "status": IdempotencyStatus.COMPLETED,
                    "result": result,
                },
                deep=True,
            )
            self._records[key] = completed
            return completed.model_copy(deep=True)

    async def get(self, key: str) -> IdempotencyRecord | None:
        async with self._lock:
            record = self._records.get(key)
            return None if record is None else record.model_copy(deep=True)
