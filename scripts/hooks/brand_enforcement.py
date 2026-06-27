#!/usr/bin/env python3
"""
Brand Enforcement Hook for ccba-agent-platform.
Checks generated markdown and text files for correct brand names and prohibited words.
"""

import sys
import os
import re
from pathlib import Path

# Brand patterns: (regex pattern, correct spelling)
BRAND_PATTERNS = [
    (r"\bclaudekit\b", "ClaudeKit"),
    (r"\blitellm\b", "LiteLLM"),
    (r"\bantigravity\b", "Antigravity"),
    (r"\bgemini\b", "Gemini"),
]

PROHIBITED_WORDS = [
    r"\blorem ipsum\b",
    r"\bplaceholder\b",
]


def check_file(file_path: Path):
    """Check a file's content for brand and policy compliance."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return
        
    has_issues = False
    
    # Check brand spellings
    for pattern, correct in BRAND_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for m in matches:
            if m != correct:
                print(f"\x1b[33m[Brand Warning]\x1b[0m In file '{file_path}': Found '{m}', expected '{correct}'")
                has_issues = True
                
    # Check prohibited words
    for pattern in PROHIBITED_WORDS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for m in matches:
            print(f"\x1b[31m[Policy Alert]\x1b[0m In file '{file_path}': Found prohibited word '{m}'")
            has_issues = True


def main(event=None, payload=None):
    # If path is provided in payload, check only that file
    if payload and payload.get("path"):
        path = Path(payload["path"])
        if path.exists() and path.is_file():
            check_file(path)
            return 0
            
    # Otherwise, check CLI args if passed
    if sys.argv and len(sys.argv) > 1 and not event:
        for arg in sys.argv[1:]:
            path = Path(arg)
            if path.exists() and path.is_file():
                check_file(path)
        return 0
        
    # Otherwise, scan newly created or modified .md/.txt files in the workspace (excluding claudekit-engineer and .agents)
    cwd = Path.cwd()
    exclude_dirs = {".git", "claudekit-engineer", ".agents", "node_modules", "venv", ".venv"}
    
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.endswith((".md", ".txt")):
                file_path = Path(root) / f
                if "node_modules" in str(file_path):
                    continue
                check_file(file_path)
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
    sys.exit(0)
