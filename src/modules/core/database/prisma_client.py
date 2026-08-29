import logging

from prisma import Prisma

logger = logging.getLogger(__name__)

_client: Prisma | None = None


async def connect() -> Prisma:
    global _client
    if _client is None:
        _client = Prisma()
    if not _client.is_connected():
        await _client.connect()
        logger.info("Connected to database")
    return _client


async def disconnect() -> None:
    global _client
    if _client is not None and _client.is_connected():
        await _client.disconnect()
        logger.info("Disconnected from database")
    _client = None


def get_client() -> Prisma:
    if _client is None:
        raise RuntimeError("Database not connected. Call connect() at startup.")
    return _client
