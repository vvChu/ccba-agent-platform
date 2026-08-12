#!/usr/bin/env python3
"""test_speed_guard.py - Pre-commit Hook & Linter for Test Execution Speed.

Monitors test execution speed of modified test files.
Warns if any unit test file takes > 2.0s to execute without having
@pytest.mark.slow or @pytest.mark.stress decorators applied.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from scripts.eval.process_safety import get_venv_python


def has_slow_marker(file_path: Path) -> bool:
    """Checks whether a test file contains pytest slow/stress markers."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return "pytest.mark.slow" in content or "pytest.mark.stress" in content
    except Exception:
        return False


def check_test_file_speed(
    test_file: Path, project_root: Path, max_fast_seconds: float = 2.0
) -> tuple[bool, float, str]:
    """Runs pytest on a single test file and checks if it exceeds threshold without marker."""
    if has_slow_marker(test_file):
        return True, 0.0, f"⏩ '{test_file.name}' is tagged slow/stress (Skipped speed check)"

    python_exe = get_venv_python(project_root)
    cmd = [python_exe, "-m", "pytest", str(test_file), "-q", "--maxfail=1"]

    start_time = time.perf_counter()
    try:
        res = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=15.0,
        )
        duration = time.perf_counter() - start_time
        success = res.returncode == 0

        tagged_slow = has_slow_marker(test_file)
        if duration > max_fast_seconds and not tagged_slow:
            warning_msg = (
                f"⚠️ [TestSpeedGuard Warning] '{test_file.name}' took {duration:.2f}s "
                f"(> {max_fast_seconds}s threshold) but lacks @pytest.mark.slow decorator!"
            )
            return False, duration, warning_msg

        return success, duration, "OK"
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start_time
        return (
            False,
            duration,
            f"⚠️ [TestSpeedGuard TIMEOUT] '{test_file.name}' timed out after {duration:.2f}s!",
        )
    except Exception as e:
        duration = time.perf_counter() - start_time
        return False, duration, f"❌ [TestSpeedGuard Error] '{test_file.name}': {e}"


def get_modified_test_files(project_root: Path) -> list[Path]:
    """Finds modified test files via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        modified: list[Path] = []
        for line in res.stdout.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                filepath = project_root / parts[1].strip()
                if (
                    filepath.suffix == ".py"
                    and filepath.exists()
                    and filepath.name.startswith("test_")
                ):
                    modified.append(filepath)
        return modified
    except Exception:
        return []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    project_root = Path(__file__).parent.parent.parent.resolve()

    parser = argparse.ArgumentParser(
        description="CCBA Test Execution Speed Guard Linter/Hook."
    )
    parser.add_argument("files", nargs="*", help="Specific test file(s) to check.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Max allowed execution duration (seconds) for fast tests. Default: 2.0s",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any test exceeds threshold without @pytest.mark.slow.",
    )

    args = parser.parse_args()

    targets: list[Path] = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if not p.is_absolute():
                p = project_root / p
            if p.exists() and p.name.startswith("test_"):
                targets.append(p)
    else:
        targets = get_modified_test_files(project_root)

    if not targets:
        print("🛡️ [TestSpeedGuard] No modified test files to check.")
        return 0

    print(f"🛡️ [TestSpeedGuard] Checking {len(targets)} test file(s) for speed compliance...")
    warnings_count = 0

    for tf in targets:
        ok, duration, msg = check_test_file_speed(
            tf, project_root, max_fast_seconds=args.threshold
        )
        if not ok:
            warnings_count += 1
            print(f"  {msg}")
        else:
            print(f"  ✅ '{tf.name}' passed speed check ({duration:.2f}s)")

    if warnings_count > 0 and args.strict:
        print(f"\n❌ [TestSpeedGuard Strict] {warnings_count} test file(s) failed speed check.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
