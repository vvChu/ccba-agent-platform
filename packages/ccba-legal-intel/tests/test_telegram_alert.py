"""Unit tests for TelegramAlertHandler in ccba_legal."""

from ccba_legal.alert_handler import TelegramAlertHandler


def test_detect_captcha_or_login_required() -> None:
    """Test detecting login requirement and CAPTCHA forms from HTML page text."""
    handler = TelegramAlertHandler()

    # Normal text should return False
    assert handler.detect_captcha_or_login_required("Luật Phòng cháy và chữa cháy 2024") is False

    # Login / VIP expired text
    login_html = "Vui lòng đăng nhập tài khoản TVPL VIP để xem nội dung đầy đủ"
    assert handler.detect_captcha_or_login_required(login_html) is True

    # CAPTCHA text
    captcha_html = "Xác nhận bạn không phải là người máy (CAPTCHA)"
    assert handler.detect_captcha_or_login_required(captcha_html) is True


def test_send_alert_mock() -> None:
    """Test sending alert using a mock sender."""
    received_messages: list[str] = []

    def mock_sender(msg: str) -> bool:
        received_messages.append(msg)
        return True

    handler = TelegramAlertHandler()
    sent = handler.send_alert(
        message="Alert: TVPL VIP Session Expired!",
        mock_sender=mock_sender,
    )

    assert sent is True
    assert len(received_messages) == 1
    assert "TVPL VIP Session Expired" in received_messages[0]


def test_check_and_notify_trigger() -> None:
    """Test check_and_notify triggers alert when login/CAPTCHA text is present."""
    sent_alerts: list[str] = []

    def mock_sender(msg: str) -> bool:
        sent_alerts.append(msg)
        return True

    handler = TelegramAlertHandler()
    page_text = "Tài khoản VIP của bạn đã hết hạn, vui lòng đăng nhập lại."
    doc_url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-55-2024.aspx"

    notified = handler.check_and_notify(
        page_text=page_text,
        doc_url=doc_url,
        mock_sender=mock_sender,
    )

    assert notified is True
    assert len(sent_alerts) == 1
    assert "Luat-55-2024" in sent_alerts[0] or doc_url in sent_alerts[0]
