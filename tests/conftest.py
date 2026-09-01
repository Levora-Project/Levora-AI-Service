import os

import pytest
import pytest_asyncio

from prisma import Prisma

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


@pytest_asyncio.fixture
async def test_db():
    """
    Fixture لقاعدة بيانات اختبارية حقيقية.
    إذا لم يكن TEST_DATABASE_URL أو DATABASE_URL متاحاً أو تعذر الاتصال،
    يتم عمل skip للاختبار التكاملي بأمان.
    """
    if not TEST_DATABASE_URL:
        pytest.skip(
            "No TEST_DATABASE_URL or DATABASE_URL provided for live DB integration test"
        )

    db = Prisma()
    try:
        await db.connect()
    except Exception as exc:
        pytest.skip(f"Could not connect to database for integration test: {exc}")

    # Clean test tables before test run
    try:
        await db.cleanedopportunity.delete_many()
        await db.rawopportunity.delete_many()
        await db.source.delete_many(
            where={"name": {"in": ["test_source", "test_grabscholarship"]}}
        )
    except Exception:
        pass

    yield db

    # Teardown: clean up and disconnect
    try:
        if db.is_connected():
            await db.cleanedopportunity.delete_many()
            await db.rawopportunity.delete_many()
            await db.source.delete_many(
                where={"name": {"in": ["test_source", "test_grabscholarship"]}}
            )
            await db.disconnect()
    except Exception:
        pass
