"""test_upstream_workflows.py - Unit tests for Upstream Contribution Workflows and /ccba-new-feature.

Verifies:
1. /ccba-issue-to-hub workflow exists, has disable-model-invocation and references gh issue create.
2. /ccba-contribute-to-hub workflow exists, has disable-model-invocation and references check_spoke_leakage.py.
3. /ccba-propose-to-hub workflow acts as backward-compatible alias.
4. /ccba-new-feature workflow references scripts/eval/run_harness_evals.py and gh issue view.
5. catalog.yaml registers all upstream workflows with valid paths.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.fast, pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
CATALOG_FILE = REPO_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"


def test_ccba_issue_to_hub_workflow_structure() -> None:
    """Verify /ccba-issue-to-hub skill structure and commands."""
    skill_path = SKILLS_DIR / "ccba-issue-to-hub" / "SKILL.md"
    assert skill_path.exists(), "ccba-issue-to-hub SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in content
    assert "gh issue create" in content
    assert "gh issue list" in content
    assert "Acceptance Criteria" in content


def test_ccba_contribute_to_hub_workflow_structure() -> None:
    """Verify /ccba-contribute-to-hub skill structure and commands."""
    skill_path = SKILLS_DIR / "ccba-contribute-to-hub" / "SKILL.md"
    assert skill_path.exists(), "ccba-contribute-to-hub SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in content
    assert "check_spoke_leakage.py" in content
    assert "gh pr create" in content
    assert "gh pr checks" in content


def test_ccba_propose_to_hub_alias_structure() -> None:
    """Verify /ccba-propose-to-hub acts as backward-compatible alias."""
    skill_path = SKILLS_DIR / "ccba-propose-to-hub" / "SKILL.md"
    assert skill_path.exists(), "ccba-propose-to-hub SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in content
    assert "ccba-contribute-to-hub" in content


def test_ccba_new_feature_workflow_structure() -> None:
    """Verify /ccba-new-feature uses correct eval path and gh issue view auto-parsing."""
    skill_path = SKILLS_DIR / "ccba-new-feature" / "SKILL.md"
    assert skill_path.exists(), "ccba-new-feature SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    assert "scripts/eval/run_harness_evals.py" in content
    assert "gh issue view" in content


def test_catalog_registers_upstream_workflows() -> None:
    """Verify catalog.yaml properly registers upstream contribution skills."""
    assert CATALOG_FILE.exists(), "catalog.yaml must exist"
    data = yaml.safe_load(CATALOG_FILE.read_text(encoding="utf-8"))

    skills = {s["name"]: s for s in data.get("skills", [])}
    assert "ccba-issue-to-hub" in skills
    assert "ccba-contribute-to-hub" in skills
    assert "ccba-propose-to-hub" in skills

    # Verify paths exist on disk
    for skill_name in ["ccba-issue-to-hub", "ccba-contribute-to-hub", "ccba-propose-to-hub"]:
        skill_entry = skills[skill_name]
        skill_file = REPO_ROOT / skill_entry["skill_path"]
        assert skill_file.exists(), f"Skill file for {skill_name} must exist at {skill_file}"
