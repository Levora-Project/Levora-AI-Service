import pytest

from src.modules.scraping.adapters.adapter_factory import AdapterFactory
from src.modules.scraping.adapters.almin7_adapter import Almin7Adapter
from src.modules.scraping.adapters.base_adapter import BaseAdapter
from src.modules.scraping.adapters.grabscholarship_adapter import GrabScholarshipAdapter
from src.modules.scraping.adapters.scholars4dev_adapter import Scholars4DevAdapter
from src.modules.scraping.adapters.wordpress_api_adapter import WordPressApiAdapter


def test_adapter_factory_known_sources():
    assert isinstance(AdapterFactory.get_adapter("almin7"), Almin7Adapter)
    assert isinstance(
        AdapterFactory.get_adapter("grabscholarship"), GrabScholarshipAdapter
    )
    assert isinstance(AdapterFactory.get_adapter("scholars4dev"), Scholars4DevAdapter)
    assert isinstance(AdapterFactory.get_adapter("wordpress_api"), WordPressApiAdapter)


def test_adapter_factory_aliases():
    assert isinstance(
        AdapterFactory.get_adapter("grabscholarships"), GrabScholarshipAdapter
    )
    assert isinstance(AdapterFactory.get_adapter("wp_api"), WordPressApiAdapter)
    assert isinstance(AdapterFactory.get_adapter("wordpress"), WordPressApiAdapter)


def test_adapter_factory_by_method():
    adapter = AdapterFactory.get_adapter(
        "custom_source", source_config={"method": "wordpress_api"}
    )
    assert isinstance(adapter, WordPressApiAdapter)


def test_adapter_factory_fallback():
    # Unknown source falls back to WordPressApiAdapter by default with warning
    adapter = AdapterFactory.get_adapter("completely_unknown_source")
    assert isinstance(adapter, WordPressApiAdapter)


def test_adapter_factory_unsupported_method_without_fallback():
    with pytest.raises(ValueError, match="Unsupported adapter"):
        AdapterFactory.get_adapter(
            "unknown_source",
            source_config={"method": "unsupported_graphql_method"},
            allow_fallback=False,
        )


def test_adapter_factory_custom_registration():
    class CustomNewAdapter(BaseAdapter):
        async def fetch(self, limit: int = 20, page: int = 1):
            return []

        def parse(self, raw_item):
            return {}

    AdapterFactory.register("custom_new", CustomNewAdapter)
    adapter = AdapterFactory.get_adapter("custom_new")
    assert isinstance(adapter, CustomNewAdapter)


def test_adapter_factory_list_supported_sources():
    sources = AdapterFactory.list_supported_sources()
    assert "almin7" in sources
    assert "grabscholarship" in sources
    assert "scholars4dev" in sources
    assert "wordpress_api" in sources
