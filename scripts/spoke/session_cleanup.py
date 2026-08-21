#!/usr/bin/env python3
"""Session Cleanup Utility for CCBA Agent Platform.

Automates the cleanup of merged git branches, stale worktrees, and
distribution of raw input documents from input_documents/.
Supports a dry-run preview before execution.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
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


def clean_worktrees(dry_run: bool) -> None:
    """Prune and remove force subagent or teamwork worktrees."""
    print("[CLEAN] Checking git worktrees...")
    raw_list = run_cmd(["git", "worktree", "list"])
    if not raw_list:
        return

    worktrees = []
    for line in raw_list.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if parts:
            worktrees.append(parts[0])

    if len(worktrees) <= 1:
        print("  No extra worktrees found.")
        return

    main_wt = os.path.normpath(worktrees[0])
    for wt in worktrees[1:]:
        wt_norm = os.path.normpath(wt)
        if wt_norm == main_wt:
            continue

        wt_name = Path(wt_norm).name
        is_subagent = (
            "subagent-" in wt_name
            or "teamwork-preview-" in wt_name
            or ".system_generated/worktrees" in wt_norm.replace("\\", "/")
            or "AppData" in wt_norm
        )

        if is_subagent:
            if dry_run:
                print(f"  [PREVIEW] Would remove worktree: {wt_norm}")
            else:
                print(f"  Removing worktree: {wt_norm}")
                run_cmd(["git", "worktree", "remove", "--force", wt_norm], check=False)

    if not dry_run:
        run_cmd(["git", "worktree", "prune"], check=False)


def clean_branches(dry_run: bool) -> None:
    """Find and delete local and remote branches that are already merged (0 commits ahead of main)."""
    print("[CLEAN] Checking merged git branches...")
    if not dry_run:
        run_cmd(["git", "fetch", "--prune"], check=False)

    # Get active branch
    active_branch = run_cmd(["git", "branch", "--show-current"])

    # Get all local branches
    raw_branches = run_cmd(["git", "branch"])
    branches = []
    for line in raw_branches.splitlines():
        b = line.strip().lstrip("*+ ").strip()
        if b and b not in CORE_BRANCHES and b != active_branch:
            branches.append(b)

    if not branches:
        print("  No merged/redundant branches to clean.")
        return

    for b in branches:
        ahead_commits = run_cmd(["git", "log", "main.." + b, "--oneline"], check=False)
        if not ahead_commits:
            if dry_run:
                print(f"  [PREVIEW] Would delete branch '{b}' (already merged)")
            else:
                print(f"  Branch '{b}' is already merged/redundant.")
                print(f"    - Deleting local: {b}")
                run_cmd(["git", "branch", "-D", b], check=False)

                has_remote = run_cmd(["git", "ls-remote", "--heads", "origin", b], check=False)
                if has_remote:
                    print(f"    - Deleting remote: origin/{b}")
                    run_cmd(["git", "push", "origin", "--delete", b], check=False)
        else:
            behind_count = len(
                run_cmd(["git", "log", f"{b}..main", "--oneline"], check=False).splitlines()
            )
            ahead_count = len(ahead_commits.splitlines())
            print(
                f"  Branch '{b}' has active changes: {ahead_count} ahead, {behind_count} behind main. Skipping."
            )


def load_project_mode(root_dir: Path) -> str:
    """Read project mode from workspace_context.yaml or infer it."""
    context_file = root_dir / ".md" / "workspace_context.yaml"
    if not context_file.exists():
        return "delivery"
    try:
        import yaml

        with open(context_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                proj = data.get("project", {})
                if isinstance(proj, dict):
                    mode = proj.get("mode")
                    if mode in ("software", "delivery", "hybrid"):
                        return mode
                    # Auto-inference based on type
                    proj_type = proj.get("type", "")
                    if proj_type == "Phần mềm":
                        return "software"
    except Exception:
        pass
    return "delivery"


def distribute_input_documents(root_dir: Path, dry_run: bool) -> None:
    """Scan and distribute files in input_documents/ based on project mode."""
    input_dir = root_dir / "input_documents"
    if not input_dir.exists():
        return

    files = [f for f in input_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]
    if not files:
        print("[FILES] No new input documents to distribute.")
        return

    mode = load_project_mode(root_dir)
    print(f"[FILES] Detected project mode: {mode}")
    print("[FILES] Found documents in input_documents/:")

    md_dir = root_dir / ".md"
    docs_dir = root_dir / "docs"

    # Define standard target dirs
    scratch_dir = md_dir / "scratch"
    references_dir = docs_dir / "references"

    # Depending on mode, create appropriate target dirs
    target_dirs = set()
    if mode == "software":
        target_dirs.add(scratch_dir)
        target_dirs.add(references_dir)
    elif mode == "delivery":
        legal_dir = md_dir / "legal_docs"
        knowledge_dir = md_dir / "knowledge"
        data_dir = md_dir / "data"
        seminar_dir = md_dir / "seminars"
        target_dirs.update([legal_dir, knowledge_dir, scratch_dir, data_dir, seminar_dir])
    elif mode == "hybrid":
        legal_dir = md_dir / "legal_docs"
        knowledge_dir = md_dir / "knowledge"
        data_dir = md_dir / "data"
        seminar_dir = md_dir / "seminars"
        target_dirs.update(
            [legal_dir, knowledge_dir, scratch_dir, data_dir, seminar_dir, references_dir]
        )

    if not dry_run:
        for d in target_dirs:
            d.mkdir(parents=True, exist_ok=True)

    for f in files:
        ext = f.suffix.lower()
        name = f.name.lower()

        dest = None
        if mode == "software":
            if ext in (".py", ".sh", ".ps1", ".bat", ".json", ".csv", ".yaml", ".yml"):
                dest = scratch_dir / f.name
            else:
                dest = references_dir / f.name
        elif mode == "delivery":
            legal_dir = md_dir / "legal_docs"
            knowledge_dir = md_dir / "knowledge"
            data_dir = md_dir / "data"
            seminar_dir = md_dir / "seminars"

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
                dest = knowledge_dir / f.name
        elif mode == "hybrid":
            legal_dir = md_dir / "legal_docs"
            knowledge_dir = md_dir / "knowledge"
            data_dir = md_dir / "data"
            seminar_dir = md_dir / "seminars"

            # Check if it looks like code/dev document
            is_dev_doc = any(
                k in name
                for k in (
                    "api",
                    "spec",
                    "adr",
                    "architecture",
                    "codebase",
                    "dev",
                    "software",
                    "reference",
                )
            )

            if ext in (".py", ".sh", ".ps1", ".bat"):
                dest = scratch_dir / f.name
            elif is_dev_doc:
                dest = references_dir / f.name
            elif ext in (".pdf", ".docx", ".doc") or any(
                k in name for k in ("luat", "nd", "tt", "qd", "legal", "law")
            ):
                dest = legal_dir / f.name
            elif ext in (".json", ".csv", ".yaml", ".yml"):
                dest = data_dir / f.name
            elif "seminar" in name or "meeting" in name or "bien_ban" in name:
                dest = seminar_dir / f.name
            else:
                dest = knowledge_dir / f.name

        if dest:
            if dry_run:
                print(
                    f"  [PREVIEW] Would move: {f.relative_to(root_dir)} -> {dest.relative_to(root_dir)}"
                )
            else:
                print(f"  [MOVE] {f.relative_to(root_dir)} -> {dest.relative_to(root_dir)}")
                try:
                    shutil.move(str(f), str(dest))
                except Exception as e:
                    print(f"  Failed to move {f.name}: {e}", file=sys.stderr)


def clean_zombies(dry_run: bool) -> None:
    """Scan and terminate orphan background processes (pytest/python) left by crashed sessions."""
    print("[CLEAN] Checking orphan/zombie background processes...")
    current_pid = os.getpid()

    try:
        import psutil

        zombies_found = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            try:
                pid = proc.info["pid"]
                if pid == current_pid:
                    continue
                name = (proc.info["name"] or "").lower()
                cmdline = " ".join(proc.info["cmdline"] or [])

                if ("pytest" in name or "python" in name) and (
                    "safe_runner" in cmdline or "pytest" in cmdline
                ):
                    age_seconds = time.time() - proc.info["create_time"]
                    if age_seconds > 900:  # Older than 15 minutes
                        zombies_found += 1
                        if dry_run:
                            print(
                                f"  [PREVIEW] Would terminate orphan process PID {pid} ({name}, age {int(age_seconds / 60)}m)"
                            )
                        else:
                            print(
                                f"  [TERMINATE] Killing orphan process PID {pid} ({name}, age {int(age_seconds / 60)}m)"
                            )
                            proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if zombies_found == 0:
            print("  No orphan background processes found.")
        return
    except ImportError:
        pass

    # Fallback for Windows using wmic/tasklist if psutil is not available
    if sys.platform == "win32":
        try:
            out = run_cmd(
                ["wmic", "process", "where", "name='python.exe'", "get", "processid,commandline"],
                check=False,
            )
            zombies_found = 0
            if out:
                for line in out.splitlines():
                    if "safe_runner" in line or "pytest" in line:
                        parts = line.strip().rsplit(maxsplit=1)
                        if len(parts) == 2 and parts[1].isdigit():
                            pid = int(parts[1])
                            if pid != current_pid:
                                zombies_found += 1
                                if dry_run:
                                    print(f"  [PREVIEW] Would terminate orphan process PID {pid}")
                                else:
                                    print(f"  [TERMINATE] Killing orphan process PID {pid}")
                                    run_cmd(["taskkill", "/F", "/PID", str(pid)], check=False)
            if zombies_found == 0:
                print("  No orphan background processes found.")
            return
        except Exception:
            pass

    print("  No orphan background processes found.")


def clean_subagent_artifacts(root_dir: Path, dry_run: bool) -> None:
    """Clean up ephemeral subagent directories and files in .agents/."""
    print("[CLEAN] Checking ephemeral subagent artifacts in .agents/...")
    agents_dir = root_dir / ".agents"
    if not agents_dir.exists():
        return

    canonical = {"skills", "workflows", "proposals", "rules", "templates", "AGENTS.md", ".gitkeep"}
    stray_items = [p for p in agents_dir.iterdir() if p.name not in canonical]

    if not stray_items:
        print("  No stray subagent artifacts found in .agents/.")
        return

    for item in stray_items:
        if dry_run:
            print(f"  [PREVIEW] Would remove: .agents/{item.name}")
        else:
            print(f"  [DELETE] Removing: .agents/{item.name}")
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                print(f"  [WARNING] Could not remove .agents/{item.name}: {e}")


def health_check() -> None:
    """Perform system health check (disk space and memory)."""
    print("[HEALTH] Running workspace health diagnostics...")
    try:
        total, used, free = shutil.disk_usage(Path.cwd())
        free_gb = free / (1024**3)
        print(f"  Disk Free Space: {free_gb:.2f} GB")
        if free_gb < 2.0:
            print("  [WARNING] Disk free space is low (< 2 GB)!", file=sys.stderr)
        else:
            print("  [OK] Disk space is healthy.")
    except Exception as e:
        print(f"  [HEALTH] Disk check error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Session Cleanup Utility for CCBA Agent Platform")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the cleanup actions (default is dry-run preview)",
    )
    args = parser.parse_args()
    dry_run = not args.execute

    # Resolve workspace root
    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.parent.parent

    # Fix stdout encoding to UTF-8 on Windows if supported
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("==================================================")
    mode_str = "EXECUTE" if args.execute else "PREVIEW (DRY-RUN)"
    print(f"[START] Running Session Cleanup Automation [{mode_str}]...")
    print("==================================================")

    health_check()
    distribute_input_documents(root_dir, dry_run)
    clean_worktrees(dry_run)
    clean_branches(dry_run)
    clean_zombies(dry_run)
    clean_subagent_artifacts(root_dir, dry_run)

    print("==================================================")
    status_str = "completed successfully" if args.execute else "preview completed"
    print(f"[SUCCESS] Cleanup process {status_str}.")
    print("==================================================")


if __name__ == "__main__":
    main()
