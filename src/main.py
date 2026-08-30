import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.v1 import health, scrape, webhook
from src.modules.core.config.settings import get_settings
from src.modules.core.database.prisma_client import connect, disconnect

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يفتح اتصال قاعدة البيانات عند الإقلاع ويغلقه عند الإيقاف."""
    await connect()
    logger.info("Service started in %s mode", settings.environment)
    yield
    await disconnect()


app = FastAPI(
    title="Levora Python Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(webhook.router)
