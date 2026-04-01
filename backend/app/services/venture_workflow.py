"""
Venture workflow event recording.

Lightweight structured logging for workflow results.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowEvent:
    event: str
    status: str
    details: dict[str, Any]
    recorded_at: datetime


def record_workflow_event(event: str, status: str, details: dict[str, Any] | None = None) -> WorkflowEvent:
    payload = details or {}
    record = WorkflowEvent(
        event=event,
        status=status,
        details=payload,
        recorded_at=datetime.now(timezone.utc),
    )
    logger.info("Workflow event recorded: %s", record)
    return record
