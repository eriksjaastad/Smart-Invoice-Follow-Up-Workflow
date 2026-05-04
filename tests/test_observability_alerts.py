from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services import alerts


@pytest.mark.asyncio
async def test_send_discord_alert_noops_when_webhook_unset(monkeypatch):
    monkeypatch.setattr(settings, "siw_alert_webhook_url", "")

    sent = await alerts.send_discord_alert("Test alert", "Something failed")

    assert sent is False


@pytest.mark.asyncio
async def test_send_discord_alert_posts_sanitized_payload(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json):
            calls.append({"url": url, "json": json})
            return FakeResponse()

    monkeypatch.setattr(settings, "siw_alert_webhook_url", "https://discord.example/webhook")
    monkeypatch.setattr(alerts.httpx, "AsyncClient", FakeAsyncClient)

    sent = await alerts.send_discord_alert(
        "Stripe webhook failed",
        "boom",
        {
            "user_id": "user-123",
            "api_key": "should-not-leak",
            "nested": {"access_token": "also-secret"},
        },
    )

    assert sent is True
    assert calls[0]["url"] == "https://discord.example/webhook"
    content = calls[0]["json"]["content"]
    assert "Stripe webhook failed" in content
    assert "user-123" in content
    assert "should-not-leak" not in content
    assert "also-secret" not in content
    assert "[redacted]" in content


@pytest.mark.asyncio
async def test_report_exception_captures_sentry_and_alerts(monkeypatch):
    captured = []
    send_alert = AsyncMock(return_value=True)
    monkeypatch.setattr(alerts.sentry_sdk, "capture_exception", captured.append)
    monkeypatch.setattr(alerts, "send_discord_alert", send_alert)

    error = RuntimeError("synthetic observability smoke")
    sent = await alerts.report_exception("Synthetic failure", error, {"route": "/test"})

    assert sent is True
    assert captured == [error]
    send_alert.assert_awaited_once()
    alert_args = send_alert.await_args.args
    assert alert_args[1] == "RuntimeError raised; see Sentry for traceback."
    assert "synthetic observability smoke" not in alert_args[1]
