"""
Generic WordPress REST API Adapter for sources that expose `/wp-json/wp/v2/posts`.
"""

import logging
from typing import List, Dict, Any, Optional
from src.modules.scraping.adapters.base_adapter import BaseAdapter
from src.modules.infrastructure.http.base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class WordPressApiAdapter(BaseAdapter):
    """Base WordPress REST API Adapter with pagination and category support."""

    DEFAULT_ENDPOINT = "/wp-json/wp/v2/posts"

    def __init__(
        self,
        source_id: str,
        source_name: str,
        base_url: str,
        api_endpoint: Optional[str] = None,
        http_client: Optional[BaseHttpClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            base_url=base_url,
            http_client=http_client,
            config=config
        )
        self.api_endpoint = api_endpoint or self.DEFAULT_ENDPOINT

    async def fetch(self, limit: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Queries WordPress REST API `/wp-json/wp/v2/posts` with pagination.
        """
        params = {
            "per_page": min(limit, 100),
            "page": page,
            "_embed": "true"
        }

        # If categories are configured in pagination_config or custom parameters
        if "categories" in self.config:
            params["categories"] = self.config["categories"]

        url = f"{self.base_url}{self.api_endpoint}"
        logger.info(f"[{self.source_name}] Fetching posts from {url} with params {params}")

        try:
            response = await self.http_client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            logger.warning(f"[{self.source_name}] Unexpected response status {response.status_code}")
            return []
        except Exception as exc:
            logger.error(f"[{self.source_name}] Error fetching WP posts: {exc}")
            raise exc

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Default parse preserves published posts with content and titles.
        """
        valid_items = []
        for post in raw_data:
            if not isinstance(post, dict):
                continue
            title = post.get("title", {}).get("rendered", "") if isinstance(post.get("title"), dict) else str(post.get("title", ""))
            content = post.get("content", {}).get("rendered", "") if isinstance(post.get("content"), dict) else str(post.get("content", ""))
            
            if title and content:
                valid_items.append(post)

        return valid_items
