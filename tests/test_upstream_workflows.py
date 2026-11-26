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
    assert "/ccba-new-feature #[ISSUE_ID]" in content
    assert "/ccba-create-pr" in content
    assert "/ccba-release-feature" in content
    assert "/ccba-contribute-to-hub --issue #[ISSUE_ID]" in content


def test_ccba_release_feature_software_spoke_gates() -> None:
    """Verify /ccba-release-feature separates Software Spoke gates and guards process_safety."""
    skill_path = SKILLS_DIR / "ccba-release-feature" / "SKILL.md"
    assert skill_path.exists(), "ccba-release-feature SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    assert "scripts/validate_legal_spoke.py" in content
    assert ".agents/skills/verify-<spoke>/harness/runner.py" in content
    assert "scripts/_guardrails/check_spoke_cleanliness.py" in content
    assert "CCBA_HUB_PATH" in content
    assert "scripts/eval/process_safety.py" in content
    assert (
        "Spoke:** `python scripts/validate_legal_spoke.py` hoặc `python scripts/eval/run_isolated_tests.py --all`"
        not in content
    )


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
    """Verify propose-to-hub acts as backward-compatible reference in ccba-contribute-to-hub."""
    ref_path = SKILLS_DIR / "ccba-contribute-to-hub" / "references" / "propose_to_hub.md"
    assert ref_path.exists(), "propose_to_hub.md reference must exist"

    content = (SKILLS_DIR / "ccba-contribute-to-hub" / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in content
    assert "propose-to-hub" in content or "ccba-propose-to-hub" in content


def test_ccba_new_feature_workflow_structure() -> None:
    """Verify /ccba-new-feature uses correct eval path, v1.4.0 triage and peer claim locking."""
    skill_path = SKILLS_DIR / "ccba-new-feature" / "SKILL.md"
    assert skill_path.exists(), "ccba-new-feature SKILL.md must exist"

    content = skill_path.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(content.split("---", 2)[1])
    version_parts = tuple(int(part) for part in str(frontmatter["metadata"]["version"]).split("."))
    assert version_parts >= (1, 5, 2)
    assert "git symbolic-ref --short refs/remotes/origin/HEAD" in content
    assert 'if [ "$b" != "<default_branch>" ]; then git branch -d "$b"; fi' in content
    assert "triage" in content
    assert "backlog" in content
    assert "claim issue" in content
    assert "scripts/eval/run_harness_evals.py" in content
    assert "gh issue view" in content
    assert "gh issue list" in content
    assert "--state open" in content
    assert "--json number,title,labels,assignees,updatedAt" in content
    assert "[P0]" in content and "[P1]" in content and "[P2]" in content and "[P3]" in content
    assert "CCBA_PEER_CLAIM_LOCK" in content
    assert "--remove-assignee" in content
    assert "git show-ref" in content
    assert "Untrusted Data Block" in content
    assert (
        "Thu thập đầy đủ phạm vi yêu cầu từ Issue hoặc phỏng vấn người dùng, hoàn tất Claim Lock hợp lệ nếu chọn từ Backlog."
        in content
    )


def test_catalog_registers_upstream_workflows() -> None:
    """Verify catalog.yaml properly registers upstream contribution skills."""
    assert CATALOG_FILE.exists(), "catalog.yaml must exist"
    data = yaml.safe_load(CATALOG_FILE.read_text(encoding="utf-8"))

    skills = {s["name"]: s for s in data.get("skills", [])}
    assert "ccba-issue-to-hub" in skills
    assert "ccba-contribute-to-hub" in skills

    # Verify paths exist on disk
    for skill_name in ["ccba-issue-to-hub", "ccba-contribute-to-hub"]:
        skill_entry = skills[skill_name]
        skill_file = REPO_ROOT / skill_entry["skill_path"]
        assert skill_file.exists(), f"Skill file for {skill_name} must exist at {skill_file}"


SPOKE_ONLY_UPSTREAM_UNIVERSAL_SKILLS = frozenset(
    {
        "ccba-contribute-to-hub",
        "ccba-issue-to-hub",
        "ccba-promote-sandbox",
        "ccba-update-spoke",
    }
)


def test_universal_skills_pr_routing_contract() -> None:
    """Lock Hub-vs-Spoke PR routing semantics on scope: universal SKILL.md files.

    Out of scope by design:
    - scope: hub skills (ccba-graduate-rd line 130, ccba-build-skill lines 53 & 200)
    - references/ subdirectories
    """
    nf_text = (SKILLS_DIR / "ccba-new-feature" / "SKILL.md").read_text(encoding="utf-8")
    assert (
        "dùng `/ccba-create-pr` cho repo hiện tại (Hub hoặc nội bộ Spoke); "
        "chỉ dùng `/ccba-contribute-to-hub` khi đóng góp ngược từ Spoke lên Hub"
    ) in nf_text

    ask_text = (SKILLS_DIR / "ccba-ask" / "SKILL.md").read_text(encoding="utf-8")
    assert (
        "repo hiện tại (Hub/nội bộ Spoke) qua [`/ccba-create-pr`](../ccba-create-pr/SKILL.md); "
        "chỉ đóng góp ngược Spoke → Hub qua [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md)"
    ) in ask_text

    cr_text = (SKILLS_DIR / "ccba-code-review" / "SKILL.md").read_text(encoding="utf-8")
    assert (
        "Thường chạy trước:** `/ccba-create-pr` (PR repo hiện tại), "
        "`/ccba-contribute-to-hub` (Spoke→Hub)"
    ) in cr_text

    plat_text = (SKILLS_DIR / "ccba-platform" / "SKILL.md").read_text(encoding="utf-8")
    assert "| **Bối cảnh 5 & Hub Monorepo** | `/ccba-create-pr` |" in plat_text
    assert "| **Bối cảnh 5 (Spoke → Hub)** | `/ccba-contribute-to-hub` |" in plat_text
    assert "| **Bối cảnh 5 & Hub Monorepo** | `/ccba-contribute-to-hub` |" not in plat_text

    cth_text = (SKILLS_DIR / "ccba-contribute-to-hub" / "SKILL.md").read_text(encoding="utf-8")
    cth_fm = yaml.safe_load(cth_text.split("---", 2)[1]) or {}
    cth_triggers = set(cth_fm.get("triggers", []))
    assert "ccba-create-pr" not in cth_triggers
    assert "create-pr" not in cth_triggers
    assert "PR trực tiếp trên Hub hoặc nội bộ Spoke dùng `/ccba-create-pr`" in cth_text

    offenders: list[str] = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        content = skill_md.read_text(encoding="utf-8")
        if "/ccba-contribute-to-hub" not in content:
            continue
        fm = yaml.safe_load(content.split("---", 2)[1]) or {}
        if str(fm.get("scope", "")).strip().lower() != "universal":
            continue
        name = str(fm.get("name", skill_md.parent.name))
        if name not in SPOKE_ONLY_UPSTREAM_UNIVERSAL_SKILLS and "/ccba-create-pr" not in content:
            offenders.append(name)
    assert not offenders, (
        f"Universal skill(s) suggest /ccba-contribute-to-hub without /ccba-create-pr: {offenders}"
    )
