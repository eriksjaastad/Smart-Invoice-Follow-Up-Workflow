"""
Tests for Google Workspace delegated Gmail sending and daily digest wiring.
"""
import base64

from app.core.config import settings
from app.services import digest as digest_service
from app.services import google_workspace


class _FakeSend:
    def __init__(self, sink):
        self._sink = sink

    def execute(self):
        return {"id": "msg-123"}


class _FakeMessages:
    def __init__(self, sink):
        self._sink = sink

    def send(self, userId, body):
        self._sink["userId"] = userId
        self._sink["body"] = body
        return _FakeSend(self._sink)


class _FakeUsers:
    def __init__(self, sink):
        self._sink = sink

    def messages(self):
        return _FakeMessages(self._sink)


class _FakeService:
    def __init__(self, sink):
        self._sink = sink

    def users(self):
        return _FakeUsers(self._sink)


def test_send_delegated_email_builds_message(monkeypatch):
    sink = {}

    def fake_get_service(*_args, **_kwargs):
        return _FakeService(sink)

    monkeypatch.setattr(google_workspace, "_get_gmail_service", fake_get_service)

    response = google_workspace.send_delegated_email(
        subject="Daily Digest",
        html_body="<p>Digest body</p>",
        to_emails="help@smartinvoiceworkflow.com",
        sender="delegated@smartinvoiceworkflow.com",
        service_account_file="service-account.json",
        delegated_user="delegated@smartinvoiceworkflow.com",
    )

    assert response["id"] == "msg-123"
    raw_message = sink["body"]["raw"]
    decoded = base64.urlsafe_b64decode(raw_message.encode("utf-8")).decode("utf-8")
    assert "Subject: Daily Digest" in decoded
    assert "To: help@smartinvoiceworkflow.com" in decoded
    assert "From: delegated@smartinvoiceworkflow.com" in decoded


def test_send_daily_ops_digest_records_workflow(monkeypatch):
    calls = []

    def fake_send(*_args, **_kwargs):
        return {"id": "msg-456"}

    def fake_record(event, status, details=None):
        calls.append((event, status, details))
        return {"event": event, "status": status, "details": details}

    monkeypatch.setattr(digest_service, "send_delegated_email", fake_send)
    monkeypatch.setattr(digest_service, "record_workflow_event", fake_record)
    monkeypatch.setattr(settings, "daily_digest_recipient", "help@smartinvoiceworkflow.com")

    summary = {
        "users_total": 2,
        "processed": 2,
        "failed": 0,
        "drafts_created": 3,
        "invoices_checked": 5,
        "errors": [],
    }

    result = digest_service.send_daily_ops_digest(summary)

    assert result is True
    assert calls
    event, status, details = calls[-1]
    assert event == "daily_digest_send"
    assert status == "success"
    assert details["recipient"] == "help@smartinvoiceworkflow.com"
    assert details["message_id"] == "msg-456"
