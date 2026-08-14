"""Session Initialization Hook for CCBA Lifecycle.

Initializes session parameters, detects workspace repository status,
and ensures knowledge base directory structures exist.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .base import BaseHook, HookContext, HookResult


class SessionInitHook(BaseHook):
    """Initializes workspace context on session startup."""

    name = "session_init"
    supported_events = ("session-init",)

    def execute(self, context: HookContext) -> HookResult:
        print("[session-init] Initializing workspace context...")
        cwd = Path(context.cwd or Path.cwd())

        # 1. Detect Git Root
        git_root = None
        git_branch = None
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            git_root = res.stdout.strip()
        except subprocess.SubprocessError:
            pass

        print(f"[session-init] Current Directory: {cwd}")
        if git_root:
            print(f"[session-init] Git Repository Root: {git_root}")
            try:
                branch_res = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                git_branch = branch_res.stdout.strip()
                print(f"[session-init] Active Git Branch: {git_branch}")
            except subprocess.SubprocessError:
                pass
        else:
            print("[session-init] Warning: Not inside a Git repository.")

        # 2. Create .md directory if missing (Global Rule 1)
        kb_dir = cwd / ".md"
        if not kb_dir.exists():
            try:
                kb_dir.mkdir(exist_ok=True)
                (kb_dir / "extracted_docs").mkdir(exist_ok=True)
                print(f"[session-init] Created central Knowledge Base folder: {kb_dir}")
            except Exception as e:
                print(f"[session-init] Error creating .md directory: {e}")

        # 3. Trigger ClaudeKit update checker if available
        checker_script = (
            Path(__file__).resolve().parents[1] / "spoke" / "check_claudekit_updates.py"
        )
        if checker_script.exists():
            try:
                subprocess.Popen([sys.executable, str(checker_script)])
            except Exception:
                pass

        return HookResult(
            name=self.name,
            exit_code=0,
            message="Session initialization completed successfully.",
            details={"git_root": git_root, "git_branch": git_branch, "cwd": str(cwd)},
        )
