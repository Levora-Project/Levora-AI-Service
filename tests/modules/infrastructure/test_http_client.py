import httpx
import pytest

from src.modules.infrastructure.http.base_http_client import BaseHttpClient
from src.modules.infrastructure.http.exceptions import (
    HttpConnectionError,
    HttpRateLimitError,
    HttpResponseError,
    HttpTimeoutError,
)
from src.modules.infrastructure.http.retry_strategy import RetryStrategy


def make_client(handler, **kwargs) -> BaseHttpClient:
    """ينشئ عميلاً يستخدم MockTransport بدل شبكة حقيقية."""
    transport = httpx.MockTransport(handler)
    return BaseHttpClient(
        client=httpx.AsyncClient(base_url="https://test.local", transport=transport),
        retry_strategy=RetryStrategy(max_attempts=3, base_delay=0.0, max_delay=0.0),
        **kwargs,
    )


class TestSuccess:
    async def test_get_returns_response(self):
        client = make_client(lambda req: httpx.Response(200, json={"ok": True}))
        response = await client.get("/posts")
        assert response.status_code == 200
        await client.close()

    async def test_get_json_parses_body(self):
        client = make_client(lambda req: httpx.Response(200, json={"id": 7}))
        data = await client.get_json("/posts/7")
        assert data == {"id": 7}
        await client.close()

    async def test_works_as_context_manager(self):
        async with make_client(lambda req: httpx.Response(200, text="hi")) as client:
            response = await client.get("/")
            assert response.text == "hi"


class TestFailure:
    async def test_404_raises_without_retry(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(404, text="not found")

        client = make_client(handler)
        with pytest.raises(HttpResponseError) as exc:
            await client.get("/missing")

        assert exc.value.status_code == 404
        assert len(calls) == 1
        await client.close()

    async def test_429_raises_rate_limit_error(self):
        client = make_client(lambda req: httpx.Response(429, text="slow down"))
        with pytest.raises(HttpRateLimitError):
            await client.get("/limited")
        await client.close()

    async def test_timeout_raises_timeout_error(self):
        def handler(request):
            raise httpx.ConnectTimeout("timed out", request=request)

        client = make_client(handler)
        with pytest.raises(HttpTimeoutError):
            await client.get("/slow")
        await client.close()

    async def test_connection_error_raises(self):
        def handler(request):
            raise httpx.ConnectError("refused", request=request)

        client = make_client(handler)
        with pytest.raises(HttpConnectionError):
            await client.get("/down")
        await client.close()


class TestRetry:
    async def test_recovers_after_transient_failure(self):
        calls = []

        def handler(request):
            calls.append(request)
            if len(calls) < 3:
                return httpx.Response(503, text="unavailable")
            return httpx.Response(200, json={"recovered": True})

        client = make_client(handler)
        response = await client.get("/flaky")

        assert response.json() == {"recovered": True}
        assert len(calls) == 3
        await client.close()

    async def test_gives_up_after_max_attempts(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(500, text="boom")

        client = make_client(handler)
        with pytest.raises(HttpResponseError):
            await client.get("/broken")

        assert len(calls) == 3
        await client.close()


class TestRetryStrategy:
    def test_stops_at_max_attempts(self):
        strategy = RetryStrategy(max_attempts=3)
        assert strategy.should_retry(2, 500) is True
        assert strategy.should_retry(3, 500) is False

    def test_network_errors_always_retryable(self):
        assert RetryStrategy().should_retry(1, None) is True

    def test_client_errors_not_retryable(self):
        strategy = RetryStrategy()
        assert strategy.should_retry(1, 404) is False
        assert strategy.should_retry(1, 400) is False

    def test_delay_grows_and_is_capped(self):
        strategy = RetryStrategy(base_delay=1.0, max_delay=4.0)
        assert strategy.compute_delay(1) <= 1.0
        assert strategy.compute_delay(10) <= 4.0
