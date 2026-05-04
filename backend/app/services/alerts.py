"""Operational alert helpers for production error visibility."""
from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

import httpx
import sentry_sdk

from app.core.config import settings

logger = logging.getLogger(__name__)

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "client_secret",
    "password",
    "secret",
    "signature",
    "token",
    "webhook",
)
_MAX_VALUE_LENGTH = 500
_MAX_DISCORD_CONTENT_LENGTH = 1900


def _truncate(value: str, max_length: int = _MAX_VALUE_LENGTH) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3]}..."


def _redact_context_value(key: str, value: Any) -> Any:
    key_lower = key.lower()
    if any(part in key_lower for part in _SENSITIVE_KEY_PARTS):
        return "[redacted]"

    if isinstance(value, Mapping):
        return {
            str(nested_key): _redact_context_value(str(nested_key), nested_value)
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_redact_context_value(key, item) for item in value]

    if isinstance(value, str):
        return _truncate(value)

    return value


def _sanitize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    return {
        str(key): _redact_context_value(str(key), value)
        for key, value in context.items()
    }


def _build_discord_content(
    title: str,
    message: str,
    context: Mapping[str, Any] | None,
) -> str:
    parts = [
        f"**{_truncate(title, 180)}**",
        f"Environment: `{settings.environment}`",
        f"Message: {_truncate(message)}",
    ]

    sanitized_context = _sanitize_context(context)
    if sanitized_context:
        context_json = json.dumps(
            sanitized_context,
            default=str,
            indent=2,
            sort_keys=True,
        )
        parts.append(f"Context:\n```json\n{_truncate(context_json, 900)}\n```")

    return _truncate("\n".join(parts), _MAX_DISCORD_CONTENT_LENGTH)


async def send_discord_alert(
    title: str,
    message: str,
    context: Mapping[str, Any] | None = None,
) -> bool:
    """Post an operational alert to Discord if SIW_ALERT_WEBHOOK_URL is set."""
    webhook_url = settings.siw_alert_webhook_url.strip()
    if not webhook_url:
        logger.debug("Skipping Discord alert because SIW_ALERT_WEBHOOK_URL is unset")
        return False

    content = _build_discord_content(title, message, context)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json={"content": content})
            response.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Discord alert")
        return False


async def report_exception(
    title: str,
    error: BaseException,
    context: Mapping[str, Any] | None = None,
) -> bool:
    """Capture an exception in Sentry and notify Discord when configured."""
    sentry_sdk.capture_exception(error)
    message = f"{type(error).__name__} raised; see Sentry for traceback."
    return await send_discord_alert(title, message, context)
