import logging
import re
from typing import Any

from .wordpress_api_adapter import WordPressApiAdapter

logger = logging.getLogger(__name__)


class Almin7Adapter(WordPressApiAdapter):
    """محول خاص بموقع Almin7 للمنح الدراسية والفرص التعليمية."""

    source_name: str = "almin7"
    base_url: str = "https://almin7.com"
    api_endpoint: str = "/wp-json/wp/v2/posts"

    # أنماط استبعاد المقالات غير المرتبطة بالفرص
    EXCLUDED_PATTERNS = [
        re.compile(
            r"(?i)\b(study tips|career advice|نصائح للدراسة|كيف تختار تخصصك|معلومات عامة|أخبار عامة)\b"
        ),
    ]

    EXCLUDED_CATEGORY_PATTERNS = [
        re.compile(r"(?i)\b(articles|news|tips|advice|مقالات|أخبار|نصائح|إرشادات)\b"),
    ]

    OPPORTUNITY_CATEGORY_PATTERNS = [
        re.compile(
            r"(?i)\b(scholarships?|fellowships?|internships?|grants?|training|volunteering|منح|منحة|زمالة|تدريب|تطوع|فرص)\b"
        ),
    ]

    def parse(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        """يستخرج تفاصيل الفرصة الخاصة بموقع Almin7 مع تصفية التصنيفات واستخراج الحقول."""
        base_parsed = super().parse(raw_item)
        content = base_parsed.get("content", "")
        title = base_parsed.get("title", "")
        categories = base_parsed.get("categories", [])

        # Determine opportunity type with hierarchy (Title -> Categories -> Content)
        opportunity_type = self._determine_opportunity_type(title, categories, content)

        # Extract study levels from title and categories
        study_levels = self._extract_study_levels(title, categories, content)

        # Extract country/location
        country = self._extract_country(title, categories, content)

        # Extract funding type
        funding_type = self._extract_funding_type(title, content)

        # Extract deadline if mentioned in structured format or patterns
        deadline_text = self._extract_deadline_text(content)

        return {
            **base_parsed,
            "opportunity_type": opportunity_type,
            "study_levels": study_levels,
            "country": country,
            "location": country,
            "funding_type": funding_type,
            "deadline": deadline_text,
        }

    def is_opportunity(self, raw_item: dict[str, Any]) -> bool:
        """
        يحدد هل المقال يمثل فرصة حقيقية أم مقالاً عاماً بالاعتماد على التصنيفات كإشارة أساسية.
        """
        parsed = self.parse(raw_item)
        categories = parsed.get("categories", [])
        cat_str = " ".join(str(c) for c in categories)

        # 1. إذا كانت التصنيفات صريحة بالمقالات العامة/الأخبار وبدون تصنيف منحة
        if cat_str:
            has_excluded_cat = any(
                p.search(cat_str) for p in self.EXCLUDED_CATEGORY_PATTERNS
            )
            has_opp_cat = any(
                p.search(cat_str) for p in self.OPPORTUNITY_CATEGORY_PATTERNS
            )
            if has_excluded_cat and not has_opp_cat:
                return False
            if has_opp_cat:
                return True

        # 2. فحص العنوان وأنماط الاستبعاد كـ Fallback
        title = str(parsed.get("title", "")).strip()
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern.search(title):
                return False

        return True

    def _determine_opportunity_type(
        self, title: str, categories: list[str], content: str
    ) -> str:
        """يحدد نوع الفرصة باعتماد أولوية العنوان ثم التصنيفات ثم المحتوى باستخدام Word Boundaries."""
        cat_str = " ".join(categories)

        # 1. Check Title First (Highest Priority)
        title_type = self._match_type_pattern(title)
        if title_type:
            return title_type

        # 2. Check Categories
        cat_type = self._match_type_pattern(cat_str)
        if cat_type:
            return cat_type

        # 3. Check Content Body
        content_type = self._match_type_pattern(content[:1000])
        if content_type:
            return content_type

        return "scholarship"

    def _match_type_pattern(self, text: str) -> str | None:
        if not text:
            return None

        # Check fellowship
        if re.search(r"(?i)\b(fellowship|fellowships|fellow|زمالة|زمالات)\b", text):
            return "fellowship"

        # Check internship (word boundary prevents matching 'international')
        if re.search(
            r"(?i)\b(internship|internships|intern|interns|تدريب[ -]?عملي|تدريب[ -]?صيفي|فرصة[ -]?تدريب)\b",
            text,
        ):
            return "internship"

        # Check training / bootcamp / workshop
        if re.search(
            r"(?i)\b(training|trainee|traineeship|bootcamp|workshop|دورة[ -]?تدريبية|برنامج[ -]?تدريبي|معسكر)\b",
            text,
        ):
            return "training"

        # Check volunteering
        if re.search(
            r"(?i)\b(volunteering|volunteer|تطوع|عمل[ -]?تطوعي|فرصة[ -]?تطوع)\b", text
        ):
            return "volunteering"

        # Check exchange program
        if re.search(
            r"(?i)\b(exchange[ -]?(?:program|programme)?|تبادل[ -]?(?:طلابي|ثقافي)?)\b",
            text,
        ):
            return "exchange_program"

        # Check competition
        if re.search(r"(?i)\b(competition|contest|hackathon|مسابقة|هاكاثون)\b", text):
            return "competition"

        # Check grant / research award
        if re.search(r"(?i)\b(grant|grants|منحة[ -]?بحثية|دعم[ -]?مالي)\b", text):
            return "grant"

        # Check scholarship
        if re.search(
            r"(?i)\b(scholarship|scholarships|منحة[ -]?دراسية|منح[ -]?دراسية|منحة|منح)\b",
            text,
        ):
            return "scholarship"

        return None

    def _extract_study_levels(
        self, title: str, categories: list[str], content: str
    ) -> list[str]:
        levels: list[str] = []
        combined = f"{title} {' '.join(categories)} {content[:500]}".lower()

        if any(
            w in combined for w in ["بكالوريوس", "bachelor", "undergraduate", "جامعي"]
        ):
            levels.append("Bachelor")
        if any(w in combined for w in ["ماجستير", "master", "postgraduate", "msc"]):
            levels.append("Master")
        if any(w in combined for w in ["دكتوراه", "phd", "doctorate"]):
            levels.append("PhD")
        if any(w in combined for w in ["ثانوية", "high school"]):
            levels.append("High School")
        if any(w in combined for w in ["دبلوم", "diploma"]):
            levels.append("Diploma")

        return levels

    def _extract_country(
        self, title: str, categories: list[str], content: str
    ) -> str | None:
        combined = f"{title} {' '.join(categories)} {content[:600]}"
        country_regexes = [
            (
                r"(?:في|دولة|منحة)\s+(تركيا|ألمانيا|بريطانيا|كندا|أمريكا|فرنسا|إيطاليا|اليابان|الصين|أستراليا|السعودية|قطر|الإمارات)",
                1,
            ),
            (
                r"(?:in|to)\s+(Turkey|Germany|UK|Canada|USA|France|Italy|Japan|China|Australia)",
                1,
            ),
        ]
        for pattern, group_idx in country_regexes:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(group_idx)

        return None

    def _extract_funding_type(self, title: str, content: str) -> str | None:
        combined = f"{title} {content[:800]}".lower()
        if any(
            w in combined
            for w in [
                "ممول بالكامل",
                "تمويل كامل",
                "fully funded",
                "full scholarship",
                "100% funded",
            ]
        ):
            return "fully_funded"
        if any(
            w in combined
            for w in ["ممول جزئيا", "تمويل جزئي", "partially funded", "تخفيض"]
        ):
            return "partially_funded"
        if any(w in combined for w in ["غير ممول", "تمويل ذاتي", "unfunded"]):
            return "unfunded"
        return None

    def _extract_deadline_text(self, content: str) -> str | None:
        patterns = [
            r"(?:آخر موعد للتقديم|اخر موعد|الموعد النهائي)[:\s]+([^<\n\.,;]+)",
            r"(?:deadline|application deadline)[:\s]+([^<\n\.,;]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
