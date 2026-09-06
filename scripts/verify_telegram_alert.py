#!/usr/bin/env python3
"""Script to verify and test Telegram Bot notification integration on Server Spark."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct CLI execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from scripts.eval.telegram_alert import send_telegram_alert

# Ensure UTF-8 output on Windows console
if sys.platform.startswith("win"):
    try:
        reconfig_out = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig_out):
            reconfig_out(encoding="utf-8")
        reconfig_err = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfig_err):
            reconfig_err(encoding="utf-8")
    except Exception:
        pass

# Auto-load environment variables
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def main() -> None:
    """Entrypoint for Telegram alert verification CLI."""
    bot_credential = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_channel = os.environ.get("TELEGRAM_CHAT_ID")

    print("=================================================================")
    print("🤖 [CCBA Telegram Notification Verifier]")
    print("=================================================================")

    if not bot_credential or not chat_channel:
        print("❌ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID!")
        print()
        print("📝 Hướng dẫn thiết lập:")
        print("  1. Thiết lập trong biến môi trường hoặc file cấu hình .env:")
        print("     - TELEGRAM_BOT_TOKEN (mã token lấy từ BotFather)")
        print("     - TELEGRAM_CHAT_ID (id phòng chat hoặc kênh thông báo)")
        print()
        print("💡 Cách lấy thông tin:")
        print("  - Bot Token: chat với @BotFather trên Telegram -> gõ /newbot")
        print("  - Chat ID: chat với bot @userinfobot để lấy ID của bạn hoặc nhóm")
        print("=================================================================")
        sys.exit(1)

    if len(bot_credential) > 12:
        masked_token = f"{bot_credential[:8]}...{bot_credential[-4:]}"
    else:
        masked_token = "***"
    print("🔑 Trạng thái Token:", masked_token)
    print("💬 Kênh nhận tin:", chat_channel)
    print("📤 Đang gửi tin nhắn thử nghiệm qua Telegram Alert Seam...")

    test_message = (
        "🚀 *[CCBA Server Spark]* 🤖\n"
        "✅ *Kênh Thông Báo Telegram Đã Sẵn Sàng!*\n\n"
        "📅 Thời gian: `Live Ping Test`\n"
        "⚡ Gateway: `LiteLLM :8090`\n"
        "🌙 Nightly Auto-Tuner: `Crontab 00:00 Daily Active`\n"
    )

    success = send_telegram_alert(
        message=test_message,
        bot_token=bot_credential,
        chat_id=chat_channel,
        parse_mode="Markdown",
        mock_fallback=False,
    )

    if success:
        print("=================================================================")
        print("🎉 THÀNH CÔNG: Tin nhắn thử nghiệm đã được gửi đến Telegram!")
        print("=================================================================")
    else:
        print("❌ Gửi tin nhắn thất bại. Vui lòng kiểm tra lại Token, Chat ID và quyền của Bot.")
        sys.exit(1)


if __name__ == "__main__":
    main()
