"""Unit tests for incremental skill-contract mapping and dedupe in run_harness_evals.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.verifier import SKILL_CONTRACT_TEST_PATHS
from scripts.eval.run_harness_evals import (
    _collect_verify_harness_targets,
    _dedupe_covered_test_targets,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.mark.parametrize(
    "modified_rel",
    [
        ".agents/skills/ccba-new-feature/SKILL.md",
        "docs/skills/ccba-new-feature.md",
        ".agents/AGENTS.md",
    ],
)
def test_collect_verify_harness_targets_maps_all_skill_contract_paths(
    tmp_path: Path, modified_rel: str
) -> None:
    """Verify skill, docs, and AGENTS.md edits trigger all 10 SSOT skill contract tests."""
    targets = _collect_verify_harness_targets(tmp_path, {tmp_path / modified_rel})
    for expected in SKILL_CONTRACT_TEST_PATHS:
        assert expected in targets


def test_dedupe_covered_test_targets_drops_descendant_paths() -> None:
    """Verify ancestor directory targets eliminate duplicate child test file targets."""
    raw = {
        "tests/governance",
        "tests/governance/test_skills_docs_integrity.py",
        "tests/governance/test_statechart_anti_lie.py",
        "tests/test_upstream_workflows.py",
        "scripts/tests",
    }
    assert _dedupe_covered_test_targets(raw) == {
        "tests/governance",
        "tests/test_upstream_workflows.py",
        "scripts/tests",
    }

    with_root_tests = {
        "tests",
        "tests/governance",
        "tests/test_upstream_workflows.py",
        "scripts/tests",
    }
    assert _dedupe_covered_test_targets(with_root_tests) == {"tests", "scripts/tests"}
