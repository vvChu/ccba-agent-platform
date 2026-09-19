"""test_doc_daemon.py - Scoped Fast Unit Tests for ccba_harness.docs Deep Seam."""

from __future__ import annotations

import pytest

from ccba_harness.docs import (
    CodeGroundingEngine,
    DocAutoEvolutionEngine,
    PillarBalanceAuditor,
    ZeroDeletionGuard,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_docs_public_seam_exports() -> None:
    """Verify ccba_harness.docs exports all public entities."""
    assert CodeGroundingEngine is not None
    assert DocAutoEvolutionEngine is not None
    assert PillarBalanceAuditor is not None
    assert ZeroDeletionGuard is not None


def test_zero_deletion_guard_clean() -> None:
    """Verify ZeroDeletionGuard accepts additive changes."""
    orig = "#### P1.1. First\nContent"
    prop = "#### P1.1. First\nContent\n#### P1.2. Second\nNew"
    violations = ZeroDeletionGuard.audit_diff(orig, prop)
    assert len(violations) == 0


def test_zero_deletion_guard_violation() -> None:
    """Verify ZeroDeletionGuard detects removed pattern without [DEPRECATED]."""
    orig = "#### P1.1. First\nContent"
    prop = "#### P1.2. Second\nNew"
    violations = ZeroDeletionGuard.audit_diff(orig, prop)
    assert len(violations) == 1
    assert "Zero-Deletion Violation" in violations[0]


def test_pillar_balance_auditor_detection() -> None:
    """Verify PillarBalanceAuditor identifies bloated pillars."""
    content = "\n## 1. Pillar One\n" + "\n".join(f"#### P1.{i}. Pattern {i}" for i in range(1, 20))
    bloat_info = PillarBalanceAuditor.audit_pillars(content, max_patterns=10)
    assert len(bloat_info) == 1
    assert bloat_info[0].is_bloated is True
    assert bloat_info[0].pattern_count == 19
