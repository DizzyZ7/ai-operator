from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class KnowledgeDocumentType(StrEnum):
    CLINIC = "CLINIC"
    SERVICE = "SERVICE"
    PRICE = "PRICE"
    PROMOTION = "PROMOTION"
    PREPARATION = "PREPARATION"
    POLICY = "POLICY"
    FAQ = "FAQ"


class KnowledgeQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    clinic_id: str | None = None
    service_id: str | None = None
    document_types: frozenset[KnowledgeDocumentType] = Field(default_factory=frozenset)
    max_results: int = Field(default=5, ge=1, le=20)


class KnowledgeHit(BaseModel):
    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    document_type: KnowledgeDocumentType
    text: str = Field(min_length=1)
    version: int = Field(ge=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    clinic_id: str | None = None
    service_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_validity_window(self) -> KnowledgeHit:
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_to <= self.valid_from
        ):
            raise ValueError("valid_to must be later than valid_from")
        return self

    def is_valid_at(self, moment: datetime | None = None) -> bool:
        moment = moment or datetime.now(UTC)

        if self.valid_from is not None and moment < self.valid_from:
            return False
        if self.valid_to is not None and moment >= self.valid_to:
            return False
        return True
