import logging
import re
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# Arabic month names mapping
ARABIC_MONTHS = {
    "يناير": "January",
    "فبراير": "February",
    "مارس": "March",
    "أبريل": "April",
    "ابريل": "April",
    "مايو": "May",
    "يونيو": "June",
    "يوليو": "July",
    "أغسطس": "August",
    "اغسطس": "August",
    "سبتمبر": "September",
    "أكتوبر": "October",
    "اكتوبر": "October",
    "نوفمبر": "November",
    "ديسمبر": "December",
}

# Explicit regex patterns to locate deadline section in text
DEADLINE_PATTERNS = [
    re.compile(
        r"(?:deadline|application deadline|the deadline is|due date|closes on|close on|closing date|closes|applications close on|last date to apply|last date)[:\s]+([^\n\.,;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:آخر موعد للتقديم|آخر موعد|اخر موعد للتسجيل|الموعد النهائي|تاريخ انتهاء التقديم|تاريخ الإغلاق)[:\s]+([^\n\.,;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:before|by)[:\s]+([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z\u0600-\u06FF]+\s+[0-9]{4})",
        re.IGNORECASE,
    ),
]

COMMON_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%b %d %Y",
]

MONTH_NAMES_PATTERN = re.compile(
    r"(?i)\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)\b"
)

YEAR_PATTERN = re.compile(r"\b(202[4-9]|203[0-9])\b")
NUMERIC_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
)
ISO_DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def _normalize_arabic_dates(text: str) -> str:
    """يستبدل أسماء الأشهر العربية بالإنجليزية لتحليلها بسهولة."""
    normalized = text
    for ar, en in ARABIC_MONTHS.items():
        normalized = re.sub(rf"\b{ar}\b", en, normalized)
    return normalized


def _has_sufficient_date_evidence(text: str) -> bool:
    """يتحقق من أن النص يحتوي على مؤشرات كافية لتاريخ حقيقي (سنة + شهر أو صيغة رقمية كاملة)."""
    # Check ISO datetime (e.g. 2026-10-15T12:00:00Z)
    if ISO_DATETIME_PATTERN.search(text):
        return True

    # Check numeric date (e.g. 15/09/2026 or 2026-07-31)
    if NUMERIC_DATE_PATTERN.search(text):
        return True

    # Check month name + year (e.g. 31 July 2026 or September 14, 2026)
    if MONTH_NAMES_PATTERN.search(text) and (
        YEAR_PATTERN.search(text) or re.search(r"\b\d{1,2}\b", text)
    ):
        return True

    return False


def parse_date(date_str: str | None) -> datetime | None:
    """
    يحول النص الذي يحتوي على تاريخ إلى كائن datetime موحد بتوقيت UTC.
    يرجع None بدقة إذا كان النص مجرد عبارات غير مؤكدة أو أجزاء مقتطعة.
    """
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return (
            date_str.astimezone(UTC)
            if date_str.tzinfo
            else date_str.replace(tzinfo=UTC)
        )

    cleaned = str(date_str).strip()
    if not cleaned:
        return None

    # Strip prefix words like 'on', 'the', 'by', etc.
    cleaned = re.sub(
        r"^(?:on|the|by|in|at)\s+", "", cleaned, flags=re.IGNORECASE
    ).strip()

    # Verify that the text contains sufficient date structure (avoids 'of 27', 'had passed')
    if not _has_sufficient_date_evidence(cleaned):
        return None

    norm = _normalize_arabic_dates(cleaned)
    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
    norm = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", norm)
    norm = re.sub(r"\s+", " ", norm).strip()

    # 1. Try explicit COMMON_DATE_FORMATS
    for fmt in COMMON_DATE_FORMATS:
        try:
            dt = datetime.strptime(norm, fmt)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue

    # 2. Try ISO format
    try:
        dt = datetime.fromisoformat(norm.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        pass

    # 3. Try dateparser with strict settings
    try:
        import dateparser  # noqa: PLC0415

        dt = dateparser.parse(
            norm,
            settings={
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": "UTC",
                "REQUIRE_PARTS": ["day", "month"],
            },
        )
        if dt is not None and 2024 <= dt.year <= 2040:
            return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        pass

    return None


def extract_deadline_from_text(text: str | None) -> datetime | None:
    """يبحث في النص عن مؤشرات الموعد النهائي ويستخرج تاريخ صالح."""
    if not text:
        return None

    # Try explicit patterns first
    for pattern in DEADLINE_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            parsed = parse_date(candidate)
            if parsed:
                return parsed

            # Try extracting full date pattern within candidate (e.g. "25 November 2026 for all students")
            date_match = re.search(
                r"\b(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z\u0600-\u06FF]+\s+\d{4})\b",
                candidate,
            )
            if date_match:
                parsed = parse_date(date_match.group(1))
                if parsed:
                    return parsed

            # Try month day, year (e.g. September 14, 2026)
            date_match2 = re.search(
                r"\b([A-Za-z\u0600-\u06FF]+\s+\d{1,2},?\s+\d{4})\b", candidate
            )
            if date_match2:
                parsed = parse_date(date_match2.group(1))
                if parsed:
                    return parsed

            iso_match = re.search(
                r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
                candidate,
            )
            if iso_match:
                parsed = parse_date(iso_match.group(1))
                if parsed:
                    return parsed

    return None
