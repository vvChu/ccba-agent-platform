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
            lines.append(f"| {st} | {r.exit_code} | {r.duration_ms:.1f}ms | `{r.command}` |")

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
                    lines.extend(
                        [
                            "- **Stderr Snippet:**",
                            "```text",
                            f.stderr.strip()[:1000],
                            "```",
                        ]
                    )
                elif f.stdout.strip():
                    lines.extend(
                        [
                            "- **Stdout Snippet:**",
                            "```text",
                            f.stdout.strip()[:1000],
                            "```",
                        ]
                    )
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
        stdout_text = (
            exc.stdout
            if isinstance(exc.stdout, str)
            else (exc.stdout or b"").decode("utf-8", errors="replace")
        )
        stderr_text = (
            exc.stderr
            if isinstance(exc.stderr, str)
            else (exc.stderr or b"").decode("utf-8", errors="replace")
        )
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


def verify_document_artifact(
    target_path: Path | str,
    min_bytes: int = 100,
    required_headings: Sequence[str] | None = None,
    cwd: Path | str | None = None,
) -> CommandResult:
    """Deterministically verify a document artifact's presence, size, and headings.

    Args:
        target_path: Path to the document (.md, .docx, .pdf, etc.).
        min_bytes: Minimum expected file size in bytes (default 100).
        required_headings: Optional list of heading strings that must appear.
        cwd: Base directory to resolve relative paths against.

    Returns:
        CommandResult with exit_code 0 if valid, 1 otherwise.
    """
    start_time = time.perf_counter()
    path_obj = Path(target_path)
    if not path_obj.is_absolute() and cwd:
        path_obj = (Path(cwd) / path_obj).resolve()
    else:
        path_obj = path_obj.resolve()

    cmd_display = f"verify-doc --target {target_path} --min-bytes {min_bytes}"
    if required_headings:
        cmd_display += f" --required-headings '{','.join(required_headings)}'"

    if not path_obj.exists():
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return CommandResult(
            command=cmd_display,
            exit_code=1,
            passed=False,
            duration_ms=round(duration_ms, 2),
            error_message=f"Artifact not found: {path_obj}",
        )

    if not path_obj.is_file():
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return CommandResult(
            command=cmd_display,
            exit_code=1,
            passed=False,
            duration_ms=round(duration_ms, 2),
            error_message=f"Artifact path is a directory, not a file: {path_obj}",
        )

    file_size = path_obj.stat().st_size
    if file_size < min_bytes:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return CommandResult(
            command=cmd_display,
            exit_code=1,
            passed=False,
            duration_ms=round(duration_ms, 2),
            error_message=f"Artifact size ({file_size} bytes) is below minimum threshold of {min_bytes} bytes",
        )

    if required_headings and path_obj.suffix.lower() == ".md":
        try:
            content = path_obj.read_text(encoding="utf-8", errors="replace").lower()
            missing_headings: list[str] = []
            for h in required_headings:
                h_clean = h.strip().lower()
                if h_clean and h_clean not in content:
                    missing_headings.append(h)
            if missing_headings:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return CommandResult(
                    command=cmd_display,
                    exit_code=1,
                    passed=False,
                    duration_ms=round(duration_ms, 2),
                    error_message=f"Artifact is missing required heading(s): {', '.join(missing_headings)}",
                )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return CommandResult(
                command=cmd_display,
                exit_code=1,
                passed=False,
                duration_ms=round(duration_ms, 2),
                error_message=f"Failed to read artifact content: {exc}",
            )

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    return CommandResult(
        command=cmd_display,
        exit_code=0,
        passed=True,
        duration_ms=round(duration_ms, 2),
        stdout=f"Artifact verified: {path_obj.name} ({file_size} bytes)",
    )


def resolve_preset_commands(
    preset: str,
    target: Path | str | None = None,
    min_bytes: int = 100,
    required_headings: Sequence[str] | None = None,
    python_exec: str = "python",
) -> list[str]:
    """Resolve a verification preset into deterministic command strings.

    Args:
        preset: Preset identifier ('code', 'doc', 'skill', 'adr', 'telemetry', 'ci', 'eval').
        target: Target file or directory path.
        min_bytes: Minimum bytes for 'doc' preset.
        required_headings: List of headings required for 'doc' preset.
        python_exec: Python executable name or path.

    Returns:
        List of executable command strings.
    """
    p = preset.strip().lower()
    target_str = str(target).strip() if target else ""

    if p == "code":
        cmds: list[str] = []
        if target_str:
            t_path = Path(target_str)
            src_str = (
                (t_path / "src").as_posix() + "/"
                if (t_path / "src").exists()
                else t_path.as_posix()
            )
            tests_str = (
                (t_path / "tests").as_posix() if (t_path / "tests").exists() else t_path.as_posix()
            )
            cmds.append(f"{python_exec} -m ruff check {t_path.as_posix()}")
            cmds.append(f"{python_exec} -m mypy {src_str} --follow-imports=silent")
            cmds.append(f"{python_exec} -m pytest {tests_str} -q")
        else:
            cmds.append(f"{python_exec} -m ruff check .")
            cmds.append(f"{python_exec} -m pytest tests/ -q")
        return cmds

    if p == "doc":
        if not target_str:
            raise ValueError("Preset 'doc' requires a target file path (--target <file>).")
        target_posix = Path(target_str).as_posix()
        doc_cmd = f"{python_exec} -m ccba_harness verify-doc --target {target_posix} --min-bytes {min_bytes}"
        if required_headings:
            headings_arg = ",".join(required_headings)
            doc_cmd += f' --required-headings "{headings_arg}"'
        return [doc_cmd]

    if p == "skill":
        cmds = []
        if target_str:
            t_path = Path(target_str)
            skill_file = (t_path / "SKILL.md").as_posix() if t_path.is_dir() else t_path.as_posix()
            cmds.append(
                f"{python_exec} scripts/validate_skills.py --file {skill_file} --enforce-gpi"
            )
        else:
            cmds.append(f"{python_exec} scripts/validate_skills.py --enforce-gpi")
        cmds.append(f"{python_exec} scripts/governance/compile_catalog.py --check")
        return cmds

    if p == "adr":
        return [
            f"{python_exec} -m pytest tests/governance/test_adr.py tests/governance/test_sync_adr_matrix.py -q",
        ]

    if p == "telemetry":
        cmds = [
            f"{python_exec} -m pytest packages/ccba-harness/tests/test_telemetry.py tests/governance/test_subagent_telemetry.py -q",
        ]
        if target_str:
            cmds.append(
                f"{python_exec} scripts/governance/subagent_telemetry.py budget-check {Path(target_str).as_posix()} --max-tokens 5000000"
            )
        return cmds

    if p == "ci":
        return [
            f"{python_exec} -m ruff check packages/ scripts/governance/ tests/governance/",
            f"{python_exec} -m pytest packages/ccba-harness/tests/test_telemetry.py packages/ccba-harness/tests/test_verify_patch.py tests/governance/ -q",
            f"{python_exec} scripts/validate_skills.py --enforce-gpi",
            f"{python_exec} scripts/governance/compile_catalog.py --check",
            f"{python_exec} scripts/sync_hub_adr_matrix.py --check",
        ]

    if p == "eval":
        cmds = [
            f"{python_exec} -m pytest packages/ccba-harness/tests/test_evals_engine.py packages/ccba-harness/tests/test_tuner.py -q",
        ]
        if target_str:
            if target_str.endswith(".json") or Path(target_str).is_file():
                cmds.append(f"{python_exec} -m ccba_harness eval --dataset {target_str}")
            else:
                cmds.append(f"{python_exec} -m ccba_harness eval --skill {target_str}")
        return cmds

    raise ValueError(
        f"Unknown verification preset: '{preset}'. Supported presets: 'code', 'doc', 'skill', 'adr', 'telemetry', 'ci', 'eval'."
    )


def verify_patch_execution(
    commands: Sequence[str] | None = None,
    preset: str | None = None,
    target: Path | str | None = None,
    min_bytes: int = 100,
    required_headings: Sequence[str] | None = None,
    cwd: Path | str | None = None,
    timeout: float = 120.0,
    fail_fast: bool = False,
) -> PatchVerificationReport:
    """Execute a sequence of verification commands and aggregate into a report.

    Args:
        commands: List of shell command strings to execute.
        preset: Optional preset identifier ('code', 'doc', 'skill', 'adr', 'telemetry', 'ci', 'eval').
        target: Target path when using a preset.
        min_bytes: Minimum bytes for 'doc' preset.
        required_headings: Required headings for 'doc' preset.
        cwd: Working directory for command execution.
        timeout: Maximum execution timeout per command in seconds.
        fail_fast: If True, stop executing remaining commands upon first failure.

    Returns:
        PatchVerificationReport containing all execution details and summary.
    """
    all_commands: list[str] = []

    if preset:
        preset_cmds = resolve_preset_commands(
            preset=preset,
            target=target,
            min_bytes=min_bytes,
            required_headings=required_headings,
        )
        all_commands.extend(preset_cmds)

    if commands:
        all_commands.extend(commands)

    results: list[CommandResult] = []
    total_duration_ms = 0.0

    for cmd in all_commands:
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
