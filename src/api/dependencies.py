from fastapi import Depends, Header, HTTPException, status

from src.api.protocols import ScraperServiceProtocol
from src.modules.core.auth.api_key_auth import ApiKeyService
from src.modules.core.auth.models import ApiKeyInfo
from src.modules.core.database.prisma_client import get_client


def get_api_key_service() -> ApiKeyService:
    return ApiKeyService(db=get_client())


async def require_api_key(
    x_api_key: str = Header(default="", alias="X-API-Key"),
    service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyInfo:
    """تبعية تحمي نقاط النهاية: ترفض الطلب إذا كان المفتاح غير صالح."""
    key_info = await service.validate(x_api_key)

    if key_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_info


def get_scraper_service() -> ScraperServiceProtocol:
    """يرجع خدمة الجلب. تُنفَّذ في B-10 من قبل العضو الثاني."""
    try:
        from src.modules.scraping.services.scraper_service import (  # noqa: PLC0415
            ScraperService,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scraper service is not available yet",
        ) from exc

    return ScraperService(db=get_client())
