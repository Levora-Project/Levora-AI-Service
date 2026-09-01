import html
import re

# Regex patterns for cleaning
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
SCRIPT_STYLE_PATTERN = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
MULTIPLE_WHITESPACE = re.compile(r"[ \t]+")
MULTIPLE_NEWLINES = re.compile(r"\n\s*\n+")
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def clean_html(raw_html: str | None) -> str:
    """يزيل وسوم HTML ويحوّل النصوص إلى نص مقروء ونظيف."""
    if not raw_html:
        return ""

    if not isinstance(raw_html, str):
        raw_html = str(raw_html)

    # 1. Remove script and style elements
    text = SCRIPT_STYLE_PATTERN.sub("", raw_html)

    # 2. Replace paragraph and break tags with newlines
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</?(p|div|li|h[1-6]|tr)[^>]*>", "\n", text)

    # 3. Strip all remaining HTML tags
    text = HTML_TAG_PATTERN.sub(" ", text)

    # 4. Unescape HTML entities (&amp;, &nbsp;, &#8217;, etc.)
    text = html.unescape(text)

    # 5. Clean zero-width and unusual unicode spaces
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")

    # 6. Normalize newlines and spaces
    lines = [MULTIPLE_WHITESPACE.sub(" ", line).strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)

    return MULTIPLE_NEWLINES.sub("\n\n", cleaned).strip()


def clean_text(text: str | None) -> str:
    """ينظف النص البسيط من المسافات الزائدة والمحارف الخاصة."""
    if not text:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # Unescape HTML entities if any
    text = html.unescape(text)
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")

    # Replace multiple spaces with a single space
    text = MULTIPLE_WHITESPACE.sub(" ", text)
    return text.strip()


def extract_urls(text: str | None) -> list[str]:
    """يستخرج جميع الروابط من النص."""
    if not text:
        return []
    return URL_PATTERN.findall(text)


def extract_first_url(text: str | None) -> str | None:
    """يستخرج أول رابط صالح من النص."""
    urls = extract_urls(text)
    return urls[0] if urls else None


def extract_emails(text: str | None) -> list[str]:
    """يستخرج البريد الإلكتروني من النص."""
    if not text:
        return []
    return EMAIL_PATTERN.findall(text)
