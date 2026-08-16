"""test_skill_taxonomy_and_gates.py - Governance Tests for Skills Hierarchy & CI Gates (ADR-0040).

Verifies:
1. Real workspace satisfies all 4 Hard CI Gates (0 violations).
2. Zero-Duplicate Gate catches duplicate skill names across directories.
3. Context Budget Ceiling Gate catches bundles exceeding 10 model-invoked skills.
4. Description length gate catches model-invoked descriptions > 180 characters.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.governance import DocumentAuditor, SkillAuditor

pytestmark = [pytest.mark.fast, pytest.mark.unit]
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_real_codebase_skill_ci_gates() -> None:
    """Verify that all skills in the platform pass 100% of CI gates and workspace checks."""
    auditor = DocumentAuditor(PROJECT_ROOT)
    skills_dir = PROJECT_ROOT / ".agents" / "skills"
    assert skills_dir.exists()

    # 1. Check individual skills
    skill_files = list(skills_dir.rglob("SKILL.md"))
    assert len(skill_files) > 50, f"Expected >50 skills, found {len(skill_files)}"

    for sf in skill_files:
        issues = auditor.audit_skill(sf)
        assert len(issues) == 0, f"Skill {sf} has issues: {[i.message for i in issues]}"

    # 2. Check workspace-level hard gates
    gate_issues = auditor.audit_workspace_gates(skills_dir)
    assert len(gate_issues) == 0, (
        f"Workspace hard gate violations: {[g.message for g in gate_issues]}"
    )


def test_zero_duplicate_gate_catches_duplicates(tmp_path: Path) -> None:
    """Verify that SkillAuditor flags duplicate skill names across directories."""
    auditor = SkillAuditor(tmp_path)
    skill_a = tmp_path / "skill_a" / "SKILL.md"
    skill_b = tmp_path / "skill_b" / "SKILL.md"
    skill_a.parent.mkdir(parents=True)
    skill_b.parent.mkdir(parents=True)

    skill_a.write_text(
        "---\nname: my-duplicate-skill\ndescription: Test A\nbundle: _core\n---\n# Test A\n",
        encoding="utf-8",
    )
    skill_b.write_text(
        "---\nname: my-duplicate-skill\ndescription: Test B\nbundle: _qc\n---\n# Test B\n",
        encoding="utf-8",
    )

    issues = auditor.audit_workspace_gates(tmp_path)
    dup_issues = [i for i in issues if i.category == "ZERO_DUPLICATE_GATE_VIOLATION"]
    assert len(dup_issues) == 1
    assert "Duplicate skill name 'my-duplicate-skill'" in dup_issues[0].message


def test_context_budget_ceiling_catches_overflow(tmp_path: Path) -> None:
    """Verify that SkillAuditor flags bundles with > 10 model-invoked skills."""
    auditor = SkillAuditor(tmp_path)
    bundle_dir = tmp_path / "overflow_bundle"
    bundle_dir.mkdir(parents=True)

    for i in range(12):
        sf = bundle_dir / f"skill_{i}" / "SKILL.md"
        sf.parent.mkdir(parents=True)
        sf.write_text(
            f"---\nname: skill-{i}\ndescription: Test skill {i}\nbundle: _test_bundle\n---\n# Skill {i}\n",
            encoding="utf-8",
        )

    issues = auditor.audit_workspace_gates(tmp_path)
    overflow_issues = [i for i in issues if i.category == "CONTEXT_BUDGET_CEILING_EXCEEDED"]
    assert len(overflow_issues) == 1
    assert "Bundle '_test_bundle' has 12 model-invoked skills" in overflow_issues[0].message


def test_description_length_limit_on_model_invoked(tmp_path: Path) -> None:
    """Verify that model-invoked skills with descriptions > 180 chars are flagged."""
    auditor = SkillAuditor(tmp_path)
    sf = tmp_path / "SKILL.md"
    long_desc = "A" * 185
    sf.write_text(
        f"---\nname: long-desc-skill\ndescription: {long_desc}\nbundle: _core\n---\n# Long Desc\n",
        encoding="utf-8",
    )

    issues = auditor.audit_skill(sf)
    desc_issues = [i for i in issues if i.category == "DESCRIPTION_TOO_LONG"]
    assert len(desc_issues) == 1
    assert "exceeds 180 character limit" in desc_issues[0].message
