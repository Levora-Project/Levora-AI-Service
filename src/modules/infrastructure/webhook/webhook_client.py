import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from ..http.base_http_client import BaseHttpClient
from ..http.exceptions import HttpClientError
from ..http.retry_strategy import RetryStrategy

logger = logging.getLogger(__name__)


class ScrapeCompletePayload(BaseModel):
    """حمولة إشعار اكتمال الجلب المرسلة للخدمة الرئيسية."""

    batch_id: str
    total_opportunities: int = Field(ge=0)
    succeeded_sources: list[str] = Field(default_factory=list)
    failed_sources: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WebhookClient:
    """يرسل إشعارات إلى الخدمة الرئيسية عند اكتمال الجلب."""

    def __init__(
        self,
        webhook_url: str,
        secret: str = "",
        timeout: float = 15.0,
        http_client: BaseHttpClient | None = None,
    ) -> None:
        self._url = webhook_url
        self._secret = secret
        self._http = http_client or BaseHttpClient(
            timeout=timeout,
            retry_strategy=RetryStrategy(
                max_attempts=4, base_delay=1.0, max_delay=10.0
            ),
        )

    async def close(self) -> None:
        await self._http.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._secret:
            headers["X-Webhook-Secret"] = self._secret
        return headers

    async def notify_scrape_complete(self, payload: ScrapeCompletePayload) -> bool:
        """يرسل الإشعار. يرجع True عند النجاح و False عند الفشل النهائي.

        لا يرفع استثناءً: فشل الإشعار يجب ألا يُفشل عملية جلب ناجحة.
        """
        if not self._url:
            logger.warning("Webhook URL not configured; skipping notification")
            return False

        try:
            await self._http.post(
                self._url,
                content=payload.model_dump_json(),
                headers=self._headers(),
            )
        except HttpClientError:
            logger.exception("Webhook delivery failed for batch %s", payload.batch_id)
            return False

        logger.info(
            "Webhook delivered for batch %s (%d opportunities)",
            payload.batch_id,
            payload.total_opportunities,
        )
        return True
