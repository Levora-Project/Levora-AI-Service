from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prisma import Json
from src.modules.core.database.repositories.opportunity_repository import (
    OpportunityRepository,
)
from src.modules.core.database.repositories.source_repository import SourceRepository
from src.modules.scraping.services.cleaning_service import CleaningService
from src.modules.scraping.services.deduplication_service import DeduplicationService
from src.modules.scraping.services.normalization_service import NormalizationService
from src.modules.scraping.services.scraper_service import ScraperService


@pytest.mark.asyncio
async def test_full_pipeline_persists_to_real_database(test_db):
    """
    اختبار تكاملي حقيقي يثبت الكتابة الفعلية عبر Prisma ضد Schema حقيقي:
    1. إنشاء Source حقيقي في test_db
    2. تمرير test_db فعلياً لـ SourceRepository و OpportunityRepository
    3. Mock فقط لطبقة HTTP (البيانات الخام القادمة من الإنترنت)
    4. تشغيل ScraperService.run() بالكامل
    5. التحقق من تخزين السجل الخام بكل حقوله (raw_payload, source_url, status)
    6. التحقق من تخزين السجل النظيف (eligibility, study_levels String[], content_hash)
    7. التحقق من أن raw_opportunity_id يربط السجلين بشكل صحيح
    """
    # 1. أنشئ Source حقيقي في test_db (almin7)
    source = await test_db.source.create(
        data={
            "name": "almin7_integration",
            "display_name": "Almin7 Scholarships Integration",
            "base_url": "https://almin7.com",
            "api_endpoint": "/wp-json/wp/v2/posts",
            "method": "wordpress_api",
            "pagination_config": Json({"limit": 5}),
            "field_mapping": Json(
                {
                    "title": "title.rendered",
                    "content": "content.rendered",
                    "url": "link",
                    "date": "date",
                }
            ),
            "is_active": True,
        }
    )

    # 2. Mock فقط لطبقة HTTP (البيانات الخام القادمة من الإنترنت)
    mock_posts = [
        {
            "title": {
                "rendered": "منحة الحكومة التركية 2026 لدراسة البكالوريوس ممول بالكامل"
            },
            "content": {
                "rendered": "<p>منحة كاملة في تركيا تشمل الرسوم والسكن. آخر موعد للتقديم: 20 فبراير 2026</p>"
            },
            "excerpt": {"rendered": "منحة ممولة بالكامل في تركيا"},
            "categories": ["منح دراسية", "تركيا"],
            "link": "https://almin7.com/turkey-scholarship-integration/",
            "date": "2026-09-01T12:00:00",
        }
    ]

    mock_http_response = MagicMock()
    mock_http_response.json.return_value = mock_posts
    mock_http_response.is_success = True

    mock_http_client = MagicMock()
    mock_http_client.get = AsyncMock(return_value=mock_http_response)
    mock_http_client.close = AsyncMock()

    # 3. تمرير test_db فعلياً للمستودعات و ScraperService
    source_repo = SourceRepository(test_db)
    opp_repo = OpportunityRepository(test_db)
    cleaning = CleaningService()
    norm = NormalizationService()
    dedup = DeduplicationService(opp_repo)
    mock_webhook = MagicMock(notify_scrape_complete=AsyncMock(return_value=True))

    service = ScraperService(
        db=test_db,
        source_repo=source_repo,
        opportunity_repo=opp_repo,
        cleaning_service=cleaning,
        normalization_service=norm,
        deduplication_service=dedup,
        webhook_client=mock_webhook,
    )

    # 4. تشغيل ScraperService.run() بالكامل
    with patch(
        "src.modules.scraping.adapters.base_adapter.BaseHttpClient",
        return_value=mock_http_client,
    ):
        result = await service.run(
            source_ids=[source.id], batch_id="db-full-pipeline-batch"
        )

    assert result.total_opportunities == 1
    assert "almin7_integration" in result.succeeded_sources

    # 5. التحقق من السجل الخام المخزن فعلياً في جدول raw_opportunities
    raw_records = await test_db.rawopportunity.find_many(where={"source_id": source.id})
    assert len(raw_records) == 1
    raw_rec = raw_records[0]
    assert raw_rec.status == "cleaned"
    assert raw_rec.source_url == "https://almin7.com/turkey-scholarship-integration/"
    assert raw_rec.raw_payload is not None

    # 6. التحقق من السجل النظيف المخزن فعلياً في جدول cleaned_opportunities
    cleaned_records = await test_db.cleanedopportunity.find_many(
        where={"source_id": source.id}
    )
    assert len(cleaned_records) == 1
    cleaned_rec = cleaned_records[0]

    assert (
        cleaned_rec.title == "منحة الحكومة التركية 2026 لدراسة البكالوريوس ممول بالكامل"
    )
    assert cleaned_rec.opportunity_type == "scholarship"
    assert cleaned_rec.country == "تركيا"
    assert cleaned_rec.funding_type == "fully_funded"
    assert "Bachelor" in cleaned_rec.study_levels
    assert cleaned_rec.content_hash is not None
    assert cleaned_rec.deadline is not None
    assert cleaned_rec.eligibility is not None
    assert cleaned_rec.status == "cleaned"

    # 7. التحقق من أن raw_opportunity_id يربط السجلين بشكل صحيح
    assert cleaned_rec.raw_opportunity_id == raw_rec.id
