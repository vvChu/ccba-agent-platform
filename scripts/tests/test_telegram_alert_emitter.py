"""Unit tests for the unified Telegram alert emitter and verification script."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness.cli import run_notify_cli
from scripts.eval.telegram_alert import (
    check_telegram_token_health,
    send_telegram_alert,
    send_telegram_document,
)
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


def test_check_telegram_token_health_200_ok() -> None:
    """Verify check_telegram_token_health returns True on HTTP 200 OK."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        ok = check_telegram_token_health(bot_token="valid_bot_token_123")
        assert ok is True
        req = mock_open.call_args[0][0]
        assert req.full_url.endswith("/botvalid_bot_token_123/getMe")


def test_check_telegram_token_health_401_unauthorized(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify check_telegram_token_health catches HTTP 401 Unauthorized and logs @BotFather guidance."""
    err_401 = urllib.error.HTTPError(
        url="https://api.telegram.org/botrevoked/getMe",
        code=401,
        msg="Unauthorized",
        hdrs=MagicMock(),
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=err_401):
        ok = check_telegram_token_health(bot_token="revoked_token")
        assert ok is False
        assert "@BotFather" in caplog.text


def test_send_telegram_document_200_ok(tmp_path: Path) -> None:
    """Verify send_telegram_document encodes multipart payload and succeeds on HTTP 200."""
    doc_file = tmp_path / "pccc_audit_report.pdf"
    doc_file.write_bytes(b"%PDF-1.4 mock content")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    captured_reqs: list[urllib.request.Request] = []

    def fake_urlopen(req: urllib.request.Request, timeout: int = 10) -> MagicMock:
        captured_reqs.append(req)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        ok = send_telegram_document(
            file_path=doc_file,
            caption="<b>Báo cáo thẩm tra PCCC</b>",
            bot_token="test_token_doc",
            chat_id="987654321",
            parse_mode="HTML",
        )

    assert ok is True
    assert len(captured_reqs) == 2
    assert captured_reqs[0].full_url.endswith("/getMe")
    upload_req = captured_reqs[1]
    assert upload_req.full_url.endswith("/sendDocument")
    assert "multipart/form-data; boundary=" in str(upload_req.headers.get("Content-type"))
    body_bytes = bytes(upload_req.data)
    assert b'filename="pccc_audit_report.pdf"' in body_bytes
    assert b"%PDF-1.4 mock content" in body_bytes
    assert "<b>Báo cáo thẩm tra PCCC</b>".encode() in body_bytes


def test_send_telegram_document_401_unauthorized(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify send_telegram_document aborts and logs @BotFather guidance when token returns 401."""
    doc_file = tmp_path / "report.docx"
    doc_file.write_bytes(b"PK mock docx")

    err_401 = urllib.error.HTTPError(
        url="https://api.telegram.org/botexpired/getMe",
        code=401,
        msg="Unauthorized",
        hdrs=MagicMock(),
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=err_401):
        ok = send_telegram_document(
            file_path=doc_file,
            caption="Test",
            bot_token="expired_token",
            chat_id="12345",
        )
    assert ok is False
    assert "@BotFather" in caplog.text


def test_send_telegram_document_validation_and_cli_notify(tmp_path: Path) -> None:
    """Verify missing file, unsupported extension, and run_notify_cli dispatch."""
    assert send_telegram_document(tmp_path / "missing.pdf", bot_token="t", chat_id="c") is False

    bad_ext = tmp_path / "malware.exe"
    bad_ext.write_bytes(b"MZ")
    assert send_telegram_document(bad_ext, bot_token="t", chat_id="c") is False

    valid_html = tmp_path / "dashboard.html"
    valid_html.write_text("<h1>Report</h1>", encoding="utf-8")

    with patch("ccba_harness.evals.daemon.send_telegram_document", return_value=True) as mock_doc:
        rc = run_notify_cli(["--file", str(valid_html), "--caption", "HTML Report", "--mock"])
        assert rc == 0
        mock_doc.assert_called_once()

    with patch("ccba_harness.evals.daemon.check_telegram_token_health", return_value=True) as m_chk:
        assert run_notify_cli(["--check-token", "--mock"]) == 0
        m_chk.assert_called_once()
