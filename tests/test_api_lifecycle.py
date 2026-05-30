"""
API lifecycle integration tests for Smart Invoice Workflow.

Tests the full user lifecycle using FastAPI TestClient + SQLite in-memory DB.
Make.com / Stripe external calls are mocked — no real API credits consumed.

Run with:
    uv run pytest tests/test_api_lifecycle.py -v
"""
import logging
import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.stripe_event import StripeEvent
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
async def test_stripe_webhook_deduplicates_event_replay(test_client: AsyncClient):
    """Duplicate Stripe event ids return 200 without running the handler twice."""
    handler = AsyncMock(return_value=None)
    event = {
        "id": "evt_duplicate",
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"user_id": "user-123"}}},
    }

    with (
        patch("app.api.billing.stripe.Webhook.construct_event", return_value=event),
        patch("app.api.billing.handle_checkout_completed", handler),
    ):
        first_response = await test_client.post(
            "/api/billing/webhook",
            content=json.dumps({"type": "checkout.session.completed"}),
            headers={"stripe-signature": "valid-signature"},
        )
        second_response = await test_client.post(
            "/api/billing/webhook",
            content=json.dumps({"type": "checkout.session.completed"}),
            headers={"stripe-signature": "valid-signature"},
        )

    assert first_response.status_code == 200
    assert first_response.json() == {"status": "success"}
    assert second_response.status_code == 200
    assert second_response.json() == {"status": "duplicate"}
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_alerts_on_missing_checkout_metadata(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
):
    """checkout.session.completed without metadata.user_id sends an ops alert."""
    send_discord_alert = AsyncMock(return_value=True)
    event = {
        "id": "evt_missing_metadata",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_missing_metadata",
                "customer": "cus_missing_metadata",
                "subscription": "sub_missing_metadata",
                "metadata": {},
            }
        },
    }

    with (
        patch("app.api.billing.stripe.Webhook.construct_event", return_value=event),
        patch("app.api.billing.send_discord_alert", send_discord_alert),
    ):
        response = await test_client.post(
            "/api/billing/webhook",
            content=json.dumps({"type": "checkout.session.completed"}),
            headers={"stripe-signature": "valid-signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    await test_db.refresh(test_user)
    assert test_user.plan == "free"
    assert await test_db.get(StripeEvent, "evt_missing_metadata") is not None
    send_discord_alert.assert_awaited_once()
    assert send_discord_alert.await_args.args[0] == "Stripe checkout missing user metadata"


@pytest.mark.asyncio
async def test_stripe_webhook_alerts_on_subscription_user_not_found(
    test_client: AsyncClient,
    test_db: AsyncSession,
):
    """Subscription events that match no user send an ops alert instead of silently returning."""
    send_discord_alert = AsyncMock(return_value=True)
    event = {
        "id": "evt_deleted_missing_user",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_missing_user",
                "customer": "cus_missing_user",
            }
        },
    }

    with (
        patch("app.api.billing.stripe.Webhook.construct_event", return_value=event),
        patch("app.api.billing.send_discord_alert", send_discord_alert),
    ):
        response = await test_client.post(
            "/api/billing/webhook",
            content=json.dumps({"type": "customer.subscription.deleted"}),
            headers={"stripe-signature": "valid-signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    assert await test_db.get(StripeEvent, "evt_deleted_missing_user") is not None
    send_discord_alert.assert_awaited_once()
    assert send_discord_alert.await_args.args[0] == "Stripe subscription deleted user not found"


@pytest.mark.asyncio
async def test_stripe_webhook_logs_checkout_plan_flip(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    caplog,
):
    """Successful checkout logs the paid-plan flip with Stripe event context."""
    event = {
        "id": "evt_plan_flip",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_plan_flip",
                "customer": "cus_plan_flip",
                "subscription": "sub_plan_flip",
                "metadata": {"user_id": str(test_user.id)},
            }
        },
    }

    caplog.set_level(logging.INFO, logger="app.api.billing")
    with patch("app.api.billing.stripe.Webhook.construct_event", return_value=event):
        response = await test_client.post(
            "/api/billing/webhook",
            content=json.dumps({"type": "checkout.session.completed"}),
            headers={"stripe-signature": "valid-signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    await test_db.refresh(test_user)
    assert test_user.plan == "paid"
    assert test_user.stripe_customer_id == "cus_plan_flip"
    assert test_user.stripe_subscription_id == "sub_plan_flip"
    assert await test_db.get(StripeEvent, "evt_plan_flip") is not None
    assert "Stripe checkout plan flip event=evt_plan_flip" in caplog.text
    assert "old_plan=free new_plan=paid" in caplog.text


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
