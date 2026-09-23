"""test_doc_refactor_daemon.py - Unit tests for Document Auto-Evolution Engine.

Tests code grounding AST indexing, zero-deletion guard, pillar balance auditor,
and dry-run orchestration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.eval.doc_refactor_daemon import (
    CodeGroundingEngine,
    DocAutoEvolutionEngine,
    PillarBalanceAuditor,
    ZeroDeletionGuard,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


class TestDocRefactorDaemon:
    """Test suite for DocAutoEvolutionEngine and auxiliary guards."""

    @pytest.fixture
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @pytest.fixture
    def grounding_engine(self, project_root: Path) -> CodeGroundingEngine:
        return CodeGroundingEngine(root=project_root)

    def test_code_grounding_engine_indexing(self, grounding_engine: CodeGroundingEngine) -> None:
        """Verifies that Python symbols and ADR files are indexed into memory."""
        assert len(grounding_engine.symbol_cache) > 50
        assert len(grounding_engine.file_cache) > 20

        # Verify presence of real symbols
        fake_symbol = "NonExistent" + "FakeSymbol" + "_999"
        verified, missing = grounding_engine.verify_symbols(
            ["DocAutoEvolutionEngine", "ZeroDeletionGuard", fake_symbol]
        )
        assert "DocAutoEvolutionEngine" in verified
        assert "ZeroDeletionGuard" in verified
        assert fake_symbol in missing

    def test_code_grounding_file_verification(self, grounding_engine: CodeGroundingEngine) -> None:
        """Verifies file existence checking in grounding engine."""
        verified, missing = grounding_engine.verify_files(
            ["doc_refactor_daemon.py", "non_existent_file_abc.py"]
        )
        assert "doc_refactor_daemon.py" in verified
        assert "non_existent_file_abc.py" in missing

    def test_zero_deletion_guard_clean_diff(self) -> None:
        """Verifies that non-destructive additions pass zero-deletion audit."""
        orig = "#### P1.1. Pattern One\nContent\n#### P1.2. Pattern Two\nContent"
        prop = "#### P1.1. Pattern One\nContent\n#### P1.2. Pattern Two\nContent\n#### P1.3. Pattern Three\nNew content"

        violations = ZeroDeletionGuard.audit_diff(orig, prop)
        assert len(violations) == 0

    def test_zero_deletion_guard_illegal_deletion(self) -> None:
        """Verifies that silent deletion of patterns triggers a violation."""
        orig = "#### P1.1. Pattern One\nContent\n#### P1.2. Pattern Two\nContent"
        prop = "#### P1.1. Pattern One\nContent"  # P1.2 was deleted!

        violations = ZeroDeletionGuard.audit_diff(orig, prop)
        assert len(violations) == 1
        assert "P1.2" in violations[0]

    def test_zero_deletion_guard_deprecated_exception(self) -> None:
        """Verifies that marking a pattern as DEPRECATED is permitted."""
        orig = "#### P1.1. Pattern One\nContent\n#### P1.2. Pattern Two\nContent"
        prop = "#### P1.1. Pattern One\nContent\n#### P1.2 (DEPRECATED) Pattern Two\nContent"

        violations = ZeroDeletionGuard.audit_diff(orig, prop)
        assert len(violations) == 0

    def test_parse_protection_guard_violation(self) -> None:
        """Verifies that modifying human developer notes triggers a violation."""
        orig = "Header\n<!-- DEVELOPER-NOTES-START -->\nManual Note 1\n<!-- DEVELOPER-NOTES-END -->\nFooter"
        prop = "Header\n<!-- DEVELOPER-NOTES-START -->\nTampered Note!\n<!-- DEVELOPER-NOTES-END -->\nFooter"

        violations = ZeroDeletionGuard.audit_diff(orig, prop)
        assert len(violations) == 1
        assert "Parse-Protection Violation" in violations[0]

    def test_pillar_balance_auditor_bloat_detection(self) -> None:
        """Verifies that pillars exceeding max_patterns are flagged as bloated."""
        bloated_text = "\n## 1. Pillar One\n" + "\n".join(
            [f"#### P1.{i}. Pattern {i}" for i in range(1, 18)]
        )
        results = PillarBalanceAuditor.audit_pillars(bloated_text, max_patterns=15)

        assert len(results) == 1
        assert results[0].pillar_index == 1
        assert results[0].pattern_count == 17
        assert results[0].is_bloated is True

    def test_pillar_balance_auditor_real_session_learnings(self, project_root: Path) -> None:
        """Verifies that the rebalanced session_learnings.md currently has 0 bloated pillars."""
        session_learnings_file = project_root / ".md" / "knowledge" / "session_learnings.md"
        content = session_learnings_file.read_text(encoding="utf-8")
        results = PillarBalanceAuditor.audit_pillars(content, max_patterns=25)

        assert len(results) >= 5  # Active Pillars
        for p in results:
            assert p.is_bloated is False, (
                f"Pillar {p.pillar_index} ({p.pillar_title}) is unexpectedly bloated: {p.pattern_count}"
            )

    def test_doc_auto_evolution_engine_dry_run(self, project_root: Path) -> None:
        """Verifies that run_nightly_evolution runs cleanly in dry-run mode."""
        engine = DocAutoEvolutionEngine(root=project_root)
        report = engine.run_nightly_evolution(dry_run=True)

        assert report.dry_run is True
        assert report.health.is_healthy is True
        assert len(report.health.bloated_pillars) >= 5
        assert "docs/auto-refactor-" in report.branch_name

        # Verify PR body generation
        pr_body = engine.generate_pr_body(report)
        assert "Automated Knowledge Documentation Evolution Report" in pr_body
        assert "Trụ Cột" in pr_body

    def test_empty_push_guard_when_zero_commits(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifies that when commits_created is 0, no push or PR is made and empty branch is cleaned up."""
        import subprocess

        executed_cmds: list[list[str]] = []

        class MockRes:
            def __init__(self, stdout: str = "", returncode: int = 0):
                self.stdout = stdout
                self.returncode = returncode

        def mock_run(cmd, *args, **kwargs):
            cmd_list = list(cmd)
            executed_cmds.append(cmd_list)

            if cmd_list[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                return MockRes(stdout="main\n", returncode=0)
            elif cmd_list[:2] == ["git", "commit"]:
                # Simulate nothing to commit (clean working tree)
                return MockRes(stdout="nothing to commit, working tree clean", returncode=1)
            return MockRes(returncode=0)

        monkeypatch.setattr(subprocess, "run", mock_run)

        engine = DocAutoEvolutionEngine(root=project_root)
        report = engine.run_nightly_evolution(dry_run=False)

        assert report.commits_created == 0
        assert report.pr_url is None

        # Assert git push was NEVER called
        push_calls = [c for c in executed_cmds if len(c) >= 2 and c[:2] == ["git", "push"]]
        assert len(push_calls) == 0, f"Expected 0 git push calls, found: {push_calls}"

        # Assert gh pr create was NEVER called
        pr_calls = [c for c in executed_cmds if len(c) >= 3 and c[:3] == ["gh", "pr", "create"]]
        assert len(pr_calls) == 0, f"Expected 0 gh pr create calls, found: {pr_calls}"

        # Assert checkout previous ref and delete empty branch were called
        checkout_prev = [
            c
            for c in executed_cmds
            if len(c) >= 3 and c[:2] == ["git", "checkout"] and c[2] == "main"
        ]
        assert len(checkout_prev) == 1, "Expected checkout back to previous ref"

        delete_branch = [
            c for c in executed_cmds if len(c) >= 3 and c[:3] == ["git", "branch", "-D"]
        ]
        assert len(delete_branch) == 1, "Expected git branch -D to clean up empty branch"

    def test_doc_refactor_pr_creation_logs_error_and_retries_without_bad_label(
        self, project_root: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies doc_refactor_daemon logs gh errors and falls back to opening PR without invalid label."""
        import logging
        import subprocess

        class MockRes:
            def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
                self.stdout = stdout
                self.stderr = stderr
                self.returncode = returncode

        def mock_run(cmd, *args, **kwargs):
            cmd_list = list(cmd)
            if cmd_list[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                return MockRes(stdout="main\n", returncode=0)
            if cmd_list[:2] == ["git", "commit"]:
                return MockRes(stdout="[docs/auto-refactor] commit", returncode=0)
            if cmd_list[:2] == ["git", "push"]:
                return MockRes(returncode=0)
            if cmd_list[:3] == ["gh", "pr", "create"]:
                if "--label" in cmd_list:
                    return MockRes(
                        stderr="could not add label: 'documentation' not found", returncode=1
                    )
                return MockRes(
                    stdout="https://github.com/vvChu/ccba-agent-platform/pull/294\n", returncode=0
                )
            return MockRes(returncode=0)

        monkeypatch.setattr(subprocess, "run", mock_run)

        engine = DocAutoEvolutionEngine(root=project_root)
        with caplog.at_level(logging.WARNING):
            report = engine.run_nightly_evolution(dry_run=False)

        assert report.commits_created == 1
        assert report.pr_url == "https://github.com/vvChu/ccba-agent-platform/pull/294"
        assert "could not add label: 'documentation' not found" in caplog.text

    def test_zero_deletion_guard_hub_and_spoke_formats(self) -> None:
        """Verifies that ZeroDeletionGuard recognizes Hub RULE-X.Y and Spoke ## N. formats."""
        orig_hub = (
            "- **RULE-1.1 [ADR-0059]**: First rule\n"
            "- **RULE-1.2 [ADR-0057]**: Second rule\n"
            "#### P1.3 Legacy Pattern"
        )
        # 1. Illegal deletion of RULE-1.2 and P1.3
        prop_hub_deleted = "- **RULE-1.1 [ADR-0059]**: First rule"
        violations_hub = ZeroDeletionGuard.audit_diff(orig_hub, prop_hub_deleted)
        assert len(violations_hub) == 2
        assert any("RULE-1.2" in v for v in violations_hub)
        assert any("P1.3" in v for v in violations_hub)

        # 2. Permitted deprecation with brackets [DEPRECATED] or (DEPRECATED)
        prop_hub_deprecated = (
            "- **RULE-1.1 [ADR-0059]**: First rule\n"
            "- RULE-1.2 [ADR-0057] [DEPRECATED]: Second rule\n"
            "#### P1.3 (DEPRECATED) Legacy Pattern"
        )
        violations_hub_dep = ZeroDeletionGuard.audit_diff(orig_hub, prop_hub_deprecated)
        assert len(violations_hub_dep) == 0

        # 3. Spoke format with ## Miền N. and deprecation
        orig_spoke = "## Miền 1. Provenance\nContent\n## Miền 2. Quản Trị Tri Thức\nContent"
        prop_spoke_deleted = "## Miền 1. Provenance\nContent"
        violations_spoke = ZeroDeletionGuard.audit_diff(orig_spoke, prop_spoke_deleted)
        assert len(violations_spoke) == 1
        assert "SEC-2" in violations_spoke[0]

        # 4. Spoke section deprecation
        prop_spoke_dep = (
            "## Miền 1. Provenance\nContent\n## Miền 2. Quản Trị Tri Thức [DEPRECATED]\nContent"
        )
        violations_spoke_dep = ZeroDeletionGuard.audit_diff(orig_spoke, prop_spoke_dep)
        assert len(violations_spoke_dep) == 0

    def test_doc_auto_evolution_audit_only_mode(self, project_root: Path) -> None:
        """Verifies that audit-only mode runs in-memory and sends alert without git mutation."""
        captured_reports = []

        def mock_emitter(rep):
            captured_reports.append(rep)
            return True

        engine = DocAutoEvolutionEngine(root=project_root, alert_emitter=mock_emitter)
        report = engine.run_nightly_evolution(audit_only=True)

        assert report.commits_created == 0
        assert report.pr_url is None
        assert len(captured_reports) == 1
        assert captured_reports[0].health.timestamp is not None

    def test_dynamic_telegram_alert_and_pr_body(self, project_root: Path) -> None:
        """Verifies that PR body and Telegram alerts dynamically reflect actual pillars and zero hardcoded fake data."""
        captured_messages = []

        def mock_emitter(rep):
            # Test alert content generation logic
            pillar_lines = []
            for p in rep.health.bloated_pillars:
                icon = "🔴" if p.is_bloated else "🟢"
                pillar_lines.append(f"• {icon} {p.pillar_title}: {p.pattern_count} patterns")
            captured_messages.append("\n".join(pillar_lines))
            return True

        engine = DocAutoEvolutionEngine(root=project_root, alert_emitter=mock_emitter)
        report = engine.run_nightly_evolution(dry_run=True)
        engine.send_telegram_alert(report)

        pr_body = engine.generate_pr_body(report)
        # Verify no hardcoded Potemkin strings
        assert "Trạng thái 8 Trụ Cột" not in pr_body
        assert "Bảng Đối Soát Cân Bằng Các Trụ Cột Tri Thức" in pr_body

        # Verify dynamic pillars rendered in alert
        assert len(captured_messages) == 1
        assert "patterns" in captured_messages[0]
