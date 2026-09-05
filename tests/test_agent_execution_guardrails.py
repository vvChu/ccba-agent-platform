"""Tests for Agent Execution Guardrails and Scoped Test Policy in CCBA Platform."""

from pathlib import Path


def test_agents_md_has_scoped_test_guardrail() -> None:
    """Verify that AGENTS.md links to and enforces scoped test execution rules."""
    root = Path(__file__).resolve().parent.parent
    agents_md = root / ".agents/AGENTS.md"
    assert agents_md.exists(), "AGENTS.md must exist in .agents/"
    content = agents_md.read_text(encoding="utf-8")

    guardrails_doc = root / "docs/rules/execution_guardrails.md"
    assert guardrails_doc.exists(), "execution_guardrails.md must exist in docs/rules/"
    guardrails_content = guardrails_doc.read_text(encoding="utf-8")

    assert "execution_guardrails.md" in content, (
        "AGENTS.md must link to execution_guardrails.md under Progressive Disclosure"
    )
    assert "Scoped Test Execution" in guardrails_content, (
        "execution_guardrails.md must contain Scoped Test Execution Guardrail rule"
    )
    assert "Bounded Async Task" in guardrails_content, (
        "execution_guardrails.md must contain Bounded Async Task Handling rule"
    )


def test_eval_gate_skill_has_scoped_test_guidance() -> None:
    """Verify that eval-gate SKILL.md provides scoped test path guidance."""
    root = Path(__file__).resolve().parent.parent
    eval_gate_md = root / ".agents/skills/ccba-eval-gate/SKILL.md"
    assert eval_gate_md.exists(), "ccba-eval-gate/SKILL.md must exist"
    content = eval_gate_md.read_text(encoding="utf-8")

    assert "khoanh vùng" in content.lower() or "scoped" in content.lower(), (
        "eval-gate/SKILL.md must instruct scoped test execution"
    )
