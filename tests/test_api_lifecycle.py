"""
API lifecycle integration tests for Smart Invoice Workflow.

Tests the full user lifecycle using FastAPI TestClient + SQLite in-memory DB.
Make.com / Stripe external calls are mocked — no real API credits consumed.

Run with:
    uv run pytest tests/test_api_lifecycle.py -v
"""
import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


# ---------------------------------------------------------------------------
# Health & Auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Health endpoint returns healthy status."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_me_returns_test_user(test_client: AsyncClient):
    """GET /api/auth/me returns the authenticated test user."""
    response = await test_client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "test@example.com"
    assert body["name"] == "Test User"
    assert body["business_name"] == "Test Co"


@pytest.mark.asyncio
async def test_auth_me_returns_inactive_by_default(test_client: AsyncClient):
    """New users start as inactive before completing onboarding."""
    response = await test_client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is False


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_billing_status_returns_free_plan(test_client: AsyncClient):
    """GET /api/billing/status returns free plan for new user."""
    response = await test_client.get("/api/billing/status")
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body.get("stripe_subscription_id") is None


# ---------------------------------------------------------------------------
# Cron
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cron_trigger_rejects_missing_secret(test_client: AsyncClient, monkeypatch):
    """POST /api/cron/trigger-daily without secret header returns 401."""
    monkeypatch.setattr(settings, "digest_cron_secret", "cron-secret")

    response = await test_client.post("/api/cron/trigger-daily")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cron_trigger_rejects_wrong_secret(test_client: AsyncClient, monkeypatch):
    """POST /api/cron/trigger-daily with wrong secret returns 401 with detail."""
    monkeypatch.setattr(settings, "digest_cron_secret", "cron-secret")

    response = await test_client.post(
        "/api/cron/trigger-daily",
        headers={"x-cron-secret": "totally-wrong-secret"},
    )
    assert response.status_code == 401
    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_cron_trigger_reports_user_processing_exception(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    """Daily cron sends an alert when per-user processing raises."""
    test_user.active = True
    test_user.sheet_id = "sheet-123"
    test_user.google_refresh_token_encrypted = "encrypted-refresh-token"
    await test_db.commit()

    monkeypatch.setattr(settings, "digest_cron_secret", "cron-secret")
    report_exception = AsyncMock(return_value=True)

    with (
        patch(
            "app.api.cron.process_user_invoices",
            AsyncMock(side_effect=RuntimeError("synthetic cron failure")),
        ),
        patch("app.api.cron.report_exception", report_exception),
    ):
        response = await test_client.post(
            "/api/cron/trigger-daily",
            headers={"x-cron-secret": "cron-secret"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["failed"] == 1
    report_exception.assert_awaited_once()


# ---------------------------------------------------------------------------
# Onboarding — sender-info activates user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_onboarding_sender_info_activates_user(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
):
    """
    POST /api/onboarding/sender-info sets user.active=True and stores name/business_name.
    Plan must remain 'free' — sender-info should NOT touch billing.
    """
    response = await test_client.post(
        "/api/onboarding/sender-info",
        json={"name": "Erik Sjaastad", "business_name": "Synth Insight Labs"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is True
    assert body["name"] == "Erik Sjaastad"
    assert body["business_name"] == "Synth Insight Labs"
    assert body["plan"] == "free"


# ---------------------------------------------------------------------------
# Stripe Webhook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stripe_webhook_rejects_unsigned(test_client: AsyncClient):
    """
    POST /api/billing/webhook with no stripe-signature header returns 400.
    The detail message must mention 'signature'.
    """
    response = await test_client.post(
        "/api/billing/webhook",
        content=json.dumps({"type": "checkout.session.completed"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert "signature" in body["detail"].lower()


@pytest.mark.asyncio
async def test_stripe_webhook_reports_handler_exception(test_client: AsyncClient):
    """Stripe webhook processing exceptions are reported before returning 500."""
    report_exception = AsyncMock(return_value=True)

    with (
        patch("app.api.billing.stripe.Webhook.construct_event") as construct_event,
        patch(
            "app.api.billing.handle_checkout_completed",
            AsyncMock(side_effect=RuntimeError("synthetic stripe failure")),
        ),
        patch("app.api.billing.report_exception", report_exception),
    ):
        construct_event.return_value = {
            "id": "evt_test",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"user_id": "user-123"}}},
        }
        with pytest.raises(RuntimeError, match="synthetic stripe failure"):
            await test_client.post(
                "/api/billing/webhook",
                content=json.dumps({"type": "checkout.session.completed"}),
                headers={"stripe-signature": "valid-signature"},
            )

    report_exception.assert_awaited_once()


@pytest.mark.asyncio
async def test_auth_callback_reports_exception(test_client: AsyncClient):
    """Auth0 callback exceptions are reported before returning 500."""
    report_exception = AsyncMock(return_value=True)

    with (
        patch(
            "app.api.auth.oauth.auth0.authorize_access_token",
            AsyncMock(side_effect=RuntimeError("synthetic auth failure")),
        ),
        patch("app.api.auth.report_exception", report_exception),
    ):
        response = await test_client.get("/api/auth/callback")

    assert response.status_code == 500
    report_exception.assert_awaited_once()
