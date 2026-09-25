"""Unit tests for the unified Telegram alert emitter and verification script."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from scripts.eval.telegram_alert import send_telegram_alert
from scripts.verify_telegram_alert import main as verify_main

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_send_telegram_alert_mock_fallback_when_credentials_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing credentials return True when mock_fallback is True."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    result = send_telegram_alert(
        message="Test alert message",
        bot_token=None,
        chat_id=None,
        mock_fallback=True,
    )
    assert result is True


def test_send_telegram_alert_strict_failure_when_credentials_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing credentials return False when mock_fallback is False."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    result = send_telegram_alert(
        message="Test alert message",
        bot_token=None,
        chat_id=None,
        mock_fallback=False,
    )
    assert result is False


def test_send_telegram_alert_success_with_mock_urllib() -> None:
    """Verify alert payload serialization and successful HTTP dispatch."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    captured_requests: list[urllib.request.Request] = []

    def fake_urlopen(req: urllib.request.Request, timeout: int = 10) -> MagicMock:
        captured_requests.append(req)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = send_telegram_alert(
            message="*Bold Notification*",
            bot_token="test_credential_123",
            chat_id="123456789",
            parse_mode="Markdown",
            timeout=5,
            mock_fallback=False,
        )

    assert result is True
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert "test_credential_123" in req.full_url
    assert req.headers.get("Content-type") == "application/json"

    sent_body = json.loads(req.data.decode("utf-8"))
    assert sent_body["chat_id"] == "123456789"
    assert sent_body["text"] == "*Bold Notification*"
    assert sent_body["parse_mode"] == "Markdown"


def test_send_telegram_alert_api_error_response() -> None:
    """Verify HTTP non-200 responses return False gracefully."""
    mock_resp = MagicMock()
    mock_resp.status = 400
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_telegram_alert(
            message="Test error message",
            bot_token="test_credential_123",
            chat_id="123456789",
            mock_fallback=False,
        )

    assert result is False


def test_send_telegram_alert_network_exception() -> None:
    """Verify network exceptions are safely caught and return False."""
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Connection refused"),
    ):
        result = send_telegram_alert(
            message="Test exception message",
            bot_token="test_credential_123",
            chat_id="123456789",
            mock_fallback=False,
        )

    assert result is False


def test_verify_telegram_alert_cli_without_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify verify_telegram_alert prints helpful instructions and exits with 1 when env missing."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        verify_main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Chưa cấu hình TELEGRAM_BOT_TOKEN" in captured.out
    assert "BotFather" in captured.out


def test_send_telegram_alert_suppressed_in_pytest_when_bot_token_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that send_telegram_alert suppresses real network calls in test mode when bot_token is None."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "real_looking_token_12345")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    # When PYTEST_CURRENT_TEST is present (standard during pytest runs) and bot_token is None,
    # it must safely intercept without making actual HTTP requests.
    result = send_telegram_alert(message="Test message during pytest", bot_token=None)
    assert result is True
