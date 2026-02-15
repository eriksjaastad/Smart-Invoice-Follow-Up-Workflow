"""
Escalation logic for invoice reminders.
Ported from src/invoice_collector/router.py

This module contains the core business logic for determining:
1. How many days an invoice is overdue
2. Which escalation stage should be used
3. Whether a reminder draft should be created

The 6-stage escalation sequence:
- 7 days: Friendly check-in
- 14 days: Direct follow-up
- 21 days: More urgent tone
- 28 days: Firm reminder with call suggestion
- 35 days: Final reminder before escalation
- 42 days: Last notice before collections/legal
"""
from datetime import date
from typing import Optional


# Escalation stages (days overdue)
STAGES = [7, 14, 21, 28, 35, 42]


def days_overdue(due_date: date, today: Optional[date] = None) -> int:
    """
    Calculate how many days an invoice is overdue.

    Args:
        due_date: The date the invoice was due
        today: Reference date (defaults to today)

    Returns:
        Number of days overdue (0 if not yet overdue)
    
    Examples:
        >>> from datetime import date
        >>> days_overdue(date(2024, 1, 1), date(2024, 1, 8))
        7
        >>> days_overdue(date(2024, 1, 10), date(2024, 1, 5))
        0
    """
    if today is None:
        today = date.today()
    return max(0, (today - due_date).days)


def stage_for(days: int) -> Optional[int]:
    """
    Determine which reminder stage should be sent based on days overdue.

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
    
    Examples:
        >>> stage_for(0)
        
        >>> stage_for(7)
        7
        >>> stage_for(10)
        7
        >>> stage_for(14)
        14
        >>> stage_for(50)
        42
    """
    eligible_stages = [s for s in STAGES if days >= s]
    return max(eligible_stages) if eligible_stages else None


def should_send_draft(
    stage: Optional[int],
    last_stage_sent: Optional[int],
    last_sent_at: Optional[date],
    today: Optional[date] = None
) -> bool:
    """
    Determine if a reminder draft should be created.

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
        True if a reminder draft should be created, False otherwise
    
    Examples:
        >>> from datetime import date
        >>> # First reminder at 7 days
        >>> should_send_draft(7, None, None, date(2024, 1, 8))
        True
        >>> # Already sent today
        >>> should_send_draft(7, None, date(2024, 1, 8), date(2024, 1, 8))
        False
        >>> # Same stage as last time
        >>> should_send_draft(7, 7, date(2024, 1, 1), date(2024, 1, 8))
        False
        >>> # Moving to next stage
        >>> should_send_draft(14, 7, date(2024, 1, 1), date(2024, 1, 15))
        True
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
    Get the next stage in the escalation sequence.

    Args:
        current_stage: Current stage (or None if no stage sent yet)

    Returns:
        Next stage number or None if at the end of sequence
    
    Examples:
        >>> get_next_stage(None)
        7
        >>> get_next_stage(7)
        14
        >>> get_next_stage(42)
        
    """
    if current_stage is None:
        return STAGES[0] if STAGES else None

    try:
        current_index = STAGES.index(current_stage)
        if current_index < len(STAGES) - 1:
            return STAGES[current_index + 1]
    except (ValueError, IndexError):
        pass

    return None

