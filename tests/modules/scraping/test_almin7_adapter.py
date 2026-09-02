from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.scraping.adapters.almin7_adapter import Almin7Adapter


def test_almin7_adapter_parse_scholarship():
    adapter = Almin7Adapter()
    raw_item = {
        "title": {
            "rendered": "منحة الحكومة التركية 2026 لدراسة البكالوريوس والماجستير ممول بالكامل"
        },
        "content": {
            "rendered": "<p>منحة ممولة بالكامل في تركيا لدراسة البكالوريوس والماجستير. آخر موعد للتقديم: 20 فبراير 2026</p>"
        },
        "link": "https://almin7.com/turkey-scholarship-2026",
    }

    parsed = adapter.parse(raw_item)
    assert parsed["opportunity_type"] == "scholarship"
    assert "Bachelor" in parsed["study_levels"]
    assert "Master" in parsed["study_levels"]
    assert parsed["country"] == "تركيا"
    assert parsed["funding_type"] == "fully_funded"
    assert "20 فبراير 2026" in parsed["deadline"]


def test_almin7_adapter_determine_opportunity_types():
    adapter = Almin7Adapter()

    # Fellowship
    fellowship_item = {
        "title": {"rendered": "برنامج زمالة بحثية في ألمانيا"},
        "content": {"rendered": "زمالة ما بعد الدكتوراه"},
    }
    assert adapter.parse(fellowship_item)["opportunity_type"] == "fellowship"

    # Internship (Arabic)
    internship_item = {
        "title": {"rendered": "فرصة تدريب صيفي في كندا للطلاب"},
        "content": {"rendered": "تدريب عملي مدفوع"},
    }
    assert adapter.parse(internship_item)["opportunity_type"] == "internship"

    # Training
    training_item = {
        "title": {"rendered": "دورة تدريبية مكثفة في الذكاء الاصطناعي"},
        "content": {"rendered": "معسكر تدريبي"},
    }
    assert adapter.parse(training_item)["opportunity_type"] == "training"

    # Volunteering
    volunteering_item = {
        "title": {"rendered": "فرصة عمل تطوعي في فرنسا"},
        "content": {"rendered": "تطوع ممول بالكامل"},
    }
    assert adapter.parse(volunteering_item)["opportunity_type"] == "volunteering"

    # International scholarship regression: 'international' should NOT be internship
    international_item = {
        "title": {"rendered": "International Scholarship for Undergraduates in UK"},
        "content": {"rendered": "Full funding"},
    }
    assert adapter.parse(international_item)["opportunity_type"] == "scholarship"


def test_almin7_adapter_is_opportunity_by_category():
    adapter = Almin7Adapter()

    # 1. Opportunity category -> accepted
    opp_item = {
        "title": {"rendered": "منحة جامعة ميونخ في ألمانيا 2026"},
        "categories": ["منح دراسية", "ألمانيا"],
    }
    assert adapter.is_opportunity(opp_item) is True

    # 2. Non-opportunity category (Articles/News) -> rejected
    article_item = {
        "title": {"rendered": "كيف تختار تخصصك الجامعي الأنسب"},
        "categories": ["مقالات", "نصائح وإرشادات"],
    }
    assert adapter.is_opportunity(article_item) is False

    # 3. Fallback on title when categories are empty
    real_fallback_item = {"title": {"rendered": "منحة كندا للبكالوريوس 2026"}}
    assert adapter.is_opportunity(real_fallback_item) is True

    advice_fallback_item = {"title": {"rendered": "نصائح للدراسة في الخارج"}}
    assert adapter.is_opportunity(advice_fallback_item) is False


@pytest.mark.asyncio
async def test_almin7_adapter_fetch_20_articles_and_filter():
    adapter = Almin7Adapter()

    # 20 عنصر خام: 14 فرصة حقيقية + 6 مقالات إرشادية عامة
    raw_posts = []
    for i in range(1, 15):
        raw_posts.append(
            {
                "id": i,
                "title": {
                    "rendered": f"منحة ممولة بالكامل رقم {i} لدراسة البكالوريوس في تركيا"
                },
                "content": {
                    "rendered": f"<p>تفاصيل المنحة رقم {i}. آخر موعد: 20 مارس 2026</p>"
                },
                "categories": ["منح دراسية", "تركيا"],
                "link": f"https://almin7.com/scholarship-{i}",
            }
        )
    for j in range(15, 21):
        raw_posts.append(
            {
                "id": j,
                "title": {"rendered": f"نصائح وإرشادات عامة رقم {j} للدراسة في الخارج"},
                "content": {"rendered": f"<p>مقال عام غير مرتبط بمنحة {j}.</p>"},
                "categories": ["مقالات", "نصائح"],
                "link": f"https://almin7.com/article-{j}",
            }
        )

    mock_response = MagicMock()
    mock_response.json.return_value = raw_posts
    mock_response.is_success = True

    adapter.http_client.get = AsyncMock(return_value=mock_response)

    # 1. جلب 20 مقال بالضبط
    raw_items = await adapter.fetch(limit=20)
    assert len(raw_items) == 20

    # 2. تطبيق is_opportunity لتصفية المقالات الإرشادية
    filtered_opportunities = [
        item for item in raw_items if adapter.is_opportunity(item)
    ]

    # إثبات أن التصفية تعمل على دفعة بحجم 20 واستبعدت المقالات العامة
    assert len(filtered_opportunities) < 20
    assert len(filtered_opportunities) == 14
