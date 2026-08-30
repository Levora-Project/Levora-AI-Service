from pydantic import BaseModel, Field


class ScrapeRunRequest(BaseModel):

    source_ids: list[str] = Field(min_length=1)
