"""Privacy & Secret Leakage Prevention Hook for CCBA Lifecycle.

Blocks access to sensitive credential files and scans tool arguments for secret patterns
using the CCBA Maskara detection engine.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .base import BaseHook, HookContext, HookResult

try:
    from ccba_maskara import detect_secrets_in_text
except ImportError:
    _pkg_src = Path(__file__).resolve().parents[2] / "packages" / "ccba-maskara" / "src"
    if _pkg_src.exists() and str(_pkg_src) not in sys.path:
        sys.path.insert(0, str(_pkg_src))
    try:
        from ccba_maskara import detect_secrets_in_text
    except ImportError:

        def detect_secrets_in_text(
            content: str, filepath: str = "", agent: str = "", use_llm: bool = False
        ) -> list[dict[str, Any]]:
            return []


class PrivacyHook(BaseHook):
    """Inspects file paths and tool arguments for sensitive credentials and API keys."""

    name = "privacy_block"
    supported_events = ("pre-tool",)

    SENSITIVE_PATTERNS = [
        ".env",
        ".git-credentials",
        "id_rsa",
        "id_ecdsa",
        "id_ed25519",
        "google_creds",
    ]

    def execute(self, context: HookContext) -> HookResult:
        path_arg = context.path
        args_str = context.args or "{}"
        tool_name = context.tool

        if context.is_approved:
            clean_p = context.clean_path or "arguments"
            msg = f"\x1b[32m✓\x1b[0m Privacy: User-approved access allowed to {clean_p}"
            print(msg)
            return HookResult(name=self.name, exit_code=0, message=msg)

        # 1. Block access to known sensitive file names/paths
        if path_arg:
            path_lower = path_arg.lower()
            if any(pattern in path_lower for pattern in self.SENSITIVE_PATTERNS):
                msg = f"""
\x1b[36mNOTE:\x1b[0m This is not an error - this block protects sensitive data.

\x1b[33mPRIVACY BLOCK\x1b[0m: Sensitive file access requires user approval

  \x1b[33mFile:\x1b[0m {path_arg}

  This file may contain secrets (API keys, passwords, tokens).

  To bypass this block:
  1. Ask the user for approval.
  2. If approved, prefix the path argument or args with "APPROVED:" (e.g., APPROVED:{path_arg}).
"""
                print(msg)
                return HookResult(
                    name=self.name,
                    exit_code=2,
                    message=f"Access to sensitive file '{path_arg}' blocked.",
                    details={"blocked_path": path_arg},
                )

        # 2. Scan tool arguments content for exposed secrets
        findings = detect_secrets_in_text(args_str, f"tool_args:{tool_name}", "agent")
        if findings:
            preview_lines = [
                f"  - Pattern: {f['rule_name']} ({f['severity']}) | Masked Preview: {f['preview']}"
                for f in findings
            ]
            msg = (
                f"\n\x1b[31m[PRIVACY BLOCK]\x1b[0m: Tool call blocked. Detected {len(findings)} potential secret(s) in arguments:\n"
                + "\n".join(preview_lines)
                + """
  Security policy prevents tools from executing with raw secrets.

  To bypass this block:
  1. Ask the user for approval.
  2. Prefix the argument or path with "APPROVED:" to authorize this specific invocation.
  3. Alternatively, run `python scripts/maskara.py redact` to clean up local files.
"""
            )
            print(msg)
            return HookResult(
                name=self.name,
                exit_code=2,
                message=f"Detected {len(findings)} secret(s) in tool arguments.",
                details={"findings": findings},
            )

        return HookResult(name=self.name, exit_code=0, message="Privacy checks passed.")
