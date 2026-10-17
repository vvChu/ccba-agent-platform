"""sandbox.py - Executable Docker Sandbox Evaluation for Coding Archetype (TICKET-007).

Provides hermetic, isolated container-based evaluation for agent-generated code
using ephemeral Docker containers with strict resource limits, network disabled,
and automatic fallback for environments where Docker daemon is inaccessible.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import EvalItem, ScoreResult
from .scorers import BaseScorer

logger = logging.getLogger("ccba.eval.sandbox")


@dataclass
class SandboxConfig:
    """Configuration for Docker sandbox evaluation environment."""

    image: str = "python:3.11-alpine"
    timeout_seconds: float = 15.0
    memory_limit: str = "256m"
    cpus: float = 1.0
    network_disabled: bool = True
    allow_fallback: bool = True


@dataclass
class SandboxExecutionResult:
    """Outcome of sandbox code execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timeout_triggered: bool = False
    is_fallback: bool = False
    error_message: str | None = None

    @property
    def passed(self) -> bool:
        """Indicates whether execution completed cleanly with 0 exit code."""
        return self.exit_code == 0 and not self.timeout_triggered


def extract_code_blocks(text: str, language: str = "python") -> list[str]:
    """Extracts code blocks matching language fence from markdown text."""
    pattern = re.compile(
        rf"```(?:{language}|py)\b\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if matches:
        return [m.strip() for m in matches if m.strip()]

    # Fallback: Check for generic code blocks if python keyword was omitted
    generic_pattern = re.compile(r"```\n(.*?)```", re.DOTALL)
    generic_matches = generic_pattern.findall(text)
    if generic_matches:
        return [m.strip() for m in generic_matches if m.strip()]

    # If text itself appears to be raw Python code
    if any(kw in text for kw in ["def ", "class ", "import ", "return "]) and "```" not in text:
        return [text.strip()]

    return []


class DockerSandboxRunner:
    """Executes code in ephemeral Docker containers or localized fallback sandbox."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()
        self._docker_available: bool | None = None

    def is_docker_available(self) -> bool:
        """Verifies if docker CLI and daemon are operational."""
        if self._docker_available is not None:
            return self._docker_available

        docker_path = shutil.which("docker")
        if not docker_path:
            self._docker_available = False
            return False

        try:
            res = subprocess.run(
                [docker_path, "info"],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
            )
            self._docker_available = res.returncode == 0
        except Exception as e:
            logger.warning(f"Docker availability check failed: {e}")
            self._docker_available = False

        return self._docker_available

    def execute(
        self,
        code: str,
        test_code: str,
        custom_command: str | None = None,
    ) -> SandboxExecutionResult:
        """Executes code against test_code inside an isolated container."""
        if not self.is_docker_available() and not self.config.allow_fallback:
            return SandboxExecutionResult(
                exit_code=127,
                stdout="",
                stderr="Docker daemon is unavailable and fallback execution is disabled.",
                duration_ms=0.0,
                error_message="Docker unavailable",
            )

        if not self.is_docker_available():
            logger.info("Docker daemon not reachable; executing via localized fallback sandbox.")
            return self._execute_fallback(code, test_code, custom_command)

        return self._execute_docker(code, test_code, custom_command)

    def _build_docker_cmd(self, tmp_path: Path, custom_command: str | None) -> list[str]:
        run_cmd = custom_command or "python3 -m unittest test_solution.py"
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            f"--memory={self.config.memory_limit}",
            f"--cpus={self.config.cpus}",
            "-v",
            f"{tmp_path.resolve()}:/workspace:ro",
            "-w",
            "/workspace",
        ]
        if self.config.network_disabled:
            docker_cmd.extend(["--network", "none"])
        docker_cmd.extend([self.config.image, "sh", "-c", run_cmd])
        return docker_cmd

    def _build_timeout_result(
        self,
        exc: subprocess.TimeoutExpired,
        start_time: float,
        is_fallback: bool,
    ) -> SandboxExecutionResult:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        label = "Fallback" if is_fallback else "Container"
        return SandboxExecutionResult(
            exit_code=-1,
            stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
            stderr=exc.stderr or "" if isinstance(exc.stderr, str) else "",
            duration_ms=duration_ms,
            timeout_triggered=True,
            is_fallback=is_fallback,
            error_message=f"{label} execution timed out after {self.config.timeout_seconds}s",
        )

    def _execute_docker(
        self,
        code: str,
        test_code: str,
        custom_command: str | None = None,
    ) -> SandboxExecutionResult:
        """Executes test inside ephemeral Docker container."""
        start_time = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="ccba_sandbox_") as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "solution.py").write_text(code, encoding="utf-8")
            (tmp_path / "test_solution.py").write_text(test_code, encoding="utf-8")
            docker_cmd = self._build_docker_cmd(tmp_path, custom_command)
            try:
                proc = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                    check=False,
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    duration_ms=duration_ms,
                    timeout_triggered=False,
                    is_fallback=False,
                )
            except subprocess.TimeoutExpired as exc:
                return self._build_timeout_result(exc, start_time, is_fallback=False)
            except Exception as e:
                logger.warning(f"Docker sandbox run error ({e}); attempting fallback...")
                if self.config.allow_fallback:
                    return self._execute_fallback(code, test_code, custom_command)
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=1,
                    stdout="",
                    stderr=str(e),
                    duration_ms=duration_ms,
                    error_message=str(e),
                )

    def _execute_fallback(
        self,
        code: str,
        test_code: str,
        custom_command: str | None = None,
    ) -> SandboxExecutionResult:
        """Executes in a localized subprocess sandbox when Docker is unavailable."""
        start_time = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="ccba_fallback_sandbox_") as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "solution.py").write_text(code, encoding="utf-8")
            (tmp_path / "test_solution.py").write_text(test_code, encoding="utf-8")
            cmd = (
                custom_command.split()
                if custom_command
                else [sys.executable, "-m", "unittest", "test_solution.py"]
            )
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(tmp_path),
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                    check=False,
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    duration_ms=duration_ms,
                    timeout_triggered=False,
                    is_fallback=True,
                )
            except subprocess.TimeoutExpired as exc:
                return self._build_timeout_result(exc, start_time, is_fallback=True)
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=1,
                    stdout="",
                    stderr=str(e),
                    duration_ms=duration_ms,
                    is_fallback=True,
                    error_message=str(e),
                )


class DockerSandboxScorer(BaseScorer):
    """Evaluates agent-generated Python code by executing unit tests in an isolated sandbox (TICKET-007)."""

    def __init__(
        self,
        name: str = "docker_sandbox_eval",
        weight: float = 0.5,
        is_critical: bool = True,
        runner: DockerSandboxRunner | None = None,
        custom_command: str | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.runner = runner or DockerSandboxRunner()
        self.custom_command = custom_command

    @staticmethod
    def _resolve_test_code(item: EvalItem) -> str | None:
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        ga = item.golden_answer if isinstance(item.golden_answer, dict) else {}
        test_code = (
            meta.get("test_code")
            or meta.get("test_suite")
            or meta.get("sandbox_test")
            or ga.get("test_code")
            or ga.get("test_suite")
        )
        return test_code if isinstance(test_code, str) and test_code else None

    def _format_sandbox_result(self, result: SandboxExecutionResult) -> ScoreResult:
        if result.passed:
            exec_env = (
                "Fallback Local Sandbox" if result.is_fallback else "Docker Hermetic Container"
            )
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                raw_output={
                    "status": "passed",
                    "exit_code": result.exit_code,
                    "duration_ms": result.duration_ms,
                    "is_fallback": result.is_fallback,
                },
                reasoning=(
                    f"Executable Sandbox PASS: All test assertions passed cleanly in {result.duration_ms:.1f}ms "
                    f"via {exec_env}."
                ),
                is_critical_fail=False,
            )

        reason = result.error_message or (result.stderr.strip() or result.stdout.strip())
        short_reason = reason.splitlines()[-1] if reason else f"Exit code {result.exit_code}"
        return ScoreResult(
            scorer_name=self.name,
            score=0.0,
            raw_output={
                "status": "failed",
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timeout": result.timeout_triggered,
                "is_fallback": result.is_fallback,
            },
            reasoning=f"Executable Sandbox FAIL (exit code {result.exit_code}): {short_reason}",
            is_critical_fail=self.is_critical,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        test_code = self._resolve_test_code(item)
        if not test_code:
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                raw_output={"status": "skipped", "reason": "no_test_suite_defined"},
                reasoning="Sandbox Evaluation Skipped: Item has no executable test suite defined in metadata.",
                is_critical_fail=False,
            )

        code_blocks = extract_code_blocks(out_str, language="python")
        if not code_blocks:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output={"status": "missing_code"},
                reasoning="Critical Hard Floor Failure: Output contains no executable Python code blocks (```python).",
                is_critical_fail=self.is_critical,
            )

        result = self.runner.execute(
            code="\n\n".join(code_blocks),
            test_code=test_code,
            custom_command=self.custom_command,
        )
        return self._format_sandbox_result(result)
