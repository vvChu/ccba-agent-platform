"""verifier.py - Deterministic Verification Gate for Patches and Test Runners.

Provides machine-evaluated exit-code verification to eliminate AI Agent Premature
Completion and Self-Certification (ADR-0035, ADR-0057, P0.2 Wayfinder Milestone).

Supports:
- Sequential command execution with millisecond timing.
- Safe timeout handling and error snippet extraction.
- Cross-platform subprocess execution (Windows, Linux, macOS).
- Markdown & JSON reporting for CI/CD gates and Antigravity artifacts.
"""

from __future__ import annotations

import subprocess
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    """Execution outcome for a single CLI command."""

    command: str
    exit_code: int
    passed: bool
    duration_ms: float
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to JSON-serializable dictionary."""
        return asdict(self)


@dataclass
class PatchVerificationReport:
    """Aggregated verification report across multiple commands."""

    all_passed: bool
    total_commands: int
    passed_count: int
    failed_count: int
    total_duration_ms: float
    results: list[CommandResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return {
            "all_passed": self.all_passed,
            "total_commands": self.total_commands,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "results": [r.to_dict() for r in self.results],
        }

    def to_markdown(self) -> str:
        """Render report as a clean GitHub-Flavored Markdown document."""
        status_badge = "✅ ALL PASSED" if self.all_passed else "❌ VERIFICATION FAILED"
        lines: list[str] = [
            f"# 🛡️ Deterministic Patch Verification Report: {status_badge}",
            "",
            f"- **Overall Status:** {'PASS' if self.all_passed else 'FAIL'}",
            f"- **Commands Executed:** {self.passed_count}/{self.total_commands} passed",
            f"- **Total Duration:** {self.total_duration_ms:.1f} ms",
            "",
            "## Command Execution Details",
            "",
            "| Status | Exit Code | Duration | Command |",
            "| :---: | :---: | :---: | :--- |",
        ]

        for r in self.results:
            st = "PASS" if r.passed else ("TIMEOUT" if r.timed_out else "FAIL")
            lines.append(
                f"| {st} | {r.exit_code} | {r.duration_ms:.1f}ms | `{r.command}` |"
            )

        # Add error details if any failed
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            lines.extend(["", "## Failure Diagnostics", ""])
            for f in failed_results:
                lines.append(f"### ❌ Command: `{f.command}`")
                lines.append(f"- **Exit Code:** {f.exit_code}")
                if f.timed_out:
                    lines.append(f"- **Timeout:** Command timed out after {f.duration_ms:.1f}ms")
                if f.error_message:
                    lines.append(f"- **Error:** {f.error_message}")
                if f.stderr.strip():
                    lines.extend([
                        "- **Stderr Snippet:**",
                        "```text",
                        f.stderr.strip()[:1000],
                        "```",
                    ])
                elif f.stdout.strip():
                    lines.extend([
                        "- **Stdout Snippet:**",
                        "```text",
                        f.stdout.strip()[:1000],
                        "```",
                    ])
                lines.append("")

        return "\n".join(lines).strip() + "\n"


def _execute_single_command(
    command: str,
    cwd: Path | str | None,
    timeout: float,
) -> CommandResult:
    """Execute a single shell command and return its structured CommandResult."""
    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return CommandResult(
            command=command,
            exit_code=proc.returncode,
            passed=(proc.returncode == 0),
            duration_ms=round(duration_ms, 2),
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        stdout_text = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr_text = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return CommandResult(
            command=command,
            exit_code=124,
            passed=False,
            duration_ms=round(duration_ms, 2),
            stdout=stdout_text,
            stderr=stderr_text,
            timed_out=True,
            error_message=f"Command exceeded timeout limit of {timeout}s",
        )
    except Exception as err:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return CommandResult(
            command=command,
            exit_code=1,
            passed=False,
            duration_ms=round(duration_ms, 2),
            error_message=str(err),
        )


def verify_patch_execution(
    commands: Sequence[str],
    cwd: Path | str | None = None,
    timeout: float = 60.0,
    fail_fast: bool = False,
) -> PatchVerificationReport:
    """Execute a sequence of verification commands and aggregate into a report.

    Args:
        commands: List of shell command strings to execute.
        cwd: Working directory for command execution.
        timeout: Maximum execution timeout per command in seconds.
        fail_fast: If True, stop executing remaining commands upon first failure.

    Returns:
        PatchVerificationReport containing all execution details and summary.
    """
    results: list[CommandResult] = []
    total_duration_ms = 0.0

    for cmd in commands:
        cleaned_cmd = cmd.strip()
        if not cleaned_cmd:
            continue

        res = _execute_single_command(cleaned_cmd, cwd=cwd, timeout=timeout)
        results.append(res)
        total_duration_ms += res.duration_ms

        if fail_fast and not res.passed:
            break

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    all_passed = (failed_count == 0) and (len(results) > 0)

    return PatchVerificationReport(
        all_passed=all_passed,
        total_commands=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        total_duration_ms=round(total_duration_ms, 2),
        results=results,
    )
