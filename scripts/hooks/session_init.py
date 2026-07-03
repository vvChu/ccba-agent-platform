"""
Hook script for session-init lifecycle event.
Initializes session parameters and logs environment context.
"""

import subprocess
import sys
from pathlib import Path


def main(event: str, payload: dict) -> int:
    print("[session-init] Initializing workspace context...")
    cwd = Path.cwd()

    # 1. Detect Git Root
    git_root = None
    try:
        res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        git_root = res.stdout.strip()
    except subprocess.SubprocessError:
        pass

    # 2. Log workspace properties
    project_name = cwd.name
    print(f"[session-init] Current Directory: {cwd}")
    if git_root:
        print(f"[session-init] Git Repository Root: {git_root}")
        # Detect Git branch
        try:
            branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
            print(f"[session-init] Active Git Branch: {branch_res.stdout.strip()}")
        except subprocess.SubprocessError:
            pass
    else:
        print("[session-init] Warning: Not inside a Git repository.")

    # 3. Create .md directory if missing (Global Rule 1)
    kb_dir = cwd / ".md"
    if not kb_dir.exists():
        try:
            kb_dir.mkdir(exist_ok=True)
            (kb_dir / "extracted_docs").mkdir(exist_ok=True)
            print(f"[session-init] Created central Knowledge Base folder: {kb_dir}")
        except Exception as e:
            print(f"[session-init] Error creating .md directory: {e}")

    # 4. Trigger ClaudeKit update checker
    checker_script = Path(__file__).parent.parent / "check_claudekit_updates.py"
    if checker_script.exists():
        try:
            subprocess.Popen([sys.executable, str(checker_script)])
        except Exception:
            pass

    return 0
