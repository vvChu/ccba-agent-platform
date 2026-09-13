"""Tests for Shift-Left Local CI Integration in /ccba-create-pr Workflow."""

from pathlib import Path


def test_ccba_create_pr_workflow_has_local_ci_first() -> None:
    """Verify that ccba-create-pr workflow executes local CI evals before git push."""
    hub_root = Path(__file__).resolve().parent.parent
    workflow_md = hub_root / ".agents" / "skills" / "ccba-create-pr" / "SKILL.md"
    assert workflow_md.exists(), "ccba-create-pr/SKILL.md must exist"
    content = workflow_md.read_text(encoding="utf-8")

    ci_pos = content.find("verify-patch")
    if ci_pos == -1:
        ci_pos = content.find("run_harness_evals.py")
    push_pos = content.find("git push")

    assert ci_pos != -1, "ccba-create-pr SKILL.md must reference verification gate"
    assert push_pos != -1, "ccba-create-pr SKILL.md must reference git push"
    assert ci_pos < push_pos, (
        "Local CI check must appear BEFORE git push in workflow"
    )
