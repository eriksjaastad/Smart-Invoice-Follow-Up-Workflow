"""
Soak metrics writer for sandbox stability runs.

Writes JSONL events to a configured path to provide evidence artifacts.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def record_soak_event(event: Mapping[str, Any], path: str | None) -> None:
    """Append a JSONL soak event if a metrics path is configured."""
    if not path:
        return

    file_path = Path(path)
    if file_path.is_absolute():
        logger.warning("Soak metrics path is absolute; prefer a relative path via env var.")

    payload = dict(event)
    payload.setdefault("ts", _utc_now_iso())

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception("Failed to create soak metrics directory", extra={"path": str(file_path.parent)})
        return

    try:
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    except Exception:
        logger.exception("Failed to write soak metrics event", extra={"path": str(file_path)})
