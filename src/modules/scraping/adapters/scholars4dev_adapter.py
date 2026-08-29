"""
Scholars4Dev specific adapter inheriting from WordPressApiAdapter.
Fetches and parses scholarship opportunities from Scholars4Dev.
"""

import logging
from typing import List, Dict, Any, Optional

from src.modules.scraping.adapters.wordpress_api_adapter import WordPressApiAdapter
from src.modules.infrastructure.http.base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class Scholars4DevAdapter(WordPressApiAdapter):
    """Adapter specifically tailored for https://www.scholars4dev.com."""

    def __init__(
        self,
        source_id: str,
        source_name: str = "scholars4dev",
        base_url: str = "https://www.scholars4dev.com",
        api_endpoint: str = "/wp-json/wp/v2/posts",
        http_client: Optional[BaseHttpClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            base_url=base_url,
            api_endpoint=api_endpoint,
            http_client=http_client,
            config=config
        )

    def parse(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parses scholarship posts from Scholars4Dev.

        Scholars4Dev is treated as a scholarship-focused source,
        so every valid post is assigned the 'scholarship' category.
        """

        parsed_opportunities = []

        for post in raw_data:
            if not isinstance(post, dict):
                continue

            title = (
                post.get("title", {}).get("rendered", "")
                if isinstance(post.get("title"), dict)
                else str(post.get("title", ""))
            )

            content = (
                post.get("content", {}).get("rendered", "")
                if isinstance(post.get("content"), dict)
                else str(post.get("content", ""))
            )

            if not title or not content:
                continue

            opportunity = post.copy()

            # Scholars4Dev is a scholarship-focused source
            opportunity["category"] = "scholarship"

            parsed_opportunities.append(opportunity)

        logger.info(
            f"[Scholars4DevAdapter] Parsed "
            f"{len(parsed_opportunities)} / "
            f"{len(raw_data)} valid scholarship opportunities."
        )

        return parsed_opportunities