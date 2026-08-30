import logging

from fastapi import APIRouter, Depends, status

from src.api.dependencies import require_api_key
from src.modules.core.auth.models import ApiKeyInfo
from src.modules.infrastructure.webhook.webhook_client import ScrapeCompletePayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])


@router.post(
    "/scrape-complete",
    status_code=status.HTTP_200_OK,
    responses={401: {"description": "Invalid or missing API key"}},
)
async def receive_scrape_complete(
    payload: ScrapeCompletePayload,
    key_info: ApiKeyInfo = Depends(require_api_key),
) -> dict[str, str]:
    """يستقبل إشعار اكتمال الجلب (للاختبار الداخلي ومحاكاة الخدمة الرئيسية)."""
    logger.info(
        "Received scrape-complete from %s: batch %s, %d opportunities, "
        "%d succeeded, %d failed",
        key_info.name,
        payload.batch_id,
        payload.total_opportunities,
        len(payload.succeeded_sources),
        len(payload.failed_sources),
    )

    return {"status": "received", "batch_id": payload.batch_id}
