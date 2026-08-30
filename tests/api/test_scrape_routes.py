import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_api_key_service,
    get_scraper_service,
    require_api_key,
)
from src.api.protocols import ScrapeResult
from src.api.routes.v1 import scrape
from src.modules.core.auth.api_key_auth import ApiKeyService
from src.modules.core.auth.models import ApiKeyInfo


class FakeScraperService:
    """خدمة جلب وهمية تلتزم بـ ScraperServiceProtocol."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls = []

    async def run(self, source_ids: list[str], batch_id: str) -> ScrapeResult:
        self.calls.append({"source_ids": source_ids, "batch_id": batch_id})

        if self.should_fail:
            raise RuntimeError("scraping blew up")

        return ScrapeResult(
            batch_id=batch_id,
            total_opportunities=len(source_ids) * 10,
            succeeded_sources=source_ids,
        )


class EmptyKeyTable:
    """جدول مفاتيح فارغ: أي مفتاح غير موجود."""

    async def find_unique(self, where):
        return None


class EmptyDb:
    apikey = EmptyKeyTable()


def fake_key_info() -> ApiKeyInfo:
    return ApiKeyInfo(id="key-1", name="main-service", is_active=True)


@pytest.fixture
def scraper() -> FakeScraperService:
    return FakeScraperService()


@pytest.fixture
def app(scraper) -> FastAPI:
    application = FastAPI()
    application.include_router(scrape.router)
    application.dependency_overrides[require_api_key] = fake_key_info
    application.dependency_overrides[get_scraper_service] = lambda: scraper
    return application


class TestAuthentication:
    def test_rejects_request_without_valid_key(self, scraper):
        """المفتاح غير الموجود في القاعدة يجب أن يُرفض بـ 401."""
        application = FastAPI()
        application.include_router(scrape.router)
        application.dependency_overrides[get_scraper_service] = lambda: scraper
        application.dependency_overrides[get_api_key_service] = lambda: ApiKeyService(
            db=EmptyDb()
        )

        response = TestClient(application).post(
            "/api/v1/scrape/run",
            json={"source_ids": ["src-1"]},
            headers={"X-API-Key": "bogus-key"},
        )

        assert response.status_code == 401
        assert scraper.calls == []


class TestValidation:
    def test_rejects_empty_source_ids(self, app):
        response = TestClient(app).post("/api/v1/scrape/run", json={"source_ids": []})
        assert response.status_code == 422

    def test_rejects_missing_body(self, app):
        response = TestClient(app).post("/api/v1/scrape/run", json={})
        assert response.status_code == 422

    def test_rejects_wrong_type(self, app):
        response = TestClient(app).post(
            "/api/v1/scrape/run", json={"source_ids": "not-a-list"}
        )
        assert response.status_code == 422


class TestSuccessfulRequest:
    def test_returns_202_accepted(self, app):
        response = TestClient(app).post(
            "/api/v1/scrape/run", json={"source_ids": ["src-1"]}
        )
        assert response.status_code == 202

    def test_returns_batch_id_and_count(self, app):
        response = TestClient(app).post(
            "/api/v1/scrape/run", json={"source_ids": ["src-1", "src-2"]}
        )
        body = response.json()

        assert body["source_count"] == 2
        assert body["status"] == "accepted"
        assert len(body["batch_id"]) > 0

    def test_batch_id_is_unique_per_request(self, app):
        client = TestClient(app)
        first = client.post("/api/v1/scrape/run", json={"source_ids": ["src-1"]})
        second = client.post("/api/v1/scrape/run", json={"source_ids": ["src-1"]})

        assert first.json()["batch_id"] != second.json()["batch_id"]

    def test_invokes_scraper_with_given_sources(self, app, scraper):
        response = TestClient(app).post(
            "/api/v1/scrape/run", json={"source_ids": ["src-1", "src-2"]}
        )

        assert len(scraper.calls) == 1
        assert scraper.calls[0]["source_ids"] == ["src-1", "src-2"]
        assert scraper.calls[0]["batch_id"] == response.json()["batch_id"]


class TestBackgroundFailure:
    def test_scraper_failure_does_not_break_response(self, app):
        """فشل الجلب في الخلفية يجب ألا يؤثر على الاستجابة المُرسلة مسبقاً."""
        app.dependency_overrides[get_scraper_service] = lambda: FakeScraperService(
            should_fail=True
        )

        response = TestClient(app).post(
            "/api/v1/scrape/run", json={"source_ids": ["src-1"]}
        )

        assert response.status_code == 202
