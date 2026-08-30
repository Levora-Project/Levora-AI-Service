import hashlib
import logging
from datetime import UTC, datetime

from prisma import Prisma

from .models import ApiKeyInfo

logger = logging.getLogger(__name__)


def hash_key(raw_key: str) -> str:
    """يحوّل المفتاح الخام إلى بصمة SHA-256 للتخزين والمقارنة."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


class ApiKeyService:
    """يتحقق من صحة مفاتيح API المخزّنة في قاعدة البيانات."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    async def validate(self, raw_key: str) -> ApiKeyInfo | None:
        """يرجع معلومات المفتاح إذا كان صالحاً، وإلا None."""
        if not raw_key:
            return None

        record = await self._db.apikey.find_unique(where={"key": hash_key(raw_key)})

        if record is None:
            return None

        if not record.is_active:
            logger.warning("Inactive API key used: %s", record.name)
            return None

        if record.expires_at is not None and record.expires_at < datetime.now(UTC):
            logger.warning("Expired API key used: %s", record.name)
            return None

        await self._db.apikey.update(
            where={"id": record.id},
            data={"last_used_at": datetime.now(UTC)},
        )

        return ApiKeyInfo(
            id=record.id,
            name=record.name,
            is_active=record.is_active,
            expires_at=record.expires_at,
        )
