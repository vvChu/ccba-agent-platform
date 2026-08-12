#!/usr/bin/env python3
"""safe_pytest.py - Auto-Wrapper CLI Script for Scoped Pytest Execution.

Discovers target test files (from args or git status) and runs pytest
via safe_runner.py in a detached background process to prevent daemon cancellations.
"""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def find_modified_test_files() -> list[str]:
    """Finds modified or newly added test files via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        test_files: list[str] = []
        for line in res.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.strip().split(maxsplit=1)
            if len(parts) < 2:
                continue
            filepath = parts[1].strip()
            path_obj = Path(filepath)
            if path_obj.suffix == ".py" and (
                path_obj.name.startswith("test_") or "tests" in path_obj.parts
            ):
                if path_obj.exists():
                    test_files.append(str(path_obj))
        return test_files
    except Exception as e:
        sys.stderr.write(f"[SafePytest Warning] Could not check git status: {e}\n")
        return []


def main() -> int:
    """Main CLI entry point for safe_pytest."""
    parser = argparse.ArgumentParser(description="Safe Pytest Runner Wrapper for CCBA Platform")
    parser.add_argument("-f", "--file", type=str, help="Specific test file or pattern to run")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned runner command without executing",
    )
    parser.add_argument(
        "--allow-unscoped",
        action="store_true",
        help="Allow running pytest across entire workspace",
    )
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional pytest options")

    args = parser.parse_args()

    targets: list[str] = []
    if args.file:
        targets.append(args.file)
    elif args.extra_args and any(not a.startswith("-") for a in args.extra_args):
        pass
    else:
        git_targets = find_modified_test_files()
        if git_targets:
            targets.extend(git_targets)
            print(f"[SafePytest] Auto-detected modified test files: {', '.join(targets)}")

    python_exec = sys.executable
    cmd_parts = [python_exec, "-m", "pytest", "--maxfail=1"]

    target_has_slow = False
    for t in targets:
        try:
            p = Path(t)
            if p.exists() and ("pytest.mark.slow" in p.read_text(encoding="utf-8", errors="ignore")):
                target_has_slow = True
                break
        except Exception:
            pass

    if not any(a.startswith("-m") for a in args.extra_args) and not target_has_slow:
        cmd_parts.extend(["-m", "not slow"])

    if args.allow_unscoped:
        cmd_parts.append("--allow-unscoped")

    if targets:
        cmd_parts.extend(targets)

    def safe_quote(arg: str) -> str:
        if sys.platform.startswith("win"):
            return f'"{arg}"' if (" " in arg or "\t" in arg) else arg
        return shlex.quote(arg)

    cmd_str = " ".join(safe_quote(p) for p in cmd_parts)
    safe_runner_script = Path(__file__).parent / "safe_runner.py"

    full_runner_cmd = f'"{python_exec}" "{safe_runner_script}" --command "{cmd_str}"'

    if args.dry_run:
        print(f"[SafePytest DRY-RUN] Planned execution:\n  {full_runner_cmd}")
        return 0

    print(f"[SafePytest] Executing detached runner:\n  Command: {cmd_str}")
    res = subprocess.run([python_exec, str(safe_runner_script), "--command", cmd_str])
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
