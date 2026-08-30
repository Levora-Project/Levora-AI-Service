"""Pydantic DTO for CleanedOpportunity, matching the Prisma `CleanedOpportunity` model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now() -> datetime:
    """Timezone-aware UTC timestamp (datetime.utcnow() is deprecated in 3.12+)."""
    return datetime.now(timezone.utc)


class CleanedOpportunityDTO(BaseModel):
    """Mirrors the `CleanedOpportunity` Prisma model.

    Relation fields (`raw_opportunity`, `source`) are intentionally NOT
    included here — they are Prisma relations, not real columns, and have
    no place in a write/create DTO. Only the foreign-key scalars
    (`raw_opportunity_id`, `source_id`) are kept. If a "read" shape that
    includes the nested related objects is ever needed, build a separate
    response model instead of overloading this one.

    `opportunity_type`, `funding_type`, and `status` are kept as plain
    `str` (not Enum) intentionally, until the real value set coming from
    all adapters/sources has stabilized. Known values as of now:

    - opportunity_type: "scholarship" | "internship" | "training" | "fellowship"
    - funding_type: "fully_funded" | "partially_funded" | "unfunded"
    - status: "pending" | "cleaned" | "failed"

    A validator normalizes casing/whitespace on these three fields
    (lowercased + stripped) so "Scholarship" and "scholarship" from
    different adapters don't end up as distinct values in the DB — this
    is normalization only, no value is rejected. Once the adapters agree
    on a fixed vocabulary, convert these back to `Enum` for stronger
    validation.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    raw_opportunity_id: UUID | None = None
    source_id: UUID

    title: str = Field(..., min_length=1)
    organization: str | None = None
    opportunity_type: str | None = None
    description: str | None = None
    eligibility: dict[str, Any] = Field(default_factory=dict)
    location: str | None = None
    is_remote: bool = False
    funding_type: str | None = None
    deadline: datetime | None = None
    application_url: str | None = None
    source_url: str = Field(..., min_length=1)
    country: str | None = None
    study_levels: list[str] = Field(default_factory=list)
    fields_of_study: list[str] = Field(default_factory=list)

    status: str = Field(default="pending")
    error_message: str | None = None
    content_hash: str | None = None

    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime | None = None

    @field_validator("opportunity_type", "funding_type", "status", mode="after")
    @classmethod
    def _normalize_casing(cls, value: str | None) -> str | None:
        """Lowercase + strip these free-text fields so casing differences
        between adapters don't create duplicate/inconsistent values.
        Does not validate or reject anything — pure normalization.
        """
        if value is None:
            return value
        return value.lower().strip()