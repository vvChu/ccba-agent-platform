#!/usr/bin/env python3
"""Session Cleanup Utility for CCBA Agent Platform.

Automates the cleanup of merged git branches, stale worktrees, and
distribution of raw input documents from input_documents/.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Core branches that must NEVER be deleted
CORE_BRANCHES = {"main", "master", "develop"}


def run_cmd(args: list[str], check: bool = True) -> str:
    """Run a system command and return its stdout, stripped."""
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=check, encoding="utf-8")
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(args)}: {e.stderr.strip()}", file=sys.stderr)
        if check:
            raise
        return ""


def clean_worktrees() -> None:
    """Prune and remove force subagent or teamwork worktrees."""
    print("[CLEAN] Cleaning git worktrees...")
    raw_list = run_cmd(["git", "worktree", "list"])
    if not raw_list:
        return

    worktrees = []
    for line in raw_list.splitlines():
        if not line.strip():
            continue
        # Format: <path> <hash> [<branch>]
        parts = line.split()
        if parts:
            worktrees.append(parts[0])

    # Skip the first one which is always the main workspace
    if len(worktrees) <= 1:
        print("  No extra worktrees found.")
        return

    main_wt = os.path.normpath(worktrees[0])
    for wt in worktrees[1:]:
        wt_norm = os.path.normpath(wt)
        if wt_norm == main_wt:
            continue

        wt_name = Path(wt_norm).name
        # Check if it belongs to a subagent or teamwork preview
        is_subagent = (
            "subagent-" in wt_name
            or "teamwork-preview-" in wt_name
            or ".system_generated/worktrees" in wt_norm.replace("\\", "/")
            or "AppData" in wt_norm
        )

        if is_subagent:
            print(f"  Removing worktree: {wt_norm}")
            run_cmd(["git", "worktree", "remove", "--force", wt_norm], check=False)

    run_cmd(["git", "worktree", "prune"], check=False)


def clean_branches() -> None:
    """Find and delete local and remote branches that are already merged (0 commits ahead of main)."""
    print("[CLEAN] Cleaning merged git branches...")
    run_cmd(["git", "fetch", "--prune"], check=False)

    # Get active branch
    active_branch = run_cmd(["git", "branch", "--show-current"])

    # Get all local branches
    raw_branches = run_cmd(["git", "branch"])
    branches = []
    for line in raw_branches.splitlines():
        # Remove active branch marker (*) or subagent worktree lock marker (+)
        b = line.strip().lstrip("*+ ").strip()
        if b and b not in CORE_BRANCHES and b != active_branch:
            branches.append(b)

    if not branches:
        print("  No merged/redundant branches to clean.")
        return

    for b in branches:
        # Check if the branch has any unique commits vs main
        # If output is empty, it means 0 commits ahead
        ahead_commits = run_cmd(["git", "log", "main.." + b, "--oneline"], check=False)
        if not ahead_commits:
            print(f"  Branch '{b}' is already merged/redundant.")
            # Delete local branch
            print(f"    - Deleting local: {b}")
            run_cmd(["git", "branch", "-D", b], check=False)

            # Check if remote branch exists and delete it
            has_remote = run_cmd(["git", "ls-remote", "--heads", "origin", b], check=False)
            if has_remote:
                print(f"    - Deleting remote: origin/{b}")
                # We do not fail the whole process if network is slow/timeout
                run_cmd(["git", "push", "origin", "--delete", b], check=False)
        else:
            # Check how many commits behind/ahead
            behind_count = len(
                run_cmd(["git", "log", f"{b}..main", "--oneline"], check=False).splitlines()
            )
            ahead_count = len(ahead_commits.splitlines())
            print(
                f"  Branch '{b}' has active changes: {ahead_count} ahead, {behind_count} behind main. Skipping."
            )


def distribute_input_documents(root_dir: Path) -> None:
    """Scan and distribute files in input_documents/ into correct .md/ structure."""
    input_dir = root_dir / "input_documents"
    if not input_dir.exists():
        return

    files = [f for f in input_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]
    if not files:
        print("[FILES] No new input documents to distribute.")
        return

    print("[FILES] Processing input documents...")
    # Target directories
    md_dir = root_dir / ".md"
    legal_dir = md_dir / "legal_docs"
    knowledge_dir = md_dir / "knowledge"
    scratch_dir = md_dir / "scratch"
    data_dir = md_dir / "data"
    seminar_dir = md_dir / "seminars"

    # Ensure target dirs exist
    for d in (legal_dir, knowledge_dir, scratch_dir, data_dir, seminar_dir):
        d.mkdir(parents=True, exist_ok=True)

    for f in files:
        ext = f.suffix.lower()
        name = f.name.lower()

        # Classification logic
        if ext in (".pdf", ".docx", ".doc") or any(
            k in name for k in ("luat", "nd", "tt", "qd", "legal", "law")
        ):
            dest = legal_dir / f.name
        elif ext in (".py", ".sh", ".ps1", ".bat"):
            dest = scratch_dir / f.name
        elif ext in (".json", ".csv", ".yaml", ".yml"):
            dest = data_dir / f.name
        elif "seminar" in name or "meeting" in name or "bien_ban" in name:
            dest = seminar_dir / f.name
        else:
            # Default to knowledge
            dest = knowledge_dir / f.name

        print(f"  [MOVE] {f.relative_to(root_dir)} -> {dest.relative_to(root_dir)}")
        try:
            shutil.move(str(f), str(dest))
        except Exception as e:
            print(f"  Failed to move {f.name}: {e}", file=sys.stderr)


def main() -> None:
    # Resolve workspace root
    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.parent

    # Fix stdout encoding to UTF-8 on Windows if supported
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("==================================================")
    print("[START] Running Session Cleanup Automation...")
    print("==================================================")

    distribute_input_documents(root_dir)
    clean_worktrees()
    clean_branches()

    print("==================================================")
    print("[SUCCESS] Cleanup process completed successfully.")
    print("==================================================")


if __name__ == "__main__":
    main()
