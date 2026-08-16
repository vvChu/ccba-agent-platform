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

        assert len(results) == 8  # 8 Pillars
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
        assert len(report.health.bloated_pillars) == 8
        assert "docs/auto-refactor-" in report.branch_name

        # Verify PR body generation
        pr_body = engine.generate_pr_body(report)
        assert "Automated Knowledge Documentation Evolution Report" in pr_body
        assert "Trụ Cột" in pr_body
