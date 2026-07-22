"""Tests for Agent Execution Guardrails and Scoped Test Policy in CCBA Platform."""

from pathlib import Path


def test_agents_md_has_scoped_test_guardrail() -> None:
    """Verify that AGENTS.md enforces scoped test execution rules."""
    agents_md = Path("d:/GitHubProjects/ccba-agent-platform/.agents/AGENTS.md")
    assert agents_md.exists(), "AGENTS.md must exist in .agents/"
    content = agents_md.read_text(encoding="utf-8")

    assert "Scoped Test Execution" in content, (
        "AGENTS.md must contain Scoped Test Execution Guardrail rule"
    )
    assert "Bounded Async Task" in content, (
        "AGENTS.md must contain Bounded Async Task Handling rule"
    )


def test_eval_gate_skill_has_scoped_test_guidance() -> None:
    """Verify that eval-gate SKILL.md provides scoped test path guidance."""
    eval_gate_md = Path("d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/SKILL.md")
    assert eval_gate_md.exists(), "eval-gate/SKILL.md must exist"
    content = eval_gate_md.read_text(encoding="utf-8")

    assert "khoanh vùng" in content.lower() or "scoped" in content.lower(), (
        "eval-gate/SKILL.md must instruct scoped test execution"
    )
