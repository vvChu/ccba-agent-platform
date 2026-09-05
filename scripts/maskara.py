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

from typing import Any

from ccba_maskara import (
    MaskaraScanner,
    apply_raw_redactions,
    backup_and_write,
    detect_secrets_in_text,
    is_binary,
    redact_secrets_in_text,
)
from ccba_maskara.cli import main, run_cli


def normalize_agent_name(name: str) -> str:
    """Normalize agent name to canonical form (backward-compatibility wrapper)."""
    return MaskaraScanner().normalize_agent_name(name)


def get_default_roots(dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
    """Resolve default search roots (backward-compatibility wrapper)."""
    return MaskaraScanner().get_default_roots(dot_dir, app_name, xdg_name)


def resolve_targets(agent_name: str, custom_root: str | None = None) -> list[dict[str, Any]]:
    """Resolve target files and directories for scanning (backward-compatibility wrapper)."""
    return MaskaraScanner().resolve_targets(agent_name, custom_root)


# Re-export public seam and CLI runners for external callers
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
]

if __name__ == "__main__":
    main()
