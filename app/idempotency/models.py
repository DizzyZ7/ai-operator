from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IdempotencyStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class IdempotencyRecord(BaseModel):
    key: str
    operation: str
    request_fingerprint: str
    status: IdempotencyStatus
    result: dict[str, Any] = Field(default_factory=dict)


class IdempotencyClaim(BaseModel):
    created: bool
    record: IdempotencyRecord
