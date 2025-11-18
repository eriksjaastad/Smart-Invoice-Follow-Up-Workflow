"""
Tests for routing logic
"""
import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invoice_collector.router import (
    days_overdue,
    stage_for,
    should_send,
    get_next_stage,
    days_until_next_stage,
)


class TestDaysOverdue:
    """Test days_overdue calculation"""

    def test_overdue_by_one_day(self):
        due = date(2025, 1, 1)
        today = date(2025, 1, 2)
        assert days_overdue(due, today) == 1

    def test_overdue_by_week(self):
        due = date(2025, 1, 1)
        today = date(2025, 1, 8)
        assert days_overdue(due, today) == 7

    def test_not_yet_due(self):
        due = date(2025, 1, 10)
        today = date(2025, 1, 5)
        assert days_overdue(due, today) == 0

    def test_due_today(self):
        today = date(2025, 1, 1)
        assert days_overdue(today, today) == 0


class TestStageFor:
    """Test stage determination"""

    def test_stage_7(self):
        assert stage_for(7) == 7
        assert stage_for(8) == 7
        assert stage_for(13) == 7

    def test_stage_14(self):
        assert stage_for(14) == 14
        assert stage_for(15) == 14
        assert stage_for(20) == 14

    def test_stage_21(self):
        assert stage_for(21) == 21
        assert stage_for(22) == 21
        assert stage_for(27) == 21

    def test_stage_28(self):
        assert stage_for(28) == 28
        assert stage_for(30) == 28
        assert stage_for(34) == 28

    def test_stage_35(self):
        assert stage_for(35) == 35
        assert stage_for(40) == 35
        assert stage_for(41) == 35

    def test_stage_42(self):
        assert stage_for(42) == 42
        assert stage_for(50) == 42
        assert stage_for(100) == 42

    def test_not_overdue_enough(self):
        assert stage_for(0) is None
        assert stage_for(1) is None
        assert stage_for(6) is None


class TestShouldSend:
    """Test should_send logic"""

    def test_first_reminder(self):
        """Should send first reminder"""
        today = date(2025, 1, 15)
        assert should_send(stage=7, last_stage_sent=None, last_sent_at=None, today=today)

    def test_already_sent_today(self):
        """Should not send if already sent today"""
        today = date(2025, 1, 15)
        assert not should_send(stage=7, last_stage_sent=None, last_sent_at=today, today=today)

    def test_higher_stage(self):
        """Should send when moving to higher stage"""
        today = date(2025, 1, 22)
        assert should_send(stage=14, last_stage_sent=7, last_sent_at=date(2025, 1, 15), today=today)

    def test_same_stage(self):
        """Should not re-send same stage"""
        today = date(2025, 1, 22)
        assert not should_send(stage=7, last_stage_sent=7, last_sent_at=date(2025, 1, 15), today=today)

    def test_lower_stage(self):
        """Should not send lower stage"""
        today = date(2025, 1, 22)
        assert not should_send(stage=7, last_stage_sent=14, last_sent_at=date(2025, 1, 15), today=today)

    def test_no_stage(self):
        """Should not send if no stage determined"""
        today = date(2025, 1, 22)
        assert not should_send(stage=None, last_stage_sent=None, last_sent_at=None, today=today)


class TestGetNextStage:
    """Test next stage calculation"""

    def test_first_stage(self):
        assert get_next_stage(None) == 7

    def test_progression(self):
        assert get_next_stage(7) == 14
        assert get_next_stage(14) == 21
        assert get_next_stage(21) == 28
        assert get_next_stage(28) == 35
        assert get_next_stage(35) == 42

    def test_final_stage(self):
        assert get_next_stage(42) is None


class TestDaysUntilNextStage:
    """Test days until next stage calculation"""

    def test_before_first_stage(self):
        assert days_until_next_stage(5) == 2  # 7 - 5

    def test_at_stage(self):
        assert days_until_next_stage(7) == 7  # 14 - 7

    def test_between_stages(self):
        assert days_until_next_stage(10) == 4  # 14 - 10

    def test_at_final_stage(self):
        assert days_until_next_stage(42) is None


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_complete_escalation_sequence(self):
        """Test complete escalation from day 0 to day 42+"""
        due_date = date(2025, 1, 1)

        # Day 5 - not overdue enough
        today = due_date + timedelta(days=5)
        days = days_overdue(due_date, today)
        assert stage_for(days) is None

        # Day 7 - first reminder
        today = due_date + timedelta(days=7)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 7
        assert should_send(stage_for(days), None, None, today)

        # Day 14 - second reminder
        today = due_date + timedelta(days=14)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 14
        assert should_send(stage_for(days), 7, due_date + timedelta(days=7), today)

        # Day 21 - third reminder
        today = due_date + timedelta(days=21)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 21
        assert should_send(stage_for(days), 14, due_date + timedelta(days=14), today)

        # Day 28 - fourth reminder
        today = due_date + timedelta(days=28)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 28
        assert should_send(stage_for(days), 21, due_date + timedelta(days=21), today)

        # Day 35 - fifth reminder
        today = due_date + timedelta(days=35)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 35
        assert should_send(stage_for(days), 28, due_date + timedelta(days=28), today)

        # Day 42 - final reminder
        today = due_date + timedelta(days=42)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 42
        assert should_send(stage_for(days), 35, due_date + timedelta(days=35), today)

        # Day 50 - still at final stage
        today = due_date + timedelta(days=50)
        days = days_overdue(due_date, today)
        assert stage_for(days) == 42
