import httpx

from src.modules.infrastructure.http.base_http_client import BaseHttpClient
from src.modules.infrastructure.http.retry_strategy import RetryStrategy
from src.modules.infrastructure.webhook.webhook_client import (
    ScrapeCompletePayload,
    WebhookClient,
)

WEBHOOK_URL = "https://main.local/api/webhooks/scrape-complete"


def make_webhook_client(handler, secret: str = "") -> WebhookClient:
    http = BaseHttpClient(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        retry_strategy=RetryStrategy(max_attempts=3, base_delay=0.0, max_delay=0.0),
    )
    return WebhookClient(webhook_url=WEBHOOK_URL, secret=secret, http_client=http)


def make_payload(**overrides) -> ScrapeCompletePayload:
    data = {"batch_id": "batch-123", "total_opportunities": 42}
    return ScrapeCompletePayload(**{**data, **overrides})


class TestPayload:
    def test_defaults_are_applied(self):
        payload = make_payload()
        assert payload.succeeded_sources == []
        assert payload.failed_sources == []
        assert payload.completed_at is not None

    def test_serializes_to_json(self):
        payload = make_payload(succeeded_sources=["almin7"])
        data = payload.model_dump_json()
        assert "batch-123" in data
        assert "almin7" in data


class TestDelivery:
    async def test_successful_notification_returns_true(self):
        client = make_webhook_client(lambda req: httpx.Response(200, json={"ok": True}))
        assert await client.notify_scrape_complete(make_payload()) is True
        await client.close()

    async def test_sends_payload_as_json_body(self):
        captured = {}

        def handler(request):
            captured["body"] = request.content.decode()
            captured["content_type"] = request.headers.get("content-type")
            return httpx.Response(200)

        client = make_webhook_client(handler)
        await client.notify_scrape_complete(make_payload(total_opportunities=7))

        assert '"total_opportunities":7' in captured["body"]
        assert captured["content_type"] == "application/json"
        await client.close()

    async def test_includes_secret_header_when_configured(self):
        captured = {}

        def handler(request):
            captured["secret"] = request.headers.get("x-webhook-secret")
            return httpx.Response(200)

        client = make_webhook_client(handler, secret="s3cr3t")
        await client.notify_scrape_complete(make_payload())

        assert captured["secret"] == "s3cr3t"
        await client.close()

    async def test_omits_secret_header_when_not_configured(self):
        captured = {}

        def handler(request):
            captured["secret"] = request.headers.get("x-webhook-secret")
            return httpx.Response(200)

        client = make_webhook_client(handler)
        await client.notify_scrape_complete(make_payload())

        assert captured["secret"] is None
        await client.close()


class TestFailureHandling:
    async def test_server_error_returns_false_without_raising(self):
        client = make_webhook_client(lambda req: httpx.Response(500, text="boom"))
        assert await client.notify_scrape_complete(make_payload()) is False
        await client.close()

    async def test_connection_error_returns_false_without_raising(self):
        def handler(request):
            raise httpx.ConnectError("refused", request=request)

        client = make_webhook_client(handler)
        assert await client.notify_scrape_complete(make_payload()) is False
        await client.close()

    async def test_retries_then_succeeds(self):
        calls = []

        def handler(request):
            calls.append(request)
            if len(calls) < 2:
                return httpx.Response(503)
            return httpx.Response(200)

        client = make_webhook_client(handler)
        assert await client.notify_scrape_complete(make_payload()) is True
        assert len(calls) == 2
        await client.close()

    async def test_missing_url_returns_false_without_request(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200)

        http = BaseHttpClient(
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        client = WebhookClient(webhook_url="", http_client=http)

        assert await client.notify_scrape_complete(make_payload()) is False
        assert calls == []
        await client.close()
