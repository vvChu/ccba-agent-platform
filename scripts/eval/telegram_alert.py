"""CCBA Platform Unified Telegram Alert Emitter.

Thin facade delegating to ccba_harness.evals.daemon (ADR-0057 Cổng 0).
Provides a robust, single-source-of-truth utility for sending notifications
to Telegram channels or bot chats across evaluation daemons and CLI tools.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add packages to sys.path if not present
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "ccba-harness" / "src"))

from ccba_harness.evals.daemon import send_telegram_alert

__all__ = ["send_telegram_alert"]
