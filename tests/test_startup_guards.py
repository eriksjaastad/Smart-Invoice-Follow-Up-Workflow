import logging

import pytest

from app import main


def test_debug_mock_auth_refuses_production_startup(monkeypatch, caplog):
    monkeypatch.setattr(main.settings, "environment", "production")
    monkeypatch.setattr(main.settings, "debug_mock_auth", True)

    with caplog.at_level(logging.CRITICAL), pytest.raises(
        ValueError,
        match="DEBUG_MOCK_AUTH must never be enabled in production",
    ):
        main._validate_startup_configuration()

    assert "DEBUG_MOCK_AUTH must never be enabled in production" in caplog.text


def test_debug_mock_auth_allowed_outside_production(monkeypatch):
    monkeypatch.setattr(main.settings, "environment", "development")
    monkeypatch.setattr(main.settings, "debug_mock_auth", True)

    main._validate_startup_configuration()
