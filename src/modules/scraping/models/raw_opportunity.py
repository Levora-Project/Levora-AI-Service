"""Pydantic DTO for RawOpportunity, matching the Prisma `RawOpportunity` model.

model RawOpportunity {
id                String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
source_id         String    @map("source_id") @db.Uuid
source            Source    @relation(fields: [source_id], references: [id])
raw_payload       Json      @default("{}")
source_url        String    @db.Text
scraped_at        DateTime  @default(now())
status            String    @default("pending")     // pending, processing, cleaned, failed
error_message     String?
created_at        DateTime  @default(now())
updated_at        DateTime  @updatedAt

cleaned_opportunity CleanedOpportunity?

@@map("raw_opportunities")
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Timezone-aware UTC timestamp (datetime.utcnow() is deprecated in 3.12+)."""
    return datetime.now(timezone.utc)


class RawOpportunityDTO(BaseModel):
    """Mirrors the `RawOpportunity` Prisma model.

    Relation fields (`source`, `cleaned_opportunity`) are intentionally NOT
    included — they are Prisma relations, not real columns, and have no
    place in a write/create DTO. Only the foreign-key scalar (`source_id`)
    is kept. If a "read" shape with the nested related objects is ever
    needed, build a separate response model instead of overloading this
    one.

    `status` is kept as a plain `str` (not `Enum`) for now. Known values:
    "pending" | "processing" | "cleaned" | "failed".
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID

    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source_url: str = Field(..., min_length=1)

    scraped_at: datetime = Field(default_factory=_utc_now)
    status: str = Field(default="pending")
    error_message: str | None = None

    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime | None = None