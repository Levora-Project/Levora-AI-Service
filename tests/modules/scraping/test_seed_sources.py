import pytest

from src.modules.scraping.scripts.seed_sources import INITIAL_SOURCES, seed_sources


@pytest.mark.asyncio
async def test_seed_sources_creates_almin7_and_grabscholarship(test_db):
    """التحقق من أن seed_sources ينشئ المصادر الأساسية بما فيها almin7 و grabscholarship."""
    seeded = await seed_sources(db=test_db)
    names = {s.name for s in seeded}
    assert "almin7" in names
    assert "grabscholarship" in names


@pytest.mark.asyncio
async def test_seed_sources_is_idempotent(test_db):
    """التحقق من أن تكرار تشغيل seed_sources لا يكرر السجلات (Idempotent)."""
    await seed_sources(db=test_db)
    await seed_sources(db=test_db)
    count = await test_db.source.count()
    assert count == len(INITIAL_SOURCES)
