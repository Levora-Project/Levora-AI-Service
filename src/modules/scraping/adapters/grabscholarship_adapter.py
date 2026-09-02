import logging
import re
from typing import Any

from .wordpress_api_adapter import WordPressApiAdapter

logger = logging.getLogger(__name__)


class GrabScholarshipAdapter(WordPressApiAdapter):
    """محول خاص بموقع GrabScholarships للمنح والتدريب والزمالات."""

    source_name: str = "grabscholarship"
    base_url: str = "https://grabscholarships.com"
    api_endpoint: str = "/wp-json/wp/v2/posts"

    # أنماط استبعاد المقالات العامة وصفحات معلومات الجامعات غير المرتبطة بفرص تقديم
    EXCLUDED_PATTERNS = [
        re.compile(
            r"(?i)\b(a guide to choosing university courses|guide to choosing university courses)\b"
        ),
        re.compile(
            r"(?i)\b(university rankings?|how to choose a? university|study tips|career advice)\b"
        ),
        re.compile(r"(?i)^[A-Za-z\s]+Institute of Technology(?:\s*\([A-Za-z]+\))?$"),
    ]

    # أنماط الكلمات المفتاحية المؤكدة للفرص
    OPPORTUNITY_KEYWORDS_PATTERN = re.compile(
        r"(?i)\b(scholarships?|fellowships?|internships?|traineeships?|studentships?|grants?|funding|funded|fully[ -]funded|partially[ -]funded|exchange program|competition|contest|award|training program)\b"
    )

    def parse(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        """يستخرج معلومات الفرصة مع تمييز النوع والمستوى والتمويل والدولة بدقة تامة."""
        base_parsed = super().parse(raw_item)

        title = base_parsed.get("title", "")
        content = base_parsed.get("content", "")
        categories = base_parsed.get("categories", [])

        opportunity_type = self._determine_opportunity_type(
            title,
            categories,
            content,
        )

        study_levels = self._extract_study_levels(
            title,
            categories,
            content,
        )

        funding_type = self._extract_funding_type(
            title,
            categories,
            content,
        )

        country = self._extract_country(
            title,
            categories,
            content,
        )

        deadline = self._extract_deadline(content)

        return {
            **base_parsed,
            "opportunity_type": opportunity_type,
            "study_levels": study_levels,
            "funding_type": funding_type,
            "country": country,
            "location": country,
            "deadline": deadline,
        }

    def is_opportunity(self, raw_item: dict[str, Any]) -> bool:
        """
        يحدد هل منشور GrabScholarships يمثل فرصة فعلية
        أم مقالاً عاماً / صفحة معلومات عن جامعة أو تخصص.
        """
        parsed = self.parse(raw_item)
        title = str(parsed.get("title", "")).strip()
        content = str(parsed.get("content", "")).strip()
        categories = parsed.get("categories", [])
        category_text = " ".join(str(c) for c in categories).lower()

        # 1. فحص أنماط الاستبعاد المباشرة على العنوان
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern.search(title):
                return False

        # 2. استبعاد تصنيف الجامعات العامة
        if "top universities" in category_text or "university courses" in category_text:
            # إذا لم يكن هناك مؤشر منحة صريح في العنوان فهو مقال تعريفي فقط
            if not re.search(
                r"(?i)\b(scholarships?|fellowships?|internships?|grants?)\b", title
            ):
                return False

        # 3. التأكد من وجود كلمة مفتاحية دالة على الفرصة
        combined = f"{title} {category_text} {content[:2000]}"
        if not self.OPPORTUNITY_KEYWORDS_PATTERN.search(combined):
            return False

        # 4. مؤشرات التقديم والشروط والفوائد
        application_pattern = re.compile(
            r"(?i)\b(apply|application|eligibility|eligible|deadline|how to apply|requirements|benefits|financial support|stipend|tuition|fully funded)\b"
        )
        has_application_info = bool(application_pattern.search(combined))

        has_opp_category = any(
            re.search(
                r"(?i)\b(scholarships?|fellowships?|internships?|funding|grants?)\b",
                str(cat),
            )
            for cat in categories
        )

        return has_application_info or has_opp_category

    def _determine_opportunity_type(
        self,
        title: str,
        categories: list[str],
        content: str = "",
    ) -> str:
        """
        يحدد نوع الفرصة بالاعتماد على الهرمية:
        1. العنوان (له الأولوية القصوى لمنع التصنيف الخاطئ مثل كلمة international)
        2. التصنيفات والوسوم (Categories & Tags)
        3. محتوى المقال (Fallback فقط)
        مع استخدام Word Boundaries دائماً.

        ملاحظة تصميمية:
        تصنيفات مثل MBA/Bachelor/PhD تُستخدم لتحديد study_levels، بينما Internship
        وحده من هذه القائمة يمكن أن يحدد opportunity_type. هذا تصميم مقصود:
        opportunity_type و study_levels حقلان منفصلان.
        """
        cat_str = " ".join(categories)

        # 1. Title matching (Highest Priority)
        title_type = self._match_type_from_text(title)
        if title_type:
            return title_type

        # 2. Category matching
        cat_type = self._match_type_from_text(cat_str)
        if cat_type:
            return cat_type

        # 3. Content body fallback
        content_type = self._match_type_from_text(content[:1000])
        if content_type:
            return content_type

        return "scholarship"

    def _match_type_from_text(self, text: str) -> str | None:
        if not text:
            return None

        # Check Fellowship first
        if re.search(r"(?i)\b(fellowships?|fellow)\b", text):
            return "fellowship"

        # Check Internship with strict word boundaries to never match 'international'
        if re.search(r"(?i)\b(internships?|interns?|traineeships?|trainee)\b", text):
            return "internship"

        # Check Training / Bootcamp
        if re.search(r"(?i)\b(training|bootcamp|workshop)\b", text):
            return "training"

        # Check Exchange program
        if re.search(r"(?i)\b(exchange[ -]?(?:program|programme)?)\b", text):
            return "exchange_program"

        # Check Competition / Contest / Hackathon
        if re.search(r"(?i)\b(competitions?|contests?|hackathons?)\b", text):
            return "competition"

        # Check Grant
        if re.search(r"(?i)\b(grants?|awards?)\b", text):
            return "grant"

        # Check Scholarship / Studentship
        if re.search(r"(?i)\b(scholarships?|studentships?)\b", text):
            return "scholarship"

        return None

    def _extract_study_levels(
        self,
        title: str,
        categories: list[str],
        content: str,
    ) -> list[str]:
        """
        يستخرج المراحل الأكاديمية المستهدفة (Bachelor, Master, PhD, Postdoc, Diploma, High School).

        ملاحظة تصميمية:
        تصنيفات مثل MBA/Bachelor/PhD تُستخدم لتحديد study_levels، بينما Internship
        وحده من هذه القائمة يمكن أن يحدد opportunity_type. هذا تصميم مقصود:
        opportunity_type و study_levels حقلان منفصلان.
        """
        levels: list[str] = []
        combined = f"{title} {' '.join(categories)} {content[:1000]}"

        if re.search(
            r"(?i)\b(bachelor|undergraduate|undergrad|bsc|b\.sc|ba|b\.a)\b", combined
        ):
            levels.append("Bachelor")

        if re.search(
            r"(?i)\b(master|masters|postgraduate|graduate|ms|m\.sc|msc|mba|ma|m\.a)\b",
            combined,
        ):
            levels.append("Master")

        if re.search(r"(?i)\b(phd|ph\.d|doctorate|doctoral)\b", combined):
            levels.append("PhD")

        if re.search(r"(?i)\b(postdoc|postdoctoral)\b", combined):
            levels.append("Postdoc")

        if re.search(r"(?i)\b(diploma|certificate)\b", combined):
            levels.append("Diploma")

        if re.search(r"(?i)\b(high[ -]?school)\b", combined):
            levels.append("High School")

        return levels

    def _extract_funding_type(
        self,
        title: str,
        categories: list[str],
        content: str,
    ) -> str | None:
        combined = f"{title} {' '.join(categories)} {content[:1200]}"

        if re.search(
            r"(?i)\b(fully[ -]?funded|full[ -]?funded|full funding|full scholarship|full tuition|100%[ -]?funded)\b",
            combined,
        ):
            return "fully_funded"

        if re.search(
            r"(?i)\b(partially[ -]?funded|partial funding|partial scholarship|tuition waiver|tuition discount)\b",
            combined,
        ):
            return "partially_funded"

        if re.search(r"(?i)\b(unfunded|self[ -]?funded)\b", combined):
            return "unfunded"

        return None

    def _extract_country(
        self,
        title: str,
        categories: list[str],
        content: str,
    ) -> str | None:
        combined = f"{title} {' '.join(categories)}"

        countries = [
            "USA",
            "United States",
            "United States of America",
            "UK",
            "United Kingdom",
            "Canada",
            "Germany",
            "Australia",
            "Japan",
            "South Korea",
            "China",
            "France",
            "Netherlands",
            "Sweden",
            "Switzerland",
            "Italy",
            "Turkey",
            "Saudi Arabia",
            "UAE",
            "United Arab Emirates",
            "Belgium",
            "Malaysia",
            "Qatar",
            "Mauritius",
            "New Zealand",
            "Singapore",
            "Ireland",
        ]

        for country in countries:
            if re.search(rf"\b{re.escape(country)}\b", combined, re.IGNORECASE):
                return country

        return None

    def _extract_deadline(self, content: str) -> str | None:
        pattern = re.compile(
            r"(?:deadline|application deadline|last date)[:\s]+([^<\n\.,;]+)",
            re.IGNORECASE,
        )
        match = pattern.search(content)
        return match.group(1).strip() if match else None
