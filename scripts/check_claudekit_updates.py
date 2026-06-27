#!/usr/bin/env python3
"""
Update Checker for claudekit-engineer.
Checks for new commits/skills in the claudekit-engineer repository.
"""

import sys
import os
import subprocess
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SHA_FILE = Path(".md/claudekit_last_sha.txt")
REMOTE_URL = "https://github.com/claudekit/claudekit-engineer"


def get_local_sha() -> str:
    """Get the recorded SHA or the current local clone's head commit."""
    if SHA_FILE.exists():
        return SHA_FILE.read_text(encoding="utf-8").strip()
    
    # Try getting it from the local git clone if it exists
    clone_dir = Path("claudekit-engineer")
    if clone_dir.exists() and (clone_dir / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(clone_dir),
                capture_output=True,
                text=True,
                check=True
            )
            sha = res.stdout.strip()
            # Save it
            SHA_FILE.write_text(sha, encoding="utf-8")
            return sha
        except subprocess.SubprocessError:
            pass
    return ""


def get_remote_sha() -> str:
    """Query git ls-remote for the remote repository head commit."""
    try:
        res = subprocess.run(
            ["git", "ls-remote", REMOTE_URL, "refs/heads/main"],
            capture_output=True,
            text=True,
            check=True
        )
        output = res.stdout.strip()
        if output:
            return output.split()[0]
    except subprocess.SubprocessError:
        pass
    return ""


def main():
    print("[ClaudeKit Update Check] Checking remote repository for new updates...")
    
    local_sha = get_local_sha()
    remote_sha = get_remote_sha()
    
    if not remote_sha:
        print("[ClaudeKit Update Check] Warning: Could not connect to remote repository.")
        sys.exit(0)
        
    if not local_sha:
        # First time checking
        print(f"[ClaudeKit Update Check] Initializing tracker with remote SHA: {remote_sha}")
        SHA_FILE.write_text(remote_sha, encoding="utf-8")
        sys.exit(0)
        
    if local_sha != remote_sha:
        print("\n\x1b[33m[UPDATE AVAILABLE]\x1b[0m New updates found in claudekit-engineer!")
        print(f"  - Local SHA:  {local_sha[:8]}")
        print(f"  - Remote SHA: {remote_sha[:8]}")
        print("  - Action: Run `git pull` inside `claudekit-engineer/` to see new skills/updates,")
        print("            then re-run the architectural study to evaluate additions.\n")
    else:
        print("[ClaudeKit Update Check] System is up-to-date with remote claudekit-engineer repository.")


if __name__ == "__main__":
    main()
