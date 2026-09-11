"""healing.py - Autonomous Self-Healing & Closed-Loop CI Patch Engine.

Provides automated diagnosis, candidate patch generation, and deterministic verification
remediation to prevent CI loops and premature task abandonment (ADR-0053, ADR-0058):
1. ErrorCategory: Classifies errors into format, lint, metadata drift, links, or assertions.
2. DiagnosticIssue: Structured failure details extracted from CommandResult / stderr.
3. HealingAction: Concrete corrective action (CLI command or virtual file patch).
4. SelfHealingEngine: Closed-loop orchestrator with hard 2-iteration ceiling and rollback.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .verifier import PatchVerificationReport, verify_patch_execution

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Classification of automated verification failures."""

    FORMAT_STYLE = "FORMAT_STYLE"
    LINT_SYNTAX = "LINT_SYNTAX"
    METADATA_DRIFT = "METADATA_DRIFT"
    BROKEN_LINK = "BROKEN_LINK"
    TEST_ASSERTION = "TEST_ASSERTION"
    UNKNOWN = "UNKNOWN"


@dataclass
class DiagnosticIssue:
    """Detailed diagnosis of a single verification failure."""

    category: str
    command: str
    file_path: str | None = None
    line_number: int | None = None
    rule_code: str | None = None
    message: str = ""
    raw_snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealingAction:
    """A concrete remediation action executed by the self-healing engine."""

    action_type: str  # "COMMAND_AUTORUN" or "FILE_PATCH"
    description: str
    command: str | None = None
    target_file: str | None = None
    executed: bool = False
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealingReport:
    """Outcome report of a closed-loop self-healing execution."""

    success: bool
    iterations_run: int
    diagnosed_issues: list[DiagnosticIssue] = field(default_factory=list)
    actions_taken: list[HealingAction] = field(default_factory=list)
    final_verification_passed: bool = False
    rollback_performed: bool = False
    duration_ms: float = 0.0
    final_verification_report: PatchVerificationReport | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "iterations_run": self.iterations_run,
            "diagnosed_issues": [i.to_dict() for i in self.diagnosed_issues],
            "actions_taken": [a.to_dict() for a in self.actions_taken],
            "final_verification_passed": self.final_verification_passed,
            "rollback_performed": self.rollback_performed,
            "duration_ms": round(self.duration_ms, 2),
            "final_verification_report": (
                self.final_verification_report.to_dict() if self.final_verification_report else None
            ),
        }

    def to_markdown(self) -> str:
        """Render self-healing summary report as GitHub-Flavored Markdown."""
        badge = (
            "✅ SELF-HEALING SUCCEEDED"
            if self.success
            else ("🔄 ROLLED BACK" if self.rollback_performed else "❌ HEALING FAILED")
        )
        lines = [
            f"# 🩹 Autonomous Self-Healing Report: {badge}",
            "",
            f"- **Success:** {'YES' if self.success else 'NO'}",
            f"- **Iterations Run:** {self.iterations_run}",
            f"- **Final Verification Passed:** {'YES' if self.final_verification_passed else 'NO'}",
            f"- **Rollback Performed:** {'YES' if self.rollback_performed else 'NO'}",
            f"- **Duration:** {self.duration_ms:.1f} ms",
            f"- **Issues Diagnosed:** {len(self.diagnosed_issues)}",
            f"- **Actions Executed:** {len(self.actions_taken)}",
            "",
        ]
        if self.diagnosed_issues:
            lines.extend(
                [
                    "## Diagnosed Issues",
                    "",
                    "| Category | Rule / Target | Message |",
                    "| :--- | :--- | :--- |",
                ]
            )
            for iss in self.diagnosed_issues:
                target = iss.file_path or iss.rule_code or iss.command
                lines.append(f"| `{iss.category}` | `{target}` | {iss.message} |")
            lines.append("")

        if self.actions_taken:
            lines.extend(
                [
                    "## Remediation Actions Taken",
                    "",
                    "| Status | Type | Command / Action |",
                    "| :---: | :--- | :--- |",
                ]
            )
            for act in self.actions_taken:
                st = "✅" if act.success else "❌"
                cmd_or_desc = f"`{act.command}`" if act.command else act.description
                lines.append(f"| {st} | `{act.action_type}` | {cmd_or_desc} |")
            lines.append("")

        if self.final_verification_report:
            lines.extend(
                [
                    "---",
                    "## Final Verification Report",
                    "",
                    self.final_verification_report.to_markdown(),
                ]
            )
        return "\n".join(lines)


class SelfHealingEngine:
    """Autonomous engine diagnosing verification failures and executing closed-loop fixes.

    Guarantees:
    - Hard iteration ceiling (default: max 2 iterations).
    - In-memory snapshot capture and atomic rollback if healing does not achieve Exit 0.
    - Zero unverified mutations: changes are only retained if all verify_commands pass.
    """

    def __init__(self, base_dir: Path | str | None = None, max_iterations: int = 2) -> None:
        self.base_dir = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()
        self.max_iterations = max(1, min(max_iterations, 2))

    def diagnose_failures(self, report: PatchVerificationReport) -> list[DiagnosticIssue]:
        """Analyze failed commands in verification report and classify root causes."""
        issues: list[DiagnosticIssue] = []

        for res in report.results:
            if res.passed:
                continue

            combined_output = f"{res.stdout}\n{res.stderr}".strip()

            # 1. Check for Ruff format errors
            if "ruff format" in res.command:
                issues.extend(self._diagnose_ruff_format(res.command, combined_output))
                continue

            # 2. Check for Ruff lint errors
            if "ruff check" in res.command:
                issues.extend(self._diagnose_ruff_check(res.command, combined_output))
                continue

            # 3. Check for metadata catalog sync errors
            if "compile_catalog.py" in res.command:
                issues.append(
                    DiagnosticIssue(
                        category=ErrorCategory.METADATA_DRIFT.value,
                        command=res.command,
                        message="Catalog YAML is out of sync with .agents/skills/ frontmatter",
                        raw_snippet=combined_output[:300],
                    )
                )
                continue

            # 4. Check for ADR matrix sync errors
            if "sync_hub_adr_matrix.py" in res.command:
                issues.append(
                    DiagnosticIssue(
                        category=ErrorCategory.METADATA_DRIFT.value,
                        command=res.command,
                        message="ADR matrix is out of sync with docs/adr/",
                        raw_snippet=combined_output[:300],
                    )
                )
                continue

            # 5. Check for Pytest failures
            if "pytest" in res.command:
                issues.extend(self._diagnose_pytest_failures(res.command, combined_output))
                continue

            # Generic fallback
            issues.append(
                DiagnosticIssue(
                    category=ErrorCategory.UNKNOWN.value,
                    command=res.command,
                    message=f"Command failed with exit code {res.exit_code}",
                    raw_snippet=combined_output[:400],
                )
            )

        return issues

    def _diagnose_ruff_format(self, cmd: str, output: str) -> list[DiagnosticIssue]:
        """Extract files needing formatting from ruff format output."""
        issues = []
        for match in re.finditer(r"Would reformat:\s*([^\r\n]+)", output):
            f_path = match.group(1).strip()
            issues.append(
                DiagnosticIssue(
                    category=ErrorCategory.FORMAT_STYLE.value,
                    command=cmd,
                    file_path=f_path,
                    message=f"File violates ruff code formatting: {f_path}",
                    raw_snippet=match.group(0),
                )
            )
        return issues

    def _diagnose_ruff_check(self, cmd: str, output: str) -> list[DiagnosticIssue]:
        """Extract lint errors from ruff check output."""
        issues = []
        # Pattern 1 (concise): file.py:12:8: F401 `os` imported but unused
        pattern_concise = r"([a-zA-Z0-9_\-/\\]+\.py):(\d+):(\d+):\s*([A-Z0-9]+)\s*([^\r\n]+)"
        for match in re.finditer(pattern_concise, output):
            f_path, line_no, _, code, msg = match.groups()
            issues.append(
                DiagnosticIssue(
                    category=ErrorCategory.LINT_SYNTAX.value,
                    command=cmd,
                    file_path=f_path.strip(),
                    line_number=int(line_no),
                    rule_code=code.strip(),
                    message=f"{code}: {msg.strip()}",
                    raw_snippet=match.group(0),
                )
            )

        # Pattern 2 (multiline default):
        # F401 [*] `sys` imported but unused
        #   --> packages\ccba-harness\src\ccba_harness\healing.py:16:8
        pattern_multiline = r"([A-Z0-9]+)\s*(?:\[\*\])?\s*([^\r\n]+)\r?\n\s*-->\s*([a-zA-Z0-9_\-/\\]+\.py):(\d+):(\d+)"
        for match in re.finditer(pattern_multiline, output):
            code, msg, f_path, line_no, _ = match.groups()
            issues.append(
                DiagnosticIssue(
                    category=ErrorCategory.LINT_SYNTAX.value,
                    command=cmd,
                    file_path=f_path.strip(),
                    line_number=int(line_no),
                    rule_code=code.strip(),
                    message=f"{code}: {msg.strip()}",
                    raw_snippet=match.group(0),
                )
            )

        return issues

    def _diagnose_pytest_failures(self, cmd: str, output: str) -> list[DiagnosticIssue]:
        """Extract test failure locations from pytest output."""
        issues = []
        # Pattern: FAILED path/to/test.py::test_name - Error message
        pattern = r"FAILED\s+([^\s:]+)::([^\s\-]+)\s*-\s*([^\r\n]+)"
        for match in re.finditer(pattern, output):
            f_path, test_name, err_msg = match.groups()
            issues.append(
                DiagnosticIssue(
                    category=ErrorCategory.TEST_ASSERTION.value,
                    command=cmd,
                    file_path=f_path.strip(),
                    message=f"Test failure in {test_name}: {err_msg.strip()}",
                    raw_snippet=match.group(0),
                )
            )
        return issues

    def generate_remediation_actions(
        self, issues: Sequence[DiagnosticIssue]
    ) -> list[HealingAction]:
        """Generate deterministic healing actions to resolve diagnosed issues."""
        actions: list[HealingAction] = []
        format_targets: set[str] = set()
        lint_fix_targets: set[str] = set()

        for issue in issues:
            if issue.category == ErrorCategory.FORMAT_STYLE.value and issue.file_path:
                format_targets.add(issue.file_path)

            elif issue.category == ErrorCategory.LINT_SYNTAX.value and issue.file_path:
                lint_fix_targets.add(issue.file_path)

            elif issue.category == ErrorCategory.METADATA_DRIFT.value:
                if "compile_catalog.py" in issue.command:
                    actions.append(
                        HealingAction(
                            action_type="COMMAND_AUTORUN",
                            description="Regenerate platform catalog.yaml to match skills frontmatter",
                            command="python scripts/governance/compile_catalog.py --write",
                        )
                    )
                elif "sync_hub_adr_matrix.py" in issue.command:
                    actions.append(
                        HealingAction(
                            action_type="COMMAND_AUTORUN",
                            description="Synchronize Architecture Decision Records matrix",
                            command="python scripts/sync_hub_adr_matrix.py",
                        )
                    )

        # Combine ruff check --fix commands
        if lint_fix_targets:
            files_arg = " ".join(f'"{f}"' for f in sorted(lint_fix_targets))
            actions.append(
                HealingAction(
                    action_type="COMMAND_AUTORUN",
                    description=f"Auto-fix lint issues (unused imports, sort) for {len(lint_fix_targets)} files",
                    command=f"python -m ruff check --fix {files_arg}",
                )
            )

        # Combine ruff format commands
        all_format_targets = format_targets | lint_fix_targets
        if all_format_targets:
            files_arg = " ".join(f'"{f}"' for f in sorted(all_format_targets))
            actions.append(
                HealingAction(
                    action_type="COMMAND_AUTORUN",
                    description=f"Format {len(all_format_targets)} files with ruff",
                    command=f"python -m ruff format {files_arg}",
                )
            )

        return actions

    def execute_action(self, action: HealingAction) -> bool:
        """Execute a single remediation action in the workspace."""
        action.executed = True
        if not action.command:
            return False

        try:
            logger.info("Executing self-healing command: %s", action.command)
            proc = subprocess.run(
                action.command,
                shell=True,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30.0,
            )
            action.success = proc.returncode == 0
            return action.success
        except Exception as exc:
            logger.warning("Healing action '%s' raised exception: %s", action.description, exc)
            action.success = False
            return False

    def attempt_closed_loop_healing(
        self,
        verify_commands: Sequence[str],
        timeout: float = 60.0,
        snapshot: dict[Path, str | None] | None = None,
        candidate_files: Sequence[str] | None = None,
    ) -> HealingReport:
        """Execute closed-loop healing with verification, iteration ceiling, and safety rollback."""
        t_start = time.perf_counter()

        # Step 0: Ensure in-memory snapshot if not supplied
        local_snapshot: dict[Path, str | None] = {}
        if snapshot is not None:
            local_snapshot = snapshot
        elif candidate_files:
            for f_str in candidate_files:
                p = self.base_dir / f_str if not Path(f_str).is_absolute() else Path(f_str)
                local_snapshot[p] = p.read_text(encoding="utf-8") if p.exists() else None

        # Run initial verification pass
        initial_report = verify_patch_execution(
            commands=verify_commands,
            cwd=self.base_dir,
            timeout=timeout,
        )

        if initial_report.all_passed:
            return HealingReport(
                success=True,
                iterations_run=0,
                final_verification_passed=True,
                final_verification_report=initial_report,
                duration_ms=(time.perf_counter() - t_start) * 1000.0,
            )

        all_diagnosed: list[DiagnosticIssue] = []
        all_actions: list[HealingAction] = []
        current_report = initial_report

        for iteration in range(1, self.max_iterations + 1):
            logger.info("Starting Self-Healing Iteration %d/%d", iteration, self.max_iterations)

            # Diagnose failures
            issues = self.diagnose_failures(current_report)
            all_diagnosed.extend(issues)

            if not issues:
                logger.warning("No actionable diagnoses found for failed commands, stopping.")
                break

            # Snapshot any diagnosed files before generating/executing fixes
            for iss in issues:
                if iss.file_path:
                    fp = (
                        self.base_dir / iss.file_path
                        if not Path(iss.file_path).is_absolute()
                        else Path(iss.file_path)
                    )
                    if fp not in local_snapshot:
                        local_snapshot[fp] = fp.read_text(encoding="utf-8") if fp.exists() else None
                elif iss.category == ErrorCategory.METADATA_DRIFT.value:
                    if "compile_catalog" in iss.command:
                        cat_file = (
                            self.base_dir
                            / ".agents"
                            / "skills"
                            / "platform-loader"
                            / "catalog.yaml"
                        )
                        if cat_file not in local_snapshot:
                            local_snapshot[cat_file] = (
                                cat_file.read_text(encoding="utf-8") if cat_file.exists() else None
                            )
                    elif "sync_hub_adr_matrix" in iss.command:
                        adr_file = self.base_dir / "docs" / "adr" / "README.md"
                        if adr_file not in local_snapshot:
                            local_snapshot[adr_file] = (
                                adr_file.read_text(encoding="utf-8") if adr_file.exists() else None
                            )

            # Generate actions
            actions = self.generate_remediation_actions(issues)
            if not actions:
                logger.warning("No remediation actions could be formulated, stopping.")
                break

            # Execute actions
            for act in actions:
                self.execute_action(act)
                all_actions.append(act)

            # Re-verify closed loop
            current_report = verify_patch_execution(
                commands=verify_commands,
                cwd=self.base_dir,
                timeout=timeout,
            )

            if current_report.all_passed:
                logger.info(
                    "Self-Healing successfully restored Exit Code 0 at iteration %d!", iteration
                )
                return HealingReport(
                    success=True,
                    iterations_run=iteration,
                    diagnosed_issues=all_diagnosed,
                    actions_taken=all_actions,
                    final_verification_passed=True,
                    rollback_performed=False,
                    final_verification_report=current_report,
                    duration_ms=(time.perf_counter() - t_start) * 1000.0,
                )

        # Max iterations reached without attaining exit code 0 -> Rollback safety guard
        rollback_done = False
        if local_snapshot:
            logger.warning(
                "Self-Healing failed after %d iterations. Rolling back snapshot.",
                self.max_iterations,
            )
            for file_path, original_content in local_snapshot.items():
                try:
                    if original_content is None:
                        if file_path.exists():
                            file_path.unlink()
                    else:
                        file_path.write_text(original_content, encoding="utf-8")
                    rollback_done = True
                except Exception as exc:
                    logger.error("Failed to restore %s during rollback: %s", file_path, exc)

        return HealingReport(
            success=False,
            iterations_run=self.max_iterations,
            diagnosed_issues=all_diagnosed,
            actions_taken=all_actions,
            final_verification_passed=False,
            rollback_performed=rollback_done,
            final_verification_report=current_report,
            duration_ms=(time.perf_counter() - t_start) * 1000.0,
        )
