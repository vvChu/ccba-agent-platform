"""CCBA Maskara — Unified Security Scanning & PII Redaction Deep Module.

Public Deep Seam:
    MaskaraScanner  — Detect secrets, redact credentials, inspect agent sessions.

Standalone Convenience Functions:
    detect_secrets_in_text  — Scan string for sensitive tokens.
    redact_secrets_in_text  — Scan and redact sensitive tokens in string.
    apply_raw_redactions    — Apply index-based byte replacements.
    is_binary               — Fast binary file probe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._redactor import (
    apply_raw_redactions,
    backup_and_write,
)
from ._redactor import (
    redact_findings as apply_redact_findings,
)
from ._scanner import MaskaraScanner

__version__ = "1.0.0"

_default_scanner = MaskaraScanner()


def detect_secrets_in_text(
    content: str, filepath: str = "", agent: str = "", use_llm: bool = False
) -> list[dict[str, Any]]:
    """Scan string content for secrets using default MaskaraScanner."""
    return _default_scanner.scan_text(content, filepath, agent, use_llm)


def redact_secrets_in_text(content: str, agent: str = "text") -> str:
    """Redact secrets in text string using default MaskaraScanner."""
    return _default_scanner.redact_text(content, agent)


def is_binary(filepath: Path) -> bool:
    """Check binary file using default MaskaraScanner."""
    return _default_scanner.is_binary(filepath)


__all__ = [
    # Deep Seam
    "MaskaraScanner",
    # Functions
    "detect_secrets_in_text",
    "redact_secrets_in_text",
    "apply_raw_redactions",
    "apply_redact_findings",
    "backup_and_write",
    "is_binary",
    "__version__",
]
