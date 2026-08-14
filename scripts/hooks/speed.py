"""Test Execution Speed Guard Hook for CCBA Lifecycle.

Monitors test execution speed of test files and warns if any unit test
exceeds 2.0s without @pytest.mark.slow or @pytest.mark.stress decorators.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from scripts.eval.process_safety import get_venv_python

from .base import BaseHook, HookContext, HookResult


class TestSpeedHook(BaseHook):
    """Guards against test performance regressions in the fast daily loop (< 2.0s)."""

    __test__ = False
    name = "test_speed_guard"
    supported_events = ("post-tool", "pre-tool")

    def __init__(self, max_fast_seconds: float = 2.0, strict: bool = False):
        self.max_fast_seconds = max_fast_seconds
        self.strict = strict

    @staticmethod
    def has_slow_marker(file_path: Path) -> bool:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return "pytest.mark.slow" in content or "pytest.mark.stress" in content
        except Exception:
            return False

    def check_test_file_speed(self, test_file: Path, project_root: Path) -> tuple[bool, float, str]:
        if self.has_slow_marker(test_file):
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

            tagged_slow = self.has_slow_marker(test_file)
            if duration > self.max_fast_seconds and not tagged_slow:
                warning_msg = (
                    f"⚠️ [TestSpeedGuard Warning] '{test_file.name}' took {duration:.2f}s "
                    f"(> {self.max_fast_seconds}s threshold) but lacks @pytest.mark.slow decorator!"
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

    @staticmethod
    def get_modified_test_files(project_root: Path) -> list[Path]:
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

    def execute(self, context: HookContext) -> HookResult:
        project_root = Path(context.cwd or Path(__file__).resolve().parents[2])

        targets: list[Path] = []
        if context.path:
            p = Path(context.path)
            if not p.is_absolute():
                p = project_root / p
            if p.exists() and p.name.startswith("test_") and p.suffix == ".py":
                targets.append(p)
        else:
            targets = self.get_modified_test_files(project_root)

        if not targets:
            return HookResult(
                name=self.name,
                exit_code=0,
                message="No modified test files to check.",
            )

        warnings_count = 0
        results_list = []
        for tf in targets:
            ok, duration, msg = self.check_test_file_speed(tf, project_root)
            results_list.append({"file": str(tf.name), "duration": duration, "message": msg})
            if not ok:
                warnings_count += 1
                print(f"  {msg}")
            else:
                print(f"  ✅ '{tf.name}' passed speed check ({duration:.2f}s)")

        exit_code = 1 if (warnings_count > 0 and self.strict) else 0
        return HookResult(
            name=self.name,
            exit_code=exit_code,
            message=f"Checked {len(targets)} test file(s) ({warnings_count} warnings)",
            details={"results": results_list, "warnings_count": warnings_count},
        )
