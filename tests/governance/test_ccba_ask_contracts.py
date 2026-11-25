"""Deterministic contract tests protecting /ccba-ask v1.4.0 and /ccba-knowledge-loop v1.2.0.

Locks empirically-grounded invariants introduced after the 543-transcript activation audit:
- Read-Only Consultation (Mention != Invoke) lock in ccba-ask/SKILL.md
- Mandatory delegation_matrix.md load directive & preserved ADR-0035 / run_workflow safety locks
- Top-20 live skill map coverage & LF token budget ceiling
- Zero Spoke-specific residue (vvc-notes / Command.md / Friday Alpha Arena)
- Host slash command allowlist (/plan, /teamwork, /swarm) & full directory audit cleanliness
- Single-session vs multi-source boundary & After-Friction Hook in ccba-knowledge-loop
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ccba_harness._skill_content_checks import ALLOWED_HOST_COMMANDS
from ccba_harness.economy import count_skill_tokens_lf
from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
ASK_DIR = HUB_ROOT / ".agents" / "skills" / "ccba-ask"
ASK_SKILL = ASK_DIR / "SKILL.md"
KNOWLEDGE_LOOP_SKILL = HUB_ROOT / ".agents" / "skills" / "ccba-knowledge-loop" / "SKILL.md"


def test_ccba_ask_read_only_lock_and_legacy_triggers() -> None:
    """Verify ccba-ask v1.4.0 enforces Mention != Invoke and preserves coordinator alias triggers."""
    content = ASK_SKILL.read_text(encoding="utf-8")
    assert "Mention ≠ Invoke" in content
    assert "CHỈ TƯ VẤN" in content
    assert "references/delegation_matrix.md" in content
    assert (
        "repo hiện tại (Hub/nội bộ Spoke) qua [`/ccba-create-pr`](../ccba-create-pr/SKILL.md); "
        "chỉ đóng góp ngược Spoke → Hub qua [`/ccba-contribute-to-hub`](../ccba-contribute-to-hub/SKILL.md)"
    ) in content

    fm = yaml.safe_load(content.split("---", 2)[1]) or {}
    triggers = set(fm.get("triggers", []))
    for required_alias in ("ccba-wait-what", "wait-what", "ccba-brainstorm", "brainstorm"):
        assert required_alias in triggers, f"Missing coordinator alias trigger: {required_alias}"


def test_ccba_ask_top_skills_coverage_and_token_ceiling() -> None:
    """Verify ccba-ask/SKILL.md covers top-used skills while remaining below its 4013 LF token cap."""
    content = ASK_SKILL.read_text(encoding="utf-8")
    tokens = count_skill_tokens_lf(content)
    assert tokens <= 4013, f"ccba-ask/SKILL.md exceeded token ceiling: {tokens} > 4013"

    required_skills = (
        "/ccba-release-feature",
        "/ccba-update-spoke",
        "/ccba-wayfinder",
        "/ccba-review-proposal",
        "/ccba-create-verification-skill",
        "/ccba-research",
        "/ccba-xia",
        "/ccba-code-review",
        "/ccba-youtube-learn",
    )
    missing = [cmd for cmd in required_skills if cmd not in content]
    assert not missing, f"ccba-ask/SKILL.md is missing top real-world skills: {missing}"


def test_ccba_ask_zero_spoke_leakage_and_delegation_locks() -> None:
    """Verify zero vvc-notes Spoke leakage and verbatim safety locks in delegation_matrix.md."""
    forbidden_tokens = ("Command.md", "Friday Alpha Arena", "Adversarial Twin Mode", "vvc-notes")
    for md_file in sorted(ASK_DIR.rglob("*.md")):
        if ".skill_versions" in md_file.parts:
            continue
        text = md_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"Spoke-specific token '{token}' leaked into {md_file}"

    delegation_md = (ASK_DIR / "references" / "delegation_matrix.md").read_text(encoding="utf-8")
    for lock in (
        "ADR-0035",
        "depth limit = 1",
        'type_name="research"',
        'workspace="inherit"',
        "view_file",
        "grep_search",
        "read_resource",
        "finish",
        "apply_worker_patch.py",
    ):
        assert lock in delegation_md, f"Missing delegation safety lock '{lock}'"


def test_host_commands_allowlist_and_ccba_ask_directory_audit() -> None:
    """Verify /plan, /teamwork, /swarm are allowlisted and ccba-ask passes full directory audit."""
    for host_cmd in ("/plan", "/teamwork", "/swarm"):
        assert host_cmd in ALLOWED_HOST_COMMANDS, f"Missing host command in allowlist: {host_cmd}"

    builtin_ref = (ASK_DIR / "references" / "builtin_vs_ccba.md").read_text(encoding="utf-8")
    for host_cmd in ("`/plan`", "`/teamwork`", "`/swarm`"):
        assert host_cmd in builtin_ref, (
            f"Expected canonical host command {host_cmd} in builtin_vs_ccba.md"
        )

    validator = SkillValidator(HUB_ROOT)
    issues = validator.audit_skill_directory(ASK_DIR)
    assert not issues, f"SkillValidator reported issues in ccba-ask: {issues}"


def test_ccba_knowledge_loop_boundary_and_after_friction_hook() -> None:
    """Verify ccba-knowledge-loop v1.2.0 clarifies boundary, loosens input_documents, and adds hook."""
    content = KNOWLEDGE_LOOP_SKILL.read_text(encoding="utf-8")
    assert count_skill_tokens_lf(content) <= 4000
    assert "Ranh giới với [`/ccba-ask`]" in content
    assert "không bắt buộc sao chép sang `input_documents/`" in content
    assert "After-Friction Hook" in content
    assert "Single-Writer" in content
