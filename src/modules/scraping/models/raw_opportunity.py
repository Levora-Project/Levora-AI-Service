from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RawOpportunityDTO(BaseModel):
    """B-01 Pydantic model for raw scraped opportunities."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID | None = None
    source_id: UUID
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source_url: str
    status: str = "pending"
    error_message: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class RawOpportunityBase(BaseModel):
    source_id: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None
    status: str = "pending"
    error_message: str | None = None


class RawOpportunityCreate(RawOpportunityBase):
    pass


class RawOpportunityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None
    status: str = "pending"
    error_message: str | None = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
