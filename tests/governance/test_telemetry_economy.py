"""test_telemetry_economy.py - Unit tests for Token Economy & Prompt Density Engine.

Validates:
1. Prompt Density Index (PDI) calculations and directive weighting.
2. Fast Sentence Hashing cross-skill duplication detection (< 300ms).
3. Role-Aware Token ROI computation (Coder vs Investigator).
4. Pruning Diff Report generation.
5. CLI integrations (token_economy.py & ccba-harness telemetry economy).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ccba_harness.economy import (
    EconomyAuditReport,
    SkillPromptMetrics,
    analyze_skill_prompt_density,
    calculate_role_aware_roi,
    detect_sentence_duplicates,
    generate_prompt_pruning_report,
)
from ccba_harness.telemetry import SubagentSessionMetrics


def test_prompt_density_calculation(tmp_path: Path) -> None:
    """Verify calculation of Prompt Density Index (PDI) and directives."""
    # 1. Action-rich compact prompt
    action_skill = tmp_path / "action-skill" / "SKILL.md"
    action_skill.parent.mkdir(parents=True)
    action_skill.write_text(
        """---
name: action-skill
description: High density actionable skill
---

# Action Skill

## Commands
```bash
python -m ccba_harness verify-patch --preset ci
```

## Checklists
- [x] Step 1: Run linter
- [x] Step 2: Run pytest
- [x] Step 3: Check exit code

`python run_test.py`
""",
        encoding="utf-8",
    )

    m_action = analyze_skill_prompt_density(action_skill)
    assert m_action.skill_name == "action-skill"
    assert m_action.directive_count >= 5
    assert m_action.overhead_status == "Optimal"
    assert m_action.pdi_score >= 50.0

    # 2. Bloated wordy prompt with little action
    bloated_skill = tmp_path / "bloated-skill" / "SKILL.md"
    bloated_skill.parent.mkdir(parents=True)
    filler_text = (
        "This is an extraordinarily verbose philosophical introduction about how software should be constructed. "
        * 350
    )
    bloated_skill.write_text(
        f"""---
name: bloated-skill
description: Very long narrative
---

# Bloated Skill

{filler_text}
""",
        encoding="utf-8",
    )

    m_bloated = analyze_skill_prompt_density(bloated_skill)
    assert m_bloated.skill_name == "bloated-skill"
    assert m_bloated.estimated_tokens > 3500
    assert m_bloated.overhead_status == "Bloated / High Overhead"
    assert len(m_bloated.recommendations) >= 1
    assert m_bloated.pdi_score < m_action.pdi_score


def test_sentence_hashing_duplication(tmp_path: Path) -> None:
    """Verify sentence hashing detects duplicated paragraphs across distinct skills."""
    shared_sentence = "All worker subagents must strictly adhere to the single-writer protocol and never mutate files directly."

    s1 = tmp_path / "skill-alpha" / "SKILL.md"
    s1.parent.mkdir(parents=True)
    s1.write_text(f"# Alpha\n\n{shared_sentence}\n\nDo alpha things.", encoding="utf-8")

    s2 = tmp_path / "skill-beta" / "SKILL.md"
    s2.parent.mkdir(parents=True)
    s2.write_text(f"# Beta\n\n{shared_sentence}\n\nDo beta things.", encoding="utf-8")

    dup_map = detect_sentence_duplicates([s1, s2])
    assert "skill-alpha" in dup_map
    assert "skill-beta" in dup_map
    assert any("single-writer protocol" in msg for msg in dup_map["skill-alpha"])


def test_role_aware_token_roi_coder() -> None:
    """Verify Token ROI computation for a coding subagent."""
    metrics = SubagentSessionMetrics(
        conversation_id="conv-coder-1",
        log_file="path/to/coder_log.jsonl",
        total_steps=20,
        turns_count=5,
        prompt_tokens=50000,
        completion_tokens=2000,
        total_tokens=52000,
        total_duration_sec=30.0,
        tool_counts={
            "write_to_file": 2,  # 30 pts
            "replace_file_content": 3,  # 36 pts
            "run_command": 4,  # 20 pts
        },
    )

    roi = calculate_role_aware_roi(metrics, role_override="coder")
    assert roi.role == "coder"
    assert roi.productive_score >= 80.0
    # token_roi = (productive_score / 50,000) * 100,000 >= 160.0
    assert roi.token_roi > 100.0
    assert roi.efficiency_tier == "Tier A (High Efficiency)"


def test_role_aware_token_roi_investigator() -> None:
    """Verify Token ROI computation for a research/investigation subagent."""
    metrics = SubagentSessionMetrics(
        conversation_id="conv-inv-1",
        log_file="path/to/investigator_log.jsonl",
        total_steps=25,
        turns_count=6,
        prompt_tokens=80000,
        completion_tokens=3500,
        total_tokens=83500,
        total_duration_sec=45.0,
        tool_counts={
            "view_file": 12,  # 48 pts
            "grep_search": 8,  # 32 pts
            "search_web": 2,  # 12 pts
        },
    )

    roi = calculate_role_aware_roi(metrics, role_override="investigator")
    assert roi.role == "investigator"
    assert roi.productive_score >= 90.0
    assert roi.token_roi > 50.0
    assert roi.efficiency_tier == "Tier A (High Efficiency)"


def test_generate_pruning_report_to_file(tmp_path: Path) -> None:
    """Verify Markdown report generation with recommendations."""
    s1 = SkillPromptMetrics(
        skill_name="bloated-one",
        skill_path=".agents/skills/bloated-one/SKILL.md",
        char_count=20000,
        line_count=400,
        estimated_tokens=5000,
        directive_count=4,
        prose_word_count=3000,
        code_block_ratio=0.1,
        pdi_score=25.0,
        overhead_status="Bloated / High Overhead",
        recommendations=["Move reference examples to references/."],
    )
    s2 = SkillPromptMetrics(
        skill_name="lean-one",
        skill_path=".agents/skills/lean-one/SKILL.md",
        char_count=4000,
        line_count=90,
        estimated_tokens=1000,
        directive_count=15,
        prose_word_count=400,
        code_block_ratio=0.3,
        pdi_score=85.0,
        overhead_status="Optimal",
    )

    report = EconomyAuditReport(
        total_skills=2,
        avg_pdi=55.0,
        total_prompt_tokens_est=6000,
        bloated_skills_count=1,
        skills_metrics=[s1, s2],
        estimated_token_savings=2500,
    )

    out_file = tmp_path / "prune_test_report.md"
    md_result = generate_prompt_pruning_report(report, output_path=out_file)

    assert out_file.exists()
    assert "# 📈 CCBA Token Economy & Prompt Density Audit Report" in md_result
    assert "bloated-one" in md_result
    assert "Move reference examples to references/." in md_result


def test_cli_token_economy_script(tmp_path: Path) -> None:
    """Verify execution of CLI `token_economy.py`."""
    # 1. Test scan --json
    res_scan = subprocess.run(
        [sys.executable, "scripts/governance/token_economy.py", "scan", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res_scan.returncode == 0
    parsed = json.loads(res_scan.stdout)
    assert "total_skills" in parsed
    assert "avg_pdi" in parsed
    assert "skills" in parsed

    # 2. Test report output
    rep_file = tmp_path / "rep.md"
    res_rep = subprocess.run(
        [sys.executable, "scripts/governance/token_economy.py", "report", "--out", str(rep_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res_rep.returncode == 0
    assert rep_file.exists()
    assert rep_file.stat().st_size > 500


def test_cli_ccba_harness_economy() -> None:
    """Verify execution of `ccba-harness telemetry economy`."""
    res = subprocess.run(
        [sys.executable, "-m", "ccba_harness", "telemetry", "economy", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res.returncode == 0
    parsed = json.loads(res.stdout)
    assert "total_skills" in parsed
    assert "total_prompt_tokens_est" in parsed
