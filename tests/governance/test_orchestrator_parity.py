"""test_orchestrator_parity.py - Governance Test for Tier 3 Composite Orchestrators.

Verifies:
1. All 9 Tier 3 Composite Orchestrators exist and have 'tier: orchestrator' and 'is-orchestrated: true'.
2. All 9 Orchestrators pass 'validate_skills' with strict '--enforce-gpi' (bypassing Stage 2 GPI).
3. All 9 Orchestrators are registered in 'catalog.yaml' with tier: orchestrator.
4. User ritual Orchestrators maintain 'disable-model-invocation: true' (0 background tokens).
5. Multi-agent Orchestrators comply with Single-Writer Protocol (ADR-0053).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]

HUB_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
CATALOG_PATH = SKILLS_DIR / "platform-loader" / "catalog.yaml"

TIER_3_ORCHESTRATORS = [
    "ccba-ai-qc",
    "ccba-autoresearch",
    "ccba-graduate-rd",
    "ccba-implement",
    "ccba-knowledge-loop",
    "ccba-new-feature",
    "ccba-release-feature",
    "ccba-spoke-adopter",
    "ccba-teamwork",
]

USER_RITUAL_ORCHESTRATORS = [
    "ccba-autoresearch",
    "ccba-graduate-rd",
    "ccba-implement",
    "ccba-knowledge-loop",
    "ccba-new-feature",
    "ccba-release-feature",
    "ccba-spoke-adopter",
    "ccba-teamwork",
]


def test_all_nine_orchestrators_exist_and_declared() -> None:
    """Verify that exactly the 9 Tier 3 Orchestrators exist and declare tier: orchestrator."""
    for name in TIER_3_ORCHESTRATORS:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        assert skill_file.exists(), f"Orchestrator skill file missing: {skill_file}"

        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"Missing frontmatter in {skill_file}"
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])

        assert meta.get("tier") == "orchestrator", f"{name} must have tier: orchestrator"
        assert meta.get("is-orchestrated") is True or meta.get("is_orchestrated") is True, (
            f"{name} must have is-orchestrated: true"
        )


def test_all_orchestrators_pass_enforce_gpi() -> None:
    """Verify that all 9 Orchestrators pass SkillValidator under --enforce-gpi without needing 'gpi:'."""
    validator = SkillValidator()
    for name in TIER_3_ORCHESTRATORS:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        issues = validator.audit_skill(skill_file, enforce_gpi=True)
        assert not issues, f"Orchestrator {name} failed audit: {[i.message for i in issues]}"


def test_orchestrators_registered_in_catalog() -> None:
    """Verify that all 9 Orchestrators appear with tier: orchestrator in catalog.yaml."""
    assert CATALOG_PATH.exists(), "catalog.yaml missing"
    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    skills_map = {s["name"]: s for s in catalog.get("skills", [])}

    for name in TIER_3_ORCHESTRATORS:
        assert name in skills_map, f"{name} not found in catalog.yaml"
        entry = skills_map[name]
        assert entry.get("tier") == "orchestrator", (
            f"{name} in catalog.yaml must have tier: orchestrator"
        )


def test_ritual_orchestrators_zero_background_tokens() -> None:
    """Verify that 8 User Ritual Orchestrators maintain disable-model-invocation: true."""
    for name in USER_RITUAL_ORCHESTRATORS:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        assert meta.get("disable-model-invocation") is True, (
            f"User ritual {name} must have disable-model-invocation: true to preserve 0 background tokens"
        )


def test_multi_agent_single_writer_compliance() -> None:
    """Verify that multi-agent Orchestrators explicitly declare Single-Writer Protocol (ADR-0053)."""
    for name in ["ccba-teamwork", "ccba-knowledge-loop"]:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8").lower()
        has_single_writer = any(
            k in content
            for k in (
                "single-writer",
                "single writer",
                "read-only",
                "read only",
                "duy nhất orchestrator",
                "duy nhất có quyền ghi",
            )
        )
        assert has_single_writer, (
            f"Multi-agent orchestrator {name} must specify Single-Writer Protocol"
        )
