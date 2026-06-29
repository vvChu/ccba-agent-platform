"""Hook script for pre-tool privacy checks.

Blocks access to sensitive files and scans tool arguments for secret patterns
using the Maskara detection engine.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Ensure scripts directory is in path to import maskara
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

try:
    from maskara import detect_secrets_in_text
except ImportError:
    # Safe fallback if maskara script is not available
    def detect_secrets_in_text(content: str, filepath: str, agent: str, use_llm: bool = False) -> list:
        return []


def main(event: str, payload: Dict[str, Any]) -> int:
    """Scan tool path and arguments for sensitive credentials.

    Args:
        event: The hook lifecycle event name (e.g. 'pre-tool').
        payload: Dict containing 'tool', 'path', 'args', etc.

    Returns:
        Exit code: 0 to allow execution, 2 to block.
    """
    path_arg = payload.get("path")
    args_str = payload.get("args") or "{}"
    tool_name = payload.get("tool") or ""
    
    # Check if user has explicitly approved this call
    is_approved = False
    if path_arg and path_arg.startswith("APPROVED:"):
        is_approved = True
        path_arg = path_arg.replace("APPROVED:", "")
        
    if not is_approved and "APPROVED:" in args_str:
        is_approved = True
        
    if is_approved:
        clean_path = path_arg or "arguments"
        print(f"\x1b[32m✓\x1b[0m Privacy: User-approved access allowed to {clean_path}")
        return 0

    # 1. Block access to known sensitive file names/paths
    if path_arg:
        sensitive_patterns = [".env", ".git-credentials", "id_rsa", "id_ecdsa", "id_ed25519", "google_creds"]
        path_lower = path_arg.lower()
        if any(pattern in path_lower for pattern in sensitive_patterns):
            print(f"""
\x1b[36mNOTE:\x1b[0m This is not an error - this block protects sensitive data.

\x1b[33mPRIVACY BLOCK\x1b[0m: Sensitive file access requires user approval

  \x1b[33mFile:\x1b[0m {path_arg}

  This file may contain secrets (API keys, passwords, tokens).

  To bypass this block:
  1. Ask the user for approval.
  2. If approved, prefix the path argument or args with "APPROVED:" (e.g., APPROVED:{path_arg}).
""")
            return 2  # Block execution

    # 2. Scan tool arguments content for exposed secrets
    findings = detect_secrets_in_text(args_str, f"tool_args:{tool_name}", "agent")
    if findings:
        print(f"\n\x1b[31m[PRIVACY BLOCK]\x1b[0m: Tool call blocked. Detected {len(findings)} potential secret(s) in arguments:")
        for f in findings:
            print(f"  - Pattern: {f['rule_name']} ({f['severity']}) | Masked Preview: {f['preview']}")
        print("""
  Security policy prevents tools from executing with raw secrets.

  To bypass this block:
  1. Ask the user for approval.
  2. Prefix the argument or path with "APPROVED:" to authorize this specific invocation.
  3. Alternatively, run `python scripts/maskara.py redact` to clean up local files.
""")
        return 2  # Block execution

    return 0
