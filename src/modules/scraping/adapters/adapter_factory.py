"""
Factory for creating and resolving adapters dynamically based on source name or method.
"""

from typing import Dict, Type, Optional, Any
from src.modules.scraping.adapters.base_adapter import BaseAdapter
from src.modules.scraping.adapters.wordpress_api_adapter import WordPressApiAdapter
from src.modules.scraping.adapters.almin7_adapter import Almin7Adapter
from src.modules.scraping.adapters.grabscholarship_adapter import GrabScholarshipAdapter
from src.modules.scraping.adapters.scholars4dev_adapter import Scholars4DevAdapter
from src.modules.infrastructure.http.base_http_client import BaseHttpClient


class AdapterFactory:
    """Registry and factory for source adapters."""

    _registry: Dict[str, Type[BaseAdapter]] = {
    "almin7": Almin7Adapter,
    "grabscholarship": GrabScholarshipAdapter,
    "scholars4dev": Scholars4DevAdapter,
    "wordpress_api": WordPressApiAdapter
    }

    @classmethod
    def register_adapter(cls, name: str, adapter_cls: Type[BaseAdapter]) -> None:
        """Allows dynamic registration of new custom adapters."""
        cls._registry[name.lower()] = adapter_cls

    @classmethod
    def create_adapter(
        cls,
        source_id: str,
        source_name: str,
        base_url: str,
        api_endpoint: str = "/wp-json/wp/v2/posts",
        method: str = "wordpress_api",
        http_client: Optional[BaseHttpClient] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAdapter:
        """Instantiates the appropriate adapter for the given source."""
        clean_name = source_name.lower().strip()
        
        # 1. Exact name match (e.g. 'almin7', 'grabscholarship')
        if clean_name in cls._registry:
            adapter_cls = cls._registry[clean_name]
            return adapter_cls(
                source_id=source_id,
                source_name=source_name,
                base_url=base_url,
                api_endpoint=api_endpoint,
                http_client=http_client,
                config=config
            )

        # 2. Match by method (e.g. 'wordpress_api')
        clean_method = method.lower().strip()
        if clean_method in cls._registry:
            adapter_cls = cls._registry[clean_method]
            return adapter_cls(
                source_id=source_id,
                source_name=source_name,
                base_url=base_url,
                api_endpoint=api_endpoint,
                http_client=http_client,
                config=config
            )

        # 3. Default fallback
        return WordPressApiAdapter(
            source_id=source_id,
            source_name=source_name,
            base_url=base_url,
            api_endpoint=api_endpoint,
            http_client=http_client,
            config=config
        )
