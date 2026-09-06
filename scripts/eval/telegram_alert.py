"""CCBA Platform Unified Telegram Alert Emitter.

Provides a robust, single-source-of-truth utility for sending notifications
to Telegram channels or bot chats across evaluation daemons and CLI tools.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

logger = logging.getLogger("ccba.telegram_alert")


def send_telegram_alert(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    parse_mode: str = "Markdown",
    timeout: int = 10,
    mock_fallback: bool = False,
) -> bool:
    """Send a notification message to Telegram Bot API.

    Args:
        message: The message body to send (supports Markdown or HTML).
        bot_token: Telegram Bot API Token. If omitted, read from TELEGRAM_BOT_TOKEN env.
        chat_id: Target Chat or Channel ID. If omitted, read from TELEGRAM_CHAT_ID env.
        parse_mode: Telegram parse mode ("Markdown", "MarkdownV2", "HTML", or empty).
        timeout: Network timeout in seconds for urllib request.
        mock_fallback: If True, missing credentials log a mock notification and return True
            (ideal for unattended nightly daemons). If False, returns False.

    Returns:
        bool: True if message was sent successfully (or mock-handled), False otherwise.
    """
    bot_credential = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    target_channel = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_credential or not target_channel:
        if mock_fallback:
            logger.info(f"📱 [Mock Telegram Notification Sent]:\n{message}")
            return True
        logger.warning(
            "⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. Telegram alert was not sent."
        )
        return False

    endpoint_url = f"https://api.telegram.org/bot{bot_credential}/sendMessage"
    data_dict: dict[str, str] = {
        "chat_id": str(target_channel),
        "text": message,
    }
    if parse_mode:
        data_dict["parse_mode"] = parse_mode

    payload = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                logger.info("✅ Đã gửi thông báo Telegram thành công.")
                return True
            logger.warning(f"⚠️ Telegram API phản hồi mã: {resp.status}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Không thể gửi Telegram alert: {e}")
        return False
