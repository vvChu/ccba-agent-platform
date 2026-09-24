"""test_tuner_ssot_fix.py - Regression tests for Tuner SSOT Archetype routing & Heading Inversion prevention."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals.archetypes import (
    resolve_domain_archetype,
    resolve_domain_dataset,
)
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    RatchetConfig,
)
from ccba_harness.verifier import resolve_preset_commands

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_bigbim_skills_ssot_archetype_routing() -> None:
    """Verify bigbim skills are cleanly partitioned: classification -> bim, governance/rase -> general fallback."""
    # bigbim-classification must route to bim / eval_bigbim_classification.json
    arch_class = resolve_domain_archetype("bigbim-classification")
    assert arch_class is not None
    assert arch_class.name == "bim"
    assert resolve_domain_dataset("bigbim-classification") == "eval_bigbim_classification.json"

    # bigbim-governance must fallback cleanly to general domain (never classification)
    arch_gov = resolve_domain_archetype("bigbim-governance")
    assert arch_gov is None
    assert resolve_domain_dataset("bigbim-governance") == "eval_general_domain.json"

    # bigbim-rase must fallback cleanly to general domain (never classification)
    arch_rase = resolve_domain_archetype("bigbim-rase")
    assert arch_rase is None
    assert resolve_domain_dataset("bigbim-rase") == "eval_general_domain.json"

    # bigbim-risk must route to risk
    arch_risk = resolve_domain_archetype("bigbim-risk")
    assert arch_risk is not None
    assert arch_risk.name == "risk"
    assert resolve_domain_dataset("bigbim-risk") == "eval_bigbim_risk.json"

    # bigbim-vbpl-digest must route to legal
    arch_vbpl = resolve_domain_archetype("bigbim-vbpl-digest")
    assert arch_vbpl is not None
    assert arch_vbpl.name == "legal"
    assert resolve_domain_dataset("bigbim-vbpl-digest") == "eval_legal_intel.json"


def test_propose_mutation_coding_no_unsolicited_adr_matrix_token(tmp_path: Path) -> None:
    """Verify propose_mutation for coding skills does not inject raw ADR-0058 token in heading."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: ccba-append-only-logger\n---\n# Logger Pattern\n"
    target.write_text(base_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-append-only-logger")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    mut = tuner.propose_mutation(base_content, 1)

    # Must contain Hard Completion Lock heading WITHOUT (ADR-0058)
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất\n" in mut
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)" not in mut
    # Must still contain required verify-patch command for scorer
    assert "python -m ccba_harness verify-patch" in mut


def test_propose_mutation_headings_have_no_hardcoded_numbers(tmp_path: Path) -> None:
    """Verify all domain strategy headings use semantic headings without numeric prefixes."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: test-skill\n---\n# Test Skill\n"
    target.write_text(base_content, encoding="utf-8")

    domains = [
        "ccba-academic-writing",
        "bigbim-classification",
        "ccba-code-review",
        "ccba-ai-qc-pccc-audit",
        "ccba-legal-intel",
        "ccba-generic-fallback",
    ]
    for skill_name in domains:
        cfg = RatchetConfig(target_file=str(target), skill_name=skill_name)
        tuner = GitRatchetOptimizer(cfg, dry_run_git=True)
        for it in range(1, 5):
            mut = tuner.propose_mutation(base_content, it)
            lines = mut.splitlines()
            h2_lines = [line.strip() for line in lines if line.strip().startswith("## ")]
            for h in h2_lines:
                # Must not start with ## 1., ## 2., ## 4., etc.
                assert not any(h.startswith(f"## {num}.") for num in range(1, 10)), (
                    f"Found numeric heading '{h}' in {skill_name} iteration {it}"
                )


def test_preset_skill_includes_adr_matrix_check() -> None:
    """Verify resolve_preset_commands('skill') includes sync_hub_adr_matrix.py --check for CI parity."""
    cmds = resolve_preset_commands("skill")
    assert any("sync_hub_adr_matrix.py --check" in c for c in cmds)
