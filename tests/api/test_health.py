import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.v1 import health


class FakeClient:
    """عميل قاعدة بيانات وهمي."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.queries = []

    async def query_raw(self, query: str):
        if self.should_fail:
            raise ConnectionError("database unreachable")
        self.queries.append(query)
        return [{"?column?": 1}]


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(health.router)
    return application


class TestHealthEndpoint:
    def test_returns_ok_when_database_reachable(self, app, monkeypatch):
        monkeypatch.setattr(health, "get_client", lambda: FakeClient())

        response = TestClient(app).get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "connected"}

    def test_returns_503_when_database_fails(self, app, monkeypatch):
        monkeypatch.setattr(health, "get_client", lambda: FakeClient(should_fail=True))

        response = TestClient(app).get("/health")

        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert response.json()["database"] == "unavailable"

    def test_returns_503_when_client_not_initialised(self, app, monkeypatch):
        def raise_runtime_error():
            raise RuntimeError("Database not connected")

        monkeypatch.setattr(health, "get_client", raise_runtime_error)

        response = TestClient(app).get("/health")

        assert response.status_code == 503

    def test_actually_queries_the_database(self, app, monkeypatch):
        fake = FakeClient()
        monkeypatch.setattr(health, "get_client", lambda: fake)

        TestClient(app).get("/health")

        assert fake.queries == ["SELECT 1"]
