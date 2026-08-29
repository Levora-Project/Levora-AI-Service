"""
Almin7 specific adapter inheriting from WordPressApiAdapter.
Filters out non-opportunity articles and extracts scholarship metadata.
"""

import logging 
from typing import List, Dict, Any, Optional
from src.modules.scraping.adapters.wordpress_api_adapter import WordPressApiAdapter
from src.modules.infrastructure.http.base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class Almin7Adapter(WordPressApiAdapter):
    """Adapter specifically tailored for https://almin7.com."""

    def __init__(
        self,
        source_id: str,
        source_name: str = "almin7",
        base_url: str = "https://almin7.com",
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

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses and filters posts from Almin7.
        Returns normalized opportunity objects.
        """

        parsed_opportunities = []

        category_keywords = {
            "scholarship": [
                "منحة",
                "منح",
                "منحة دراسية",
                "scholarship",
                "scholarships",
            ],
            "internship": [
                "تدريب",
                "تدريب عملي",
                "internship",
                "internships",
            ],
            "fellowship": [
                "زمالة",
                "زمالات",
                "fellowship",
                "fellowships",
            ],
            "volunteering": [
                "تطوع",
                "فرصة تطوع",
                "متطوع",
                "volunteer",
                "volunteering",
            ],
        }

        for post in raw_data:
            if not isinstance(post, dict):
                continue

            title = self._extract_rendered(post.get("title"))
            content = self._extract_rendered(post.get("content"))

            if not title and not content:
                continue

            combined = f"{title} {content}".lower()

            category = None

            for category_name, keywords in category_keywords.items():
                if any(keyword.lower() in combined for keyword in keywords):
                    category = category_name
                    break

            if category is None:
                continue

            parsed_opportunities.append(self._normalize_post(post, category=category))

        logger.info(
            f"[Almin7Adapter] Parsed "
            f"{len(parsed_opportunities)} / {len(raw_data)} valid opportunities."
        )

        return parsed_opportunities