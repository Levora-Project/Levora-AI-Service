import pytest

from src.modules.scraping.adapters.base_adapter import BaseAdapter


class MockAdapter(BaseAdapter):
    """Simple adapter used only for testing BaseAdapter."""

    async def fetch(self, limit: int = 20, page: int = 1):
        return [
            {
                "id": 1,
                "title": "Test Scholarship",
                "url": "https://example.com/scholarship",
            },
            {
                "id": 2,
                "title": "Test Internship",
                "url": "https://example.com/internship",
            },
        ][:limit]

    def parse(self, raw_data):
        return [
            {
                "title": item["title"],
                "url": item["url"],
            }
            for item in raw_data
        ]


def test_base_adapter_initialization():
    adapter = MockAdapter(
        source_id="test-1",
        source_name="test_source",
        base_url="https://example.com/",
    )

    assert adapter.source_id == "test-1"
    assert adapter.source_name == "test_source"
    assert adapter.base_url == "https://example.com"
    assert adapter.config == {}
    assert adapter.http_client is not None


@pytest.mark.asyncio
async def test_fetch():
    adapter = MockAdapter(
        source_id="test-1",
        source_name="test_source",
        base_url="https://example.com",
    )

    result = await adapter.fetch(limit=2)

    assert len(result) == 2
    assert result[0]["title"] == "Test Scholarship"


def test_parse():
    adapter = MockAdapter(
        source_id="test-1",
        source_name="test_source",
        base_url="https://example.com",
    )

    raw_data = [
        {
            "id": 1,
            "title": "Test Scholarship",
            "url": "https://example.com/scholarship",
        }
    ]

    result = adapter.parse(raw_data)

    assert len(result) == 1
    assert result[0]["title"] == "Test Scholarship"


@pytest.mark.asyncio
async def test_close():
    adapter = MockAdapter(
        source_id="test-1",
        source_name="test_source",
        base_url="https://example.com",
    )

    await adapter.close()
