#!/usr/bin/env python3
"""Script to verify and test Telegram Bot notification integration on Server Spark."""

import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

# Auto-load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)


def main() -> None:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    print("=================================================================")
    print("🤖 [CCBA Telegram Notification Tester]")
    print("=================================================================")

    if not bot_token or not chat_id:
        print("❌ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env!")
        print()
        print("📝 Hướng dẫn thiết lập:")
        print("  1. Mở hoặc tạo file: ~/ccba/ccba-agent-platform/.env")
        print("  2. Điền thông tin:")
        print("     TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz")
        print("     TELEGRAM_CHAT_ID=-1001234567890 (hoặc ID cá nhân/nhóm)")
        print()
        print("💡 Cách lấy Token & Chat ID:")
        print(
            "  - Bot Token: Chat với @BotFather trên Telegram -> gõ /newbot -> lưu HTTP API Token"
        )
        print(
            "  - Chat ID: Chat với bot @userinfobot hoặc @RawDataBot để lấy Chat ID của bạn / nhóm"
        )
        print("=================================================================")
        sys.exit(1)

    print(f"🔑 Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"💬 Chat ID:   {chat_id}")
    print("📤 Đang gửi tin nhắn thử nghiệm...")

    test_message = (
        "🚀 *[CCBA Server Spark]* 🤖\n"
        "✅ *Kênh Thông Báo Telegram Đã Sẵn Sàng!*\n\n"
        "📅 Thời gian: `Live Ping Test`\n"
        "⚡ Gateway: `LiteLLM :8090`\n"
        "🌙 Nightly Auto-Tuner: `Crontab 00:00 Daily Active`\n"
    )

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": test_message,
            "parse_mode": "Markdown",
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("ok"):
                    print("=================================================================")
                    print("🎉 THÀNH CÔNG: Tin nhắn thử nghiệm đã được gửi đến Telegram!")
                    print("=================================================================")
                    return
            print(f"⚠️ Telegram API phản hồi mã: {resp.status}")
    except Exception as e:
        print(f"❌ Gửi tin nhắn thất bại: {e}")
        print("💡 Kiểm tra lại Token, Chat ID và quyền gửi tin của Bot vào nhóm/kênh.")
        sys.exit(1)


if __name__ == "__main__":
    main()
