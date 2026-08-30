from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class ScrapeResult(BaseModel):

    batch_id: str
    total_opportunities: int
    succeeded_sources: list[str] = []
    failed_sources: list[str] = []


@runtime_checkable
class ScraperServiceProtocol(Protocol):

    async def run(self, source_ids: list[str], batch_id: str) -> ScrapeResult: ...
