#!/usr/bin/env python3
"""CCBA Maskara — CLI Delegate for CCBA Maskara Security Scanner.

Delegates all business logic and command execution to the `ccba_maskara` deep package.
Maintains 100% backward compatibility for all existing scripts, workflows, and CI/CD pipelines.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Safe Bootstrap: ensure packages/ccba-maskara/src is in sys.path even if not pip-installed
_PACKAGE_SRC = Path(__file__).resolve().parent.parent / "packages" / "ccba-maskara" / "src"
if _PACKAGE_SRC.exists() and str(_PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_SRC))

from ccba_maskara import (
    MaskaraScanner,
    apply_raw_redactions,
    backup_and_write,
    detect_secrets_in_text,
    is_binary,
    redact_secrets_in_text,
)
from ccba_maskara._locator import (
    AGENT_ALIASES,
    AGENT_SPECS,
    get_default_roots,
    normalize_agent_name,
    resolve_targets,
)
from ccba_maskara._redactor import BACKUP_DIR
from ccba_maskara._rules import REGEX_PATTERNS, SAFE_STRINGS
from ccba_maskara.cli import main, run_cli

# Re-export convenience aliases for any legacy external callers
__all__ = [
    "MaskaraScanner",
    "detect_secrets_in_text",
    "redact_secrets_in_text",
    "apply_raw_redactions",
    "backup_and_write",
    "is_binary",
    "normalize_agent_name",
    "get_default_roots",
    "resolve_targets",
    "main",
    "run_cli",
    "REGEX_PATTERNS",
    "SAFE_STRINGS",
    "AGENT_SPECS",
    "AGENT_ALIASES",
    "BACKUP_DIR",
]

if __name__ == "__main__":
    main()
