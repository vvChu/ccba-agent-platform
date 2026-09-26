"""test_tuner_ssot_fix.py - Regression tests for Tuner SSOT Archetype routing & Heading Inversion prevention."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals.archetypes import (
    resolve_domain_archetype,
    resolve_domain_dataset,
)
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    RatchetConfig,
)
from ccba_harness.verifier import resolve_preset_commands

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_bigbim_skills_ssot_archetype_routing() -> None:
    """Verify bigbim skills are cleanly partitioned: classification -> bim, governance -> bim_governance, rase -> bim_rase."""
    # bigbim-classification must route to bim / eval_bigbim_classification.json
    arch_class = resolve_domain_archetype("bigbim-classification")
    assert arch_class is not None
    assert arch_class.name == "bim"
    assert resolve_domain_dataset("bigbim-classification") == "eval_bigbim_classification.json"

    # bigbim-governance must route to bim_governance / eval_bigbim_governance.json
    arch_gov = resolve_domain_archetype("bigbim-governance")
    assert arch_gov is not None
    assert arch_gov.name == "bim_governance"
    assert resolve_domain_dataset("bigbim-governance") == "eval_bigbim_governance.json"

    # bigbim-rase must route to bim_rase / eval_bigbim_rase.json
    arch_rase = resolve_domain_archetype("bigbim-rase")
    assert arch_rase is not None
    assert arch_rase.name == "bim_rase"
    assert resolve_domain_dataset("bigbim-rase") == "eval_bigbim_rase.json"

    # bigbim-risk must route to risk
    arch_risk = resolve_domain_archetype("bigbim-risk")
    assert arch_risk is not None
    assert arch_risk.name == "risk"
    assert resolve_domain_dataset("bigbim-risk") == "eval_bigbim_risk.json"

    # bigbim-vbpl-digest must route to legal
    arch_vbpl = resolve_domain_archetype("bigbim-vbpl-digest")
    assert arch_vbpl is not None
    assert arch_vbpl.name == "legal"
    assert resolve_domain_dataset("bigbim-vbpl-digest") == "eval_legal_intel.json"


def test_propose_mutation_coding_no_unsolicited_adr_matrix_token(tmp_path: Path) -> None:
    """Verify propose_mutation for coding skills does not inject raw ADR-0058 token in heading."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: ccba-append-only-logger\n---\n# Logger Pattern\n"
    target.write_text(base_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-append-only-logger")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    mut = tuner.propose_mutation(base_content, 1)

    # Must contain Hard Completion Lock heading WITHOUT (ADR-0058)
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất\n" in mut
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)" not in mut
    # Must still contain required verify-patch command for scorer
    assert "python -m ccba_harness verify-patch" in mut


def test_propose_mutation_headings_have_no_hardcoded_numbers(tmp_path: Path) -> None:
    """Verify all domain strategy headings use semantic headings without numeric prefixes."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: test-skill\n---\n# Test Skill\n"
    target.write_text(base_content, encoding="utf-8")

    domains = [
        "ccba-academic-writing",
        "bigbim-governance",
        "bigbim-rase",
        "bigbim-classification",
        "ccba-code-review",
        "ccba-ai-qc-pccc-audit",
        "ccba-legal-intel",
        "ccba-generic-fallback",
    ]
    for skill_name in domains:
        cfg = RatchetConfig(target_file=str(target), skill_name=skill_name)
        tuner = GitRatchetOptimizer(cfg, dry_run_git=True)
        for it in range(1, 5):
            mut = tuner.propose_mutation(base_content, it)
            lines = mut.splitlines()
            h2_lines = [line.strip() for line in lines if line.strip().startswith("## ")]
            for h in h2_lines:
                # Must not start with ## 1., ## 2., ## 4., etc.
                assert not any(h.startswith(f"## {num}.") for num in range(1, 10)), (
                    f"Found numeric heading '{h}' in {skill_name} iteration {it}"
                )


def test_preset_skill_includes_adr_matrix_check() -> None:
    """Verify resolve_preset_commands('skill') includes sync_hub_adr_matrix.py --check for CI parity."""
    cmds = resolve_preset_commands("skill")
    assert any("sync_hub_adr_matrix.py --check" in c for c in cmds)


def test_skill_repair_ssot_archetype_routing() -> None:
    """Verify ccba-skill-repair routes to dedicated skill_repair archetype and eval_skill_repair.json."""
    from ccba_harness.evals.archetypes import get_default_domain_scorers
    from ccba_harness.evals.runner import load_eval_dataset

    arch = resolve_domain_archetype("ccba-skill-repair")
    assert arch is not None
    assert arch.name == "skill_repair"
    assert resolve_domain_dataset("ccba-skill-repair") == "eval_skill_repair.json"

    # Verify scorers
    scorers = get_default_domain_scorers("ccba-skill-repair")
    scorer_names = [s.name for s in scorers]
    assert "skill_repair_gpi_and_frontmatter" in scorer_names
    assert "skill_repair_anti_trap_hard_floor" in scorer_names
    assert "skill_repair_debloat_and_verification" in scorer_names
    assert "depth" in scorer_names

    # Verify dataset loading
    items = load_eval_dataset(skill_name="ccba-skill-repair")
    assert len(items) == 5
    item_ids = [it.id for it in items]
    assert "test_skill_repair_yaml_syntax_triage" in item_ids
    assert "test_skill_repair_gate0_gate1_classification" in item_ids
    assert "test_skill_repair_gpi_calculation_and_patching" in item_ids
    assert "test_skill_repair_completion_criteria_and_relative_links" in item_ids
    assert "test_skill_repair_mandatory_verification" in item_ids


def test_visual_design_ssot_archetype_routing() -> None:
    """Verify ccba-design routes to dedicated visual_design archetype and eval_visual_design.json."""
    from ccba_harness.evals.archetypes import get_default_domain_scorers
    from ccba_harness.evals.runner import load_eval_dataset

    # Verify visual design skills route to visual_design
    for sname in ["ccba-design", "ccba-brand", "ccba-logo", "ccba-banner", "ccba-cip"]:
        arch = resolve_domain_archetype(sname)
        assert arch is not None, f"{sname} should resolve to an archetype"
        assert arch.name == "visual_design", f"{sname} should resolve to visual_design"
        assert resolve_domain_dataset(sname) == "eval_visual_design.json"

    # Disjoint keyword invariance: ccba-codebase-design must strictly route to coding
    arch_codebase = resolve_domain_archetype("ccba-codebase-design")
    assert arch_codebase is not None
    assert arch_codebase.name == "coding"
    assert resolve_domain_dataset("ccba-codebase-design") == "eval_codebase_engineering.json"

    # Verify scorers
    scorers = get_default_domain_scorers("ccba-design")
    scorer_names = [s.name for s in scorers]
    assert "visual_design_tokens_and_colors" in scorer_names
    assert "visual_design_brand_and_guidelines" in scorer_names
    assert "visual_design_typography_and_assets" in scorer_names
    assert "depth" in scorer_names

    # Check critical flag
    brand_scorer = next(s for s in scorers if s.name == "visual_design_brand_and_guidelines")
    assert brand_scorer.is_critical is True

    # Verify dataset loading
    items = load_eval_dataset(skill_name="ccba-design")
    assert len(items) == 5
    item_ids = [it.id for it in items]
    assert "test_visual_design_color_palette_tokens" in item_ids
    assert "test_visual_design_typography_hierarchy_scale" in item_ids
    assert "test_visual_design_logo_guidelines_safe_zone" in item_ids
    assert "test_visual_design_banner_prompt_specifications" in item_ids
    assert "test_visual_design_cip_corporate_identity_program" in item_ids


@pytest.mark.asyncio
async def test_visual_design_simulation_mock_task_and_scoring() -> None:
    """Verify build_mock_agent_task generates authentic visual_design responses scoring 100% across all 5 benchmark items."""
    from pathlib import Path

    from ccba_harness.evals.archetypes import get_default_domain_scorers
    from ccba_harness.evals.runner import load_eval_dataset
    from ccba_harness.evals.simulation import build_mock_agent_task

    skill_path = Path(".agents/skills/ccba-design/SKILL.md")
    content = (
        skill_path.read_text(encoding="utf-8")
        if skill_path.exists()
        else "ccba-design skill content"
    )
    dataset = load_eval_dataset(skill_name="ccba-design")
    assert len(dataset) == 5

    task = build_mock_agent_task(content, "ccba-design")
    scorers = get_default_domain_scorers("ccba-design")

    for item in dataset:
        output = task(item)
        assert "<legal_context>" not in output, f"Legal context leaked into {item.id}"
        assert "Uniclass" not in output, f"BIM Uniclass hijacked {item.id}"
        assert "Nghị định 30" not in output, f"Office hijacked {item.id}"
        assert "Quy chuẩn Thiết kế Thị giác" in output, f"Visual design not matched for {item.id}"

        # Score the output against all 4 domain scorers
        for s in scorers:
            res = await s.score(output, item)
            assert not res.is_critical_fail, f"Critical failure on {s.name} for {item.id}"
            assert res.score == 1.0, f"Expected 1.0 on {s.name} for {item.id}, got {res.score}"


def test_office_ssot_archetype_routing() -> None:
    """Verify all 5 office skills route to office archetype and eval_copywriting.json."""
    from ccba_harness.evals.archetypes import get_default_domain_scorers
    from ccba_harness.evals.runner import load_eval_dataset

    office_skills = [
        "ccba-copywriting",
        "ccba-markdown-document-processing",
        "ccba-pptx",
        "ccba-seminar-builder",
        "ccba-xu-ly-van-phong",
    ]
    for sname in office_skills:
        arch = resolve_domain_archetype(sname)
        assert arch is not None, f"{sname} should resolve to an archetype"
        assert arch.name == "office", f"{sname} should resolve to office"
        assert resolve_domain_dataset(sname) == "eval_copywriting.json"

    # Verify scorers
    scorers = get_default_domain_scorers("ccba-copywriting")
    scorer_names = [s.name for s in scorers]
    assert "office_standard" in scorer_names
    assert "progressive_disclosure_links" in scorer_names
    assert "anti_debris" in scorer_names
    assert "depth" in scorer_names

    # Verify dataset loading
    items = load_eval_dataset(skill_name="ccba-copywriting")
    assert len(items) == 5
    item_ids = [it.id for it in items]
    assert "test_office_administrative_document_format_nd30" in item_ids
    assert "test_office_markdown_table_standardization" in item_ids
    assert "test_office_presentation_slide_outline_structure" in item_ids
    assert "test_office_seminar_curriculum_and_agenda" in item_ids
    assert "test_office_bim_technical_copywriting_and_article" in item_ids


@pytest.mark.asyncio
async def test_office_copywriting_simulation_mock_task_and_scoring() -> None:
    """Verify build_mock_agent_task generates authentic office responses scoring 100% across all 5 benchmark items."""
    from pathlib import Path

    from ccba_harness.evals.archetypes import get_default_domain_scorers
    from ccba_harness.evals.runner import load_eval_dataset
    from ccba_harness.evals.simulation import build_mock_agent_task

    skill_path = Path(".agents/skills/ccba-copywriting/SKILL.md")
    content = (
        skill_path.read_text(encoding="utf-8")
        if skill_path.exists()
        else "ccba-copywriting skill content"
    )
    dataset = load_eval_dataset(skill_name="ccba-copywriting")
    assert len(dataset) == 5

    task = build_mock_agent_task(content, "ccba-copywriting")
    scorers = get_default_domain_scorers("ccba-copywriting")

    for item in dataset:
        output = task(item)
        assert "<legal_context>" not in output, f"Legal context leaked into {item.id}"
        assert "Uniclass" not in output, f"BIM Uniclass hijacked {item.id}"
        assert "Quy chuẩn Thiết kế Thị giác" not in output, f"Visual design hijacked {item.id}"

        # Score the output against all 4 domain scorers
        for s in scorers:
            res = await s.score(output, item)
            assert not res.is_critical_fail, f"Critical failure on {s.name} for {item.id}"
            assert res.score == 1.0, f"Expected 1.0 on {s.name} for {item.id}, got {res.score}"
