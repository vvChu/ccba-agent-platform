"""
Hook script for pre-tool privacy checks.
Blocks access to sensitive files unless approved by the user via an 'APPROVED:' path prefix.
"""

import sys
from pathlib import Path


def main(event: str, payload: dict) -> int:
    path_arg = payload.get("path")
    if not path_arg:
        return 0
    
    # Files/directories that are sensitive by default
    sensitive_patterns = [".env", ".git-credentials", "id_rsa", "id_ecdsa", "id_ed25519", "google_creds"]
    
    # Check if path contains sensitive patterns
    path_lower = path_arg.lower()
    is_sensitive = any(pattern in path_lower for pattern in sensitive_patterns)
    
    # Check for approval prefix
    if is_sensitive:
        if path_arg.startswith("APPROVED:"):
            # Strip the prefix and allow
            clean_path = path_arg.replace("APPROVED:", "")
            print(f"\x1b[32m✓\x1b[0m Privacy: User-approved access allowed to {clean_path}")
            return 0
        else:
            # Block and output instructions
            print(f"""
\x1b[36mNOTE:\x1b[0m This is not an error - this block protects sensitive data.

\x1b[33mPRIVACY BLOCK\x1b[0m: Sensitive file access requires user approval

  \x1b[33mFile:\x1b[0m {path_arg}

  This file may contain secrets (API keys, passwords, tokens).

  To bypass this block:
  1. Ask the user for approval.
  2. If approved, prefix the path argument with "APPROVED:" (e.g., APPROVED:{path_arg}).
""")
            return 2  # Block code
            
    return 0
