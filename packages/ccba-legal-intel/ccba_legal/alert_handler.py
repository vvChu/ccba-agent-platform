"""Telegram Alert Handler for VIP Expiry and CAPTCHA detection."""

import os
from collections.abc import Callable


class TelegramAlertHandler:
    """Handles Telegram Webhook notifications when crawling encounters barriers."""

    TRIGGER_KEYWORDS = [
        "vui lòng đăng nhập",
        "đăng nhập tài khoản",
        "tài khoản vip",
        "hết hạn",
        "captcha",
        "không phải là người máy",
        "cloudflare",
    ]

    def detect_captcha_or_login_required(self, page_text: str) -> bool:
        """Detect whether page text contains CAPTCHA or Login/VIP expired warnings."""
        lowered = page_text.lower()
        return any(kw in lowered for kw in self.TRIGGER_KEYWORDS)

    def send_alert(
        self,
        message: str,
        bot_token: str | None = None,
        chat_id: str | None = None,
        mock_sender: Callable[[str], bool] | None = None,
    ) -> bool:
        """Send a Telegram notification message or invoke mock_sender if provided."""
        if mock_sender:
            return mock_sender(message)

        token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        target_chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

        if not token or not target_chat:
            print(
                f"[TelegramAlert] Warning: Missing bot token or chat ID. Alert not sent: {message}"
            )
            return False

        try:
            import json
            import urllib.parse
            import urllib.request

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({"chat_id": target_chat, "text": message}).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[TelegramAlert] Error sending alert: {e}")
            return False

    def check_and_notify(
        self,
        page_text: str,
        doc_url: str,
        bot_token: str | None = None,
        chat_id: str | None = None,
        mock_sender: Callable[[str], bool] | None = None,
    ) -> bool:
        """Check page_text for barriers and send Telegram alert if detected."""
        if not self.detect_captcha_or_login_required(page_text):
            return False

        msg = (
            f"🚨 [CCBA Legal Alert] Phát hiện rào chắn Đăng nhập/CAPTCHA!\n"
            f"URL: {doc_url}\n"
            f"Hành động: Vui lòng mở Chrome CDP (port 9222) và xác thực thủ công."
        )
        return self.send_alert(msg, bot_token=bot_token, chat_id=chat_id, mock_sender=mock_sender)
