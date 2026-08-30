from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.modules.core.database.prisma_client import get_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """يفحص صحة الخدمة والاتصال بقاعدة البيانات."""
    database_ok = False

    try:
        client = get_client()
        await client.query_raw("SELECT 1")
        database_ok = True
    except Exception:  # noqa: BLE001 - أي فشل هنا يعني أن القاعدة غير متاحة
        database_ok = False

    body = {
        "status": "ok" if database_ok else "degraded",
        "database": "connected" if database_ok else "unavailable",
    }
    code = status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=code, content=body)
