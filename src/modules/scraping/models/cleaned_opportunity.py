import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CleanedOpportunityDTO(BaseModel):
    """B-01 Pydantic model for cleaned/normalized opportunities."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID | None = None
    raw_opportunity_id: UUID | None = None
    source_id: UUID
    title: str
    organization: str | None = None
    opportunity_type: str | None = None
    description: str | None = None
    eligibility: dict[str, Any] = Field(default_factory=dict)
    location: str | None = None
    is_remote: bool | None = False
    funding_type: str | None = None
    deadline: datetime | None = None
    application_url: str | None = None
    source_url: str
    country: str | None = None
    study_levels: list[str] = Field(default_factory=list)
    fields_of_study: list[str] = Field(default_factory=list)
    status: str | None = "pending"
    error_message: str | None = None
    content_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @field_validator("opportunity_type", mode="before")
    @classmethod
    def _normalize_opp_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return re.sub(r"\s+", " ", v.strip().lower())
        return v

    @field_validator("funding_type", mode="before")
    @classmethod
    def _normalize_funding_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return re.sub(r"\s+", " ", v.strip().lower())
        return v


class CleanedOpportunityBase(BaseModel):
    raw_opportunity_id: str | None = None
    source_id: str | None = None
    title: str
    organization: str | None = None
    opportunity_type: str | None = None
    description: str | None = None
    eligibility: dict[str, Any] | None = Field(default_factory=dict)
    location: str | None = None
    is_remote: bool | None = False
    funding_type: str | None = None
    deadline: datetime | None = None
    application_url: str | None = None
    source_url: str
    country: str | None = None
    study_levels: list[str] = Field(default_factory=list)
    fields_of_study: list[str] = Field(default_factory=list)
    status: str | None = "cleaned"
    error_message: str | None = None
    content_hash: str | None = None


class CleanedOpportunityCreate(CleanedOpportunityBase):
    pass


class CleanedOpportunityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_opportunity_id: str | None = None
    source_id: str | None = None
    title: str
    organization: str | None = None
    opportunity_type: str | None = None
    description: str | None = None
    eligibility: dict[str, Any] | None = Field(default_factory=dict)
    location: str | None = None
    is_remote: bool | None = False
    funding_type: str | None = None
    deadline: datetime | None = None
    application_url: str | None = None
    source_url: str
    country: str | None = None
    study_levels: list[str] = Field(default_factory=list)
    fields_of_study: list[str] = Field(default_factory=list)
    status: str | None = "cleaned"
    error_message: str | None = None
    content_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
