"""
Abstract Base Adapter interface for all opportunity scrapers/crawlers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.modules.infrastructure.http.base_http_client import BaseHttpClient

class BaseAdapter(ABC):
    """Unified interface for data source adapters."""

    def __init__(
        self,
        source_id: str,
        source_name: str,
        base_url: str,
        http_client: Optional[BaseHttpClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.source_id = source_id
        self.source_name = source_name
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or BaseHttpClient(base_url=self.base_url)
        self.config = config or {}

    @abstractmethod
    async def fetch(self, limit: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Fetches raw post dictionaries from the target source.
        """
        pass

    @abstractmethod
    def parse(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses raw posts and filters out irrelevant items.
        """
        pass

    async def close(self) -> None:
        """Closes the underlying HTTP client."""
        if self.http_client:
            await self.http_client.close()
