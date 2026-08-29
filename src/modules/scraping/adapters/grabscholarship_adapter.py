"""
GrabScholarship specific adapter inheriting from WordPressApiAdapter.
Extracts degrees (Bachelor, Master, PhD, MBA, Internships) and scholarships from https://grabscholarship.com.
"""

import logging
from typing import List, Dict, Any, Optional
from src.modules.scraping.adapters.wordpress_api_adapter import WordPressApiAdapter
from src.modules.infrastructure.http.base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class GrabScholarshipAdapter(WordPressApiAdapter):
    """Adapter specifically tailored for https://grabscholarship.com."""

    def __init__(
        self,
        source_id: str,
        source_name: str = "grabscholarship",
        base_url: str = "https://grabscholarship.com",
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
        Parses posts from GrabScholarship, checking for educational opportunities.
        """
        parsed_opportunities = []

        category_keywords = {
            "scholarship": [
                "منحة",
                "منح",
                "منحة دراسية",
                "scholarship",
                "scholarships"
            ],
            "internship": [
                "تدريب",
                "تدريب عملي",
                "internship",
                "internships"
            ],
            "fellowship": [
                "زمالة",
                "زمالات",
                "fellowship",
                "fellowships"
            ],
            "volunteering": [
                "تطوع",
                "فرصة تطوع",
                "volunteer",
                "volunteering"
            ]
        }

        for post in raw_data:
            if not isinstance(post, dict):
                continue

            title = post.get("title", {}).get("rendered", "") if isinstance(post.get("title"), dict) else str(post.get("title", ""))
            content = post.get("content", {}).get("rendered", "") if isinstance(post.get("content"), dict) else str(post.get("content", ""))

            if not title or not content:
                continue

            # Check if relevant opportunity
            combined = f"{title} {content}".lower()
            category = None

            for category_name, keywords in category_keywords.items():
                if any(keyword.lower() in combined for keyword in keywords):
                    category = category_name
                    break

            if category is None:
                continue

            opportunity = post.copy()
            opportunity["category"] = category
            parsed_opportunities.append(opportunity)

        
        logger.info(
            f"[GrabScholarshipAdapter] Parsed "
            f"{len(parsed_opportunities)} / {len(raw_data)} valid opportunities."
        )

        return parsed_opportunities