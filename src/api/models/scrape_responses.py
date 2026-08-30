from pydantic import BaseModel


class ScrapeRunResponse(BaseModel):

    batch_id: str
    status: str = "accepted"
    source_count: int
    message: str = "Scraping started; a webhook will be sent on completion."
