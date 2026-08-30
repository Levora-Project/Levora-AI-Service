import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_api_key_service, require_api_key
from src.api.routes.v1 import webhook
from src.modules.core.auth.api_key_auth import ApiKeyService
from src.modules.core.auth.models import ApiKeyInfo


class EmptyKeyTable:
    async def find_unique(self, where):
        return None


class EmptyDb:
    apikey = EmptyKeyTable()


def fake_key_info() -> ApiKeyInfo:
    return ApiKeyInfo(id="key-1", name="main-service", is_active=True)


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(webhook.router)
    application.dependency_overrides[require_api_key] = fake_key_info
    return application


def valid_payload() -> dict:
    return {
        "batch_id": "batch-abc",
        "total_opportunities": 25,
        "succeeded_sources": ["almin7"],
        "failed_sources": [],
    }


class TestWebhookReceiver:
    def test_accepts_valid_payload(self, app):
        response = TestClient(app).post(
            "/api/v1/webhook/scrape-complete", json=valid_payload()
        )

        assert response.status_code == 200
        assert response.json()["batch_id"] == "batch-abc"

    def test_requires_api_key(self):
        application = FastAPI()
        application.include_router(webhook.router)
        application.dependency_overrides[get_api_key_service] = lambda: ApiKeyService(
            db=EmptyDb()
        )

        response = TestClient(application).post(
            "/api/v1/webhook/scrape-complete",
            json=valid_payload(),
            headers={"X-API-Key": "bogus"},
        )

        assert response.status_code == 401

    def test_rejects_missing_batch_id(self, app):
        payload = valid_payload()
        del payload["batch_id"]

        response = TestClient(app).post("/api/v1/webhook/scrape-complete", json=payload)
        assert response.status_code == 422

    def test_rejects_negative_total(self, app):
        payload = valid_payload()
        payload["total_opportunities"] = -1

        response = TestClient(app).post("/api/v1/webhook/scrape-complete", json=payload)
        assert response.status_code == 422

    def test_accepts_minimal_payload(self, app):
        response = TestClient(app).post(
            "/api/v1/webhook/scrape-complete",
            json={"batch_id": "b-1", "total_opportunities": 0},
        )

        assert response.status_code == 200
