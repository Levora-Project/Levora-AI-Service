
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.modules.scraping.adapters.wordpress_api_adapter import (
    WordPressApiAdapter,
    WordPressApiFetchError,
)


class MockResponse:
    """Mock HTTP response used for testing."""

    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data if data is not None else []

    def json(self):
        return self._data


@pytest.fixture
def mock_http_client():
    """Create a mocked HTTP client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def adapter(mock_http_client):
    """Create a WordPressApiAdapter for testing."""
    return WordPressApiAdapter(
        source_id="00000000-0000-0000-0000-000000000001",
        source_name="test_wordpress",
        base_url="https://example.com/",
        http_client=mock_http_client,
    )


def test_initialization(mock_http_client):
    """Test WordPressApiAdapter initialization."""

    adapter = WordPressApiAdapter(
        source_id="00000000-0000-0000-0000-000000000001",
        source_name="test_wordpress",
        base_url="https://example.com/",
        http_client=mock_http_client,
    )

    assert adapter.source_id == "00000000-0000-0000-0000-000000000001"
    assert adapter.source_name == "test_wordpress"
    assert adapter.base_url == "https://example.com"
    assert adapter.api_endpoint == "/wp-json/wp/v2/posts"
    assert adapter.config == {}
    assert adapter.http_client is mock_http_client


@pytest.mark.asyncio
async def test_fetch_success(mock_http_client, adapter):
    """Test successful WordPress API fetch."""

    posts = [
        {
            "id": 1,
            "title": {"rendered": "Test Scholarship"},
            "content": {"rendered": "Scholarship content"},
            "link": "https://example.com/test-scholarship",
        }
    ]

    mock_http_client.get.return_value = MockResponse(
        status_code=200,
        data=posts,
    )

    result = await adapter.fetch(limit=20, page=1)

    assert result == posts

    mock_http_client.get.assert_awaited_once()

    call_args = mock_http_client.get.call_args

    assert call_args.kwargs["params"]["per_page"] == 20
    assert call_args.kwargs["params"]["page"] == 1
    assert call_args.kwargs["params"]["_embed"] == "true"


@pytest.mark.asyncio
async def test_fetch_limit_is_capped_at_100(mock_http_client, adapter):
    """Test that per_page never exceeds 100."""

    mock_http_client.get.return_value = MockResponse(
        status_code=200,
        data=[],
    )

    await adapter.fetch(limit=200, page=1)

    call_args = mock_http_client.get.call_args

    assert call_args.kwargs["params"]["per_page"] == 100


@pytest.mark.asyncio
async def test_fetch_with_categories_list(mock_http_client):
    """Test category filtering with multiple category IDs."""

    adapter = WordPressApiAdapter(
        source_id="00000000-0000-0000-0000-000000000001",
        source_name="test_wordpress",
        base_url="https://example.com",
        http_client=mock_http_client,
        config={"categories": [989, 990, 991]},
    )

    mock_http_client.get.return_value = MockResponse(
        status_code=200,
        data=[],
    )

    await adapter.fetch(limit=10, page=2)

    call_args = mock_http_client.get.call_args
    params = call_args.kwargs["params"]

    assert params["categories"] == "989,990,991"
    assert params["per_page"] == 10
    assert params["page"] == 2


@pytest.mark.asyncio
async def test_fetch_with_single_category(mock_http_client):
    """Test category filtering with a single category."""

    adapter = WordPressApiAdapter(
        source_id="00000000-0000-0000-0000-000000000001",
        source_name="test_wordpress",
        base_url="https://example.com",
        http_client=mock_http_client,
        config={"categories": 989},
    )

    mock_http_client.get.return_value = MockResponse(
        status_code=200,
        data=[],
    )

    await adapter.fetch()

    params = mock_http_client.get.call_args.kwargs["params"]

    assert params["categories"] == 989


@pytest.mark.asyncio
async def test_fetch_non_200_raises_error(mock_http_client, adapter):
    """Test that non-200 responses raise WordPressApiFetchError."""

    mock_http_client.get.return_value = MockResponse(
        status_code=500,
        data={"error": "Internal Server Error"},
    )

    with pytest.raises(WordPressApiFetchError):
        await adapter.fetch()


@pytest.mark.asyncio
async def test_fetch_non_list_response_returns_empty_list(
    mock_http_client,
    adapter,
):
    """Test that a valid response containing non-list JSON returns []."""

    mock_http_client.get.return_value = MockResponse(
        status_code=200,
        data={"message": "Not a list"},
    )

    result = await adapter.fetch()

    assert result == []


def test_extract_rendered_from_dict():
    """Test extracting rendered text from a WordPress field."""

    result = WordPressApiAdapter._extract_rendered(
        {"rendered": "Test Title"}
    )

    assert result == "Test Title"


def test_extract_rendered_from_string():
    """Test extracting rendered text from a string."""

    result = WordPressApiAdapter._extract_rendered("Test Title")

    assert result == "Test Title"


def test_extract_rendered_from_empty_value():
    """Test extracting rendered text from an empty value."""

    assert WordPressApiAdapter._extract_rendered(None) == ""
    assert WordPressApiAdapter._extract_rendered("") == ""


def test_normalize_post(adapter):
    """Test WordPress post normalization."""

    post = {
        "id": 123,
        "title": {"rendered": "Test Scholarship"},
        "content": {"rendered": "Scholarship content"},
        "excerpt": {"rendered": "Short description"},
        "link": "https://example.com/scholarship",
        "slug": "test-scholarship",
        "date": "2026-09-01T10:00:00",
        "modified": "2026-09-01T11:00:00",
        "categories": [989],
        "tags": [10, 20],
    }

    result = adapter._normalize_post(
        post,
        category="scholarship",
    )

    assert result["source_id"] == adapter.source_id
    assert result["source_name"] == adapter.source_name
    assert result["category"] == "scholarship"
    assert result["raw_post_id"] == 123
    assert result["title_raw"] == "Test Scholarship"
    assert result["content_raw"] == "Scholarship content"
    assert result["excerpt_raw"] == "Short description"
    assert result["link"] == "https://example.com/scholarship"
    assert result["slug"] == "test-scholarship"
    assert result["published_at"] == "2026-09-01T10:00:00"
    assert result["modified_at"] == "2026-09-01T11:00:00"
    assert result["wp_categories"] == [989]
    assert result["wp_tags"] == [10, 20]
    assert result["raw_json"] == post
    assert "fetched_at" in result


def test_parse_valid_posts(adapter):
    """Test parsing valid WordPress posts."""

    raw_data = [
        {
            "id": 1,
            "title": {"rendered": "Test Scholarship"},
            "content": {"rendered": "This is scholarship content."},
            "link": "https://example.com/scholarship",
        },
        {
            "id": 2,
            "title": {"rendered": "Test Internship"},
            "content": {"rendered": "This is internship content."},
            "link": "https://example.com/internship",
        },
    ]

    result = adapter.parse(raw_data)

    assert len(result) == 2

    assert result[0].raw_payload["raw_post_id"] == 1
    assert result[0].raw_payload["title_raw"] == "Test Scholarship"

    assert result[1].raw_payload["raw_post_id"] == 2
    assert result[1].raw_payload["title_raw"] == "Test Internship"


def test_parse_skips_missing_title(adapter):
    """Test that posts without a title are ignored."""

    raw_data = [
        {
            "id": 1,
            "title": {"rendered": ""},
            "content": {"rendered": "Some content"},
            "link": "https://example.com/test",
        }
    ]

    result = adapter.parse(raw_data)

    assert result == []


def test_parse_skips_missing_content(adapter):
    """Test that posts without content are ignored."""

    raw_data = [
        {
            "id": 1,
            "title": {"rendered": "Test Scholarship"},
            "content": {"rendered": ""},
            "link": "https://example.com/test",
        }
    ]

    result = adapter.parse(raw_data)

    assert result == []


def test_parse_skips_non_dict_items(adapter):
    """Test that non-dictionary items are ignored."""

    raw_data = [
        "invalid item",
        None,
        123,
        {
            "id": 1,
            "title": {"rendered": "Valid Post"},
            "content": {"rendered": "Valid Content"},
            "link": "https://example.com/valid",
        },
    ]

    result = adapter.parse(raw_data)

    assert len(result) == 1
    assert result[0].raw_payload["title_raw"] == "Valid Post"


@pytest.mark.asyncio
async def test_close(mock_http_client, adapter):
    """Test closing the HTTP client."""

    await adapter.close()

    mock_http_client.close.assert_awaited_once()
