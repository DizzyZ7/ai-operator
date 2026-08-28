from __future__ import annotations

from typing import Any, Protocol

from app.idempotency.models import IdempotencyClaim, IdempotencyRecord


class IdempotencyConflict(ValueError):
    pass


class IdempotencyStore(Protocol):
    async def claim(
        self,
        *,
        key: str,
        operation: str,
        request_fingerprint: str,
    ) -> IdempotencyClaim: ...

    async def complete(
        self,
        *,
        key: str,
        result: dict[str, Any],
    ) -> IdempotencyRecord: ...

    async def get(self, key: str) -> IdempotencyRecord | None: ...
