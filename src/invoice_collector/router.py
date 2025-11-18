"""
Routing logic for determining which reminder stage to send
Based on days overdue: 7, 14, 21, 28, 35, 42 days
"""
from datetime import date
from typing import Optional
from .config import settings


def days_overdue(due_date: date, today: date = None) -> int:
    """
    Calculate how many days an invoice is overdue

    Args:
        due_date: The date the invoice was due
        today: Reference date (defaults to today)

    Returns:
        Number of days overdue (0 if not yet overdue)
    """
    if today is None:
        today = date.today()
    return max(0, (today - due_date).days)


def stage_for(days: int) -> Optional[int]:
    """
    Determine which reminder stage should be sent based on days overdue

    The system uses these stages:
    - 7 days: Friendly check-in
    - 14 days: Direct follow-up
    - 21 days: More urgent tone
    - 28 days: Firm reminder with call suggestion
    - 35 days: Final reminder before escalation
    - 42 days: Last notice before collections/legal

    Args:
        days: Number of days overdue

    Returns:
        The stage number (7, 14, 21, 28, 35, or 42) or None if not yet time for first reminder
    """
    eligible_stages = [s for s in settings.STAGES if days >= s]
    return max(eligible_stages) if eligible_stages else None


def should_send(
    stage: Optional[int],
    last_stage_sent: Optional[int],
    last_sent_at: Optional[date],
    today: date = None
) -> bool:
    """
    Determine if a reminder should be sent

    Rules:
    1. No reminder if no stage determined (not overdue enough)
    2. No reminder if we already sent one today (prevent duplicates)
    3. Send if we've never sent a reminder before
    4. Send only if moving to a higher stage (prevents re-sending same stage)

    Args:
        stage: Current stage based on days overdue
        last_stage_sent: The last stage that was sent
        last_sent_at: Date when last reminder was sent
        today: Reference date (defaults to today)

    Returns:
        True if a reminder should be sent, False otherwise
    """
    if today is None:
        today = date.today()

    # No stage determined (not overdue enough yet)
    if stage is None:
        return False

    # Already sent a reminder today - prevent duplicates
    if last_sent_at == today:
        return False

    # Never sent a reminder before - definitely send
    if last_stage_sent is None:
        return True

    # Only send if moving to a higher stage
    # This prevents re-sending the same stage if the system runs multiple times
    return stage > last_stage_sent


def get_next_stage(current_stage: Optional[int]) -> Optional[int]:
    """
    Get the next stage in the sequence

    Args:
        current_stage: Current stage (or None if no stage sent yet)

    Returns:
        Next stage number or None if at the end of sequence
    """
    if current_stage is None:
        return settings.STAGES[0] if settings.STAGES else None

    try:
        current_index = settings.STAGES.index(current_stage)
        if current_index < len(settings.STAGES) - 1:
            return settings.STAGES[current_index + 1]
    except (ValueError, IndexError):
        pass

    return None


def days_until_next_stage(days: int) -> Optional[int]:
    """
    Calculate how many days until the next reminder stage

    Args:
        days: Current days overdue

    Returns:
        Number of days until next stage, or None if at final stage
    """
    current_stage = stage_for(days)
    next_stage = get_next_stage(current_stage)

    if next_stage is None:
        return None

    return next_stage - days
