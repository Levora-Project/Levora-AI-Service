from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.api.dependencies import require_api_key
from src.modules.core.auth.api_key_auth import ApiKeyService, hash_key


class FakeApiKeyTable:
    """جدول مفاتيح وهمي يحاكي واجهة Prisma."""

    def __init__(self, record=None):
        self.record = record
        self.updates = []

    async def find_unique(self, where):
        if self.record is None:
            return None
        return self.record if self.record.key == where["key"] else None

    async def update(self, where, data):
        self.updates.append((where, data))
        return self.record


class FakeDb:
    def __init__(self, record=None):
        self.apikey = FakeApiKeyTable(record)


def make_record(raw_key="secret-key", **overrides):
    data = {
        "id": "key-1",
        "key": hash_key(raw_key),
        "name": "main-service",
        "is_active": True,
        "expires_at": None,
    }
    return SimpleNamespace(**{**data, **overrides})


class TestHashing:
    def test_is_deterministic(self):
        assert hash_key("abc") == hash_key("abc")

    def test_differs_per_input(self):
        assert hash_key("abc") != hash_key("abd")

    def test_does_not_store_raw_key(self):
        assert "abc" not in hash_key("abc")


class TestValidation:
    async def test_valid_key_returns_info(self):
        service = ApiKeyService(db=FakeDb(make_record()))
        result = await service.validate("secret-key")

        assert result is not None
        assert result.name == "main-service"

    async def test_unknown_key_returns_none(self):
        service = ApiKeyService(db=FakeDb(make_record()))
        assert await service.validate("wrong-key") is None

    async def test_empty_key_returns_none(self):
        service = ApiKeyService(db=FakeDb(make_record()))
        assert await service.validate("") is None

    async def test_inactive_key_rejected(self):
        service = ApiKeyService(db=FakeDb(make_record(is_active=False)))
        assert await service.validate("secret-key") is None

    async def test_expired_key_rejected(self):
        past = datetime.now(UTC) - timedelta(days=1)
        service = ApiKeyService(db=FakeDb(make_record(expires_at=past)))
        assert await service.validate("secret-key") is None

    async def test_future_expiry_accepted(self):
        future = datetime.now(UTC) + timedelta(days=30)
        service = ApiKeyService(db=FakeDb(make_record(expires_at=future)))
        assert await service.validate("secret-key") is not None

    async def test_updates_last_used_on_success(self):
        db = FakeDb(make_record())
        service = ApiKeyService(db=db)
        await service.validate("secret-key")

        assert len(db.apikey.updates) == 1
        assert "last_used_at" in db.apikey.updates[0][1]

    async def test_does_not_update_on_failure(self):
        db = FakeDb(make_record())
        service = ApiKeyService(db=db)
        await service.validate("wrong-key")

        assert db.apikey.updates == []


class TestDependency:
    async def test_rejects_invalid_key_with_401(self):
        service = ApiKeyService(db=FakeDb(make_record()))

        with pytest.raises(HTTPException) as exc:
            await require_api_key(x_api_key="wrong", service=service)

        assert exc.value.status_code == 401

    async def test_accepts_valid_key(self):
        service = ApiKeyService(db=FakeDb(make_record()))
        result = await require_api_key(x_api_key="secret-key", service=service)

        assert result.name == "main-service"