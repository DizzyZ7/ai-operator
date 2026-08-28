from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
    CALL_STARTED = "CALL_STARTED"
    TURN_RECEIVED = "TURN_RECEIVED"
    LLM_DECISION = "LLM_DECISION"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    TOOL_REQUESTED = "TOOL_REQUESTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    HANDOFF_REQUESTED = "HANDOFF_REQUESTED"
    CALL_ENDED = "CALL_ENDED"


class AuditEvent(BaseModel):
    event_type: AuditEventType
    call_id: str
    conversation_id: str
    correlation_id: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
