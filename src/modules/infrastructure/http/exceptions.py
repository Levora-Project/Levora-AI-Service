class HttpClientError(Exception):
    """الخطأ الأساسي لكل أخطاء عميل HTTP."""


class HttpTimeoutError(HttpClientError):
    """انتهت مهلة الطلب."""


class HttpConnectionError(HttpClientError):
    """فشل الاتصال بالخادم."""


class HttpResponseError(HttpClientError):
    """استجابة بحالة خطأ من الخادم."""

    def __init__(self, status_code: int, message: str, url: str = "") -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP {status_code} for {url}: {message}")


class HttpRateLimitError(HttpResponseError):
    """تجاوز حد الطلبات (429)."""
