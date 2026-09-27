"""test_simulators_modular.py - Unit tests for Modular Dual-Dispatch Simulators.

Verifies:
1. Dispatcher instantiation and registration of all 17 CCBA Domain Archetypes.
2. Complete immunity to prompt hijacking when skill_name is provided.
3. Backwards compatibility for empty skill_name via multi-tier fallback cascade.
4. Direct simulation across individual domain simulators.
"""

from __future__ import annotations

from ccba_harness.evals.models import EvalItem
from ccba_harness.evals.simulation import build_mock_agent_task, create_domain_mock_agent_task
from ccba_harness.evals.simulators import (
    BaseDomainSimulator,
    SimulationContext,
    SimulatorDispatcher,
)


def test_dispatcher_registry_all_17_archetypes() -> None:
    """Verify SimulatorDispatcher registers exactly all 17 domain archetypes plus fallback."""
    dispatcher = SimulatorDispatcher()
    expected_archetypes = {
        "grilling",
        "adr",
        "risk",
        "skill_repair",
        "legal_tooling",
        "legal",
        "tech_qc",
        "academic",
        "office",
        "visual_design",
        "visual",
        "bim_governance",
        "bim_rase",
        "bim",
        "coding",
        "platform_tooling",
        "orchestration",
    }
    assert set(dispatcher.simulators.keys()) == expected_archetypes
    for name, sim in dispatcher.simulators.items():
        assert isinstance(sim, BaseDomainSimulator)
        assert sim.archetype_name == name


def test_prompt_hijacking_immunity_tier1() -> None:
    """Verify that when skill_name is provided, prompt keywords CANNOT hijack the domain.

    Prompt contains 'Introduction' (academic trigger), 'redis' (grilling trigger),
    and '136/2020' (legal trap trigger), but skill_name is 'ccba-api-circuit-breaker' (platform_tooling).
    Tier 1 must route to platform_tooling without hijacking.
    """
    task = build_mock_agent_task(
        content="Rate limiter + Circuit Breaker pattern. references/guide.md",
        skill_name="ccba-api-circuit-breaker",
    )
    item = EvalItem(
        id="hijack_test_1",
        input_prompt="Draft an Introduction for circuit breaker with redis and 136/2020 cooldown",
    )
    output = task(item)

    # Must contain circuit breaker / platform tooling content
    assert "CIRCUIT BREAKER" in output.upper() or "RATE LIMIT" in output.upper()
    # Must NOT contain Academic CARS Swales response
    assert "John Swales" not in output
    assert "Move 1 (Establish Territory)" not in output
    # Must NOT contain Socrates grilling response
    assert "Grilling Socrates" not in output
    assert "Phỏng Vấn Dồn Dập" not in output


def test_prompt_hijacking_immunity_coding_domain() -> None:
    """Verify coding skills are not hijacked by academic keywords in prompt."""
    task = build_mock_agent_task(
        content="Hard Completion Lock ADR-0058 python -m ccba_harness verify-patch. KISS discipline.",
        skill_name="ccba-codebase-engineering",
    )
    item = EvalItem(
        id="hijack_test_2",
        input_prompt="Write an Introduction section for the refactor of this module",
    )
    output = task(item)

    assert "Codebase Engineering Discipline" in output or "verify-patch" in output
    assert "John Swales" not in output


def test_empty_skill_name_fallback_tier3_anchors() -> None:
    """Verify that legacy calls without skill_name resolve via Tier 3 Content/Prompt anchors."""
    # 1. Legal redteam trap
    legal_task = build_mock_agent_task(
        content="Nghị định 105/2025 thay thế 136/2020. Luật số 135/2025.",
        skill_name="",
    )
    res_legal = legal_task(
        EvalItem(id="leg_1", input_prompt="Trích dẫn Nghị định 136/2020 về thẩm duyệt PCCC")
    )
    assert "105/2025" in res_legal
    assert "136/2020" in res_legal

    # 2. Academic CARS trap
    acad_task = build_mock_agent_task(
        content="CARS 3-Move Blueprint. Yale Style Guide.",
        skill_name="",
    )
    res_acad = acad_task(
        EvalItem(id="acad_1", input_prompt="Draft academic Introduction discussion")
    )
    assert "Move 1" in res_acad or "CARS" in res_acad

    # 3. BIM Uniclass trap
    bim_task = build_mock_agent_task(
        content="BIM Uniclass 200 ISO 12006-2.",
        skill_name="",
    )
    res_bim = bim_task(EvalItem(id="bim_1", input_prompt="Phân loại Uniclass vật tư"))
    assert "Uniclass" in res_bim or "ISO" in res_bim or "BIM" in res_bim


def test_fallback_golden_answer() -> None:
    """Verify Tier 4 fallback returns item golden_answer when provided."""
    task = build_mock_agent_task(content="Generic prompt without domain markers", skill_name="")
    item = EvalItem(
        id="fallback_1",
        input_prompt="Some unknown prompt",
        golden_answer="Exact Expected Output 42",
    )
    output = task(item)
    assert output == "Exact Expected Output 42"


def test_alias_parity() -> None:
    """Verify create_domain_mock_agent_task is an exact functional alias of build_mock_agent_task."""
    assert create_domain_mock_agent_task is build_mock_agent_task


def test_simulation_context_wrapping() -> None:
    """Verify SimulationContext wraps core text with XML and links when configured."""
    ctx = SimulationContext(
        content="references/guide.md",
        skill_name="ccba-legal-advisor",
        has_legal_grounding=True,
        is_legal_advisory=True,
        has_xml=True,
        has_guardrail=True,
        has_pccc_guardrail=False,
        has_academic_grounding=False,
        has_academic_bibtex=False,
        has_cars_stems=False,
        has_progressive_links=True,
    )
    wrapped = ctx.wrap_response("Core Analysis Body")
    assert "<legal_context>" in wrapped
    assert "Core Analysis Body" in wrapped
    assert "<legal_citation>" in wrapped
    assert "<compliance_verdict>" in wrapped
    assert "references/guide.md" in wrapped


def test_tuner_mutators_all_17_archetypes() -> None:
    """Verify GitRatchetOptimizer proposes specialized mutation strategies across all 17 archetypes."""
    from ccba_harness.evals.archetypes import DOMAIN_ARCHETYPES
    from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

    base_skill = "# Test Skill Content\n\nBasic instructions."

    for arch in DOMAIN_ARCHETYPES:
        representative_skill = f"ccba-{arch.keywords[0]}"
        cfg = RatchetConfig(target_file="test/SKILL.md", skill_name=representative_skill)
        opt = GitRatchetOptimizer(cfg, dry_run_git=True)

        mutated = opt.propose_mutation(base_skill, iteration=1)
        assert mutated != base_skill, (
            f"Mutation failed to propose changes for archetype {arch.name}"
        )
        assert "## " in mutated, f"Mutation missing section header for archetype {arch.name}"
