import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status

from src.api.dependencies import get_scraper_service, require_api_key
from src.api.models.scrape_requests import ScrapeRunRequest
from src.api.models.scrape_responses import ScrapeRunResponse
from src.api.protocols import ScraperServiceProtocol
from src.modules.core.auth.models import ApiKeyInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scrape", tags=["scrape"])


async def _run_scrape(
    service: ScraperServiceProtocol, source_ids: list[str], batch_id: str
) -> None:
    """ينفّذ الجلب في الخلفية ويسجّل النتيجة."""
    try:
        result = await service.run(source_ids=source_ids, batch_id=batch_id)
    except Exception:
        logger.exception("Scrape batch %s failed", batch_id)
        return

    logger.info(
        "Scrape batch %s finished: %d opportunities",
        batch_id,
        result.total_opportunities,
    )


@router.post(
    "/run",
    response_model=ScrapeRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_scrape(
    request: ScrapeRunRequest,
    background_tasks: BackgroundTasks,
    key_info: ApiKeyInfo = Depends(require_api_key),
    service: ScraperServiceProtocol = Depends(get_scraper_service),
) -> ScrapeRunResponse:
    """يستقبل معرفات المصادر ويبدأ عملية الجلب في الخلفية."""
    batch_id = str(uuid.uuid4())

    logger.info(
        "Scrape requested by %s: batch %s, %d sources",
        key_info.name,
        batch_id,
        len(request.source_ids),
    )

    background_tasks.add_task(_run_scrape, service, request.source_ids, batch_id)

    return ScrapeRunResponse(
        batch_id=batch_id,
        source_count=len(request.source_ids),
    )
