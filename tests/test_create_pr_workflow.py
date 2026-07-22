"""Tests for Shift-Left Local CI Integration in /ccba-create-pr Workflow."""

from pathlib import Path


def test_ccba_create_pr_workflow_has_local_ci_first() -> None:
    """Verify that ccba-create-pr workflow executes local CI evals before git push."""
    workflow_md = Path("d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-create-pr.md")
    assert workflow_md.exists(), "ccba-create-pr.md must exist"
    content = workflow_md.read_text(encoding="utf-8")

    ci_pos = content.find("run_harness_evals.py")
    push_pos = content.find("git push")

    assert ci_pos != -1, "ccba-create-pr.md must reference run_harness_evals.py"
    assert push_pos != -1, "ccba-create-pr.md must reference git push"
    assert ci_pos < push_pos, (
        "Local CI check (run_harness_evals.py) must appear BEFORE git push in workflow"
    )
