"""test_gpi_decision_framework.py - Tests for Two-Stage Decision Framework & GPI.

Tests requirements defined in Research Report RES-2026-ARCH-001 v1.2:
- Stage 1: Determinism Gate (Gate 0) and Orchestration Gate (Gate 1).
- Stage 2: Granularity & Placement Index (GPI) computation, routing, and breakdown.
- SkillValidator integration, frontmatter schema validation, and CLI commands.
"""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_harness import (
    CANONICAL_ANCHORS,
    GPI_DEADBAND_LOWER,
    GPI_DEADBAND_UPPER,
    GPI_STANDALONE_THRESHOLD,
    MAX_METRIC_SCORE,
    MIN_METRIC_SCORE,
    WEIGHT_AUTONOMOUS_INVOCATION_A,
    WEIGHT_INTERFACE_COMPLEXITY_K,
    WEIGHT_PARENT_COUPLING_P,
    WEIGHT_REASONING_STEPS_S,
    ArchitectureTier,
    CanonicalAnchor,
    DecisionRequest,
    GPIMetrics,
    SkillValidator,
    calculate_gpi,
    evaluate_two_stage_decision,
)
from ccba_harness.cli import main, run_evaluate_gpi_cli, run_skill_validation_cli


def _make_dummy_skill_md(
    name: str = "ccba-test-skill",
    extra_frontmatter: dict[str, str] | None = None,
    extra_lines: int = 30,
) -> str:
    """Helper to generate dummy skill markdown with custom frontmatter."""
    lines = [
        "---",
        f"name: {name}",
        "description: Valid description for test skill.",
        "bundle: _core",
    ]
    if extra_frontmatter:
        for k, v in extra_frontmatter.items():
            lines.append(f"{k}: {v}")
    lines.extend(
        [
            "---",
            f"# {name.title()}",
            "",
            "## Quy trình thực hiện",
            "### Bước 1: Khởi tạo",
            "Nội dung bước 1.",
            "- **Tiêu chí hoàn thành:** Sẵn sàng.",
        ]
    )
    for i in range(extra_lines):
        lines.append(f"Dòng nội dung bổ sung {i + 1} để đáp ứng độ dài tối thiểu.")
    return "\n".join(lines)


# =====================================================================
# 1. GPI Formula, Weights, and Breakdown Tests
# =====================================================================


def test_gpi_constants() -> None:
    """Validate empirical weights and threshold match RES-2026-ARCH-001 v1.2."""
    assert WEIGHT_REASONING_STEPS_S == 2.5
    assert WEIGHT_INTERFACE_COMPLEXITY_K == 2.0
    assert WEIGHT_AUTONOMOUS_INVOCATION_A == 2.0
    assert WEIGHT_PARENT_COUPLING_P == 1.5
    assert GPI_STANDALONE_THRESHOLD == 12.0
    assert GPI_DEADBAND_LOWER == 11.5
    assert GPI_DEADBAND_UPPER == 12.5
    assert MIN_METRIC_SCORE == 1.0
    assert MAX_METRIC_SCORE == 5.0


def test_gpi_exact_calculations() -> None:
    """Verify formula: GPI = (S * 2.5) + (K * 2.0) + (A * 2.0) - (P * 1.5)."""
    # Minimum theoretical bound: S=1, K=1, A=1, P=5 -> 2.5 + 2.0 + 2.0 - 7.5 = -1.0
    assert calculate_gpi(s=1, k=1, a=1, p=5) == -1.0

    # Maximum theoretical bound: S=5, K=5, A=5, P=1 -> 12.5 + 10.0 + 10.0 - 1.5 = 31.0
    assert calculate_gpi(s=5, k=5, a=5, p=1) == 31.0

    # Typical Standalone Skill: S=3, K=2, A=4, P=1 -> 7.5 + 4.0 + 8.0 - 1.5 = 18.0
    assert calculate_gpi(s=3, k=2, a=4, p=1) == 18.0

    # Exact threshold boundary: S=2, K=2, A=3, P=2 -> 5.0 + 4.0 + 6.0 - 3.0 = 12.0
    assert calculate_gpi(s=2, k=2, a=3, p=2) == 12.0

    # Sub-threshold reference: S=2, K=1, A=2, P=4 -> 5.0 + 2.0 + 4.0 - 6.0 = 5.0
    assert calculate_gpi(s=2, k=1, a=2, p=4) == 5.0


def test_gpi_breakdown() -> None:
    """Verify detailed breakdown dictionary components."""
    metrics = GPIMetrics(s=4, k=3, a=2, p=1)
    bd = metrics.breakdown()
    assert bd["s_raw"] == 4.0
    assert bd["s_weighted"] == 10.0
    assert bd["k_raw"] == 3.0
    assert bd["k_weighted"] == 6.0
    assert bd["a_raw"] == 2.0
    assert bd["a_weighted"] == 4.0
    assert bd["p_raw"] == 1.0
    assert bd["p_weighted"] == 1.5
    assert bd["gpi_total"] == 18.5


def test_gpi_metric_boundary_validation() -> None:
    """Verify that scores outside [1.0, 5.0] raise ValueError and non-numerics raise TypeError."""
    # S out of bounds
    with pytest.raises(ValueError, match="Metric 's' must be between 1.0 and 5.0"):
        GPIMetrics(s=0.5, k=3, a=3, p=2)
    with pytest.raises(ValueError, match="Metric 's' must be between 1.0 and 5.0"):
        GPIMetrics(s=5.5, k=3, a=3, p=2)

    # K out of bounds
    with pytest.raises(ValueError, match="Metric 'k' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=0, a=3, p=2)
    with pytest.raises(ValueError, match="Metric 'k' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=6, a=3, p=2)

    # A out of bounds
    with pytest.raises(ValueError, match="Metric 'a' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=3, a=0.9, p=2)
    with pytest.raises(ValueError, match="Metric 'a' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=3, a=5.1, p=2)

    # P out of bounds
    with pytest.raises(ValueError, match="Metric 'p' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=3, a=3, p=-1)
    with pytest.raises(ValueError, match="Metric 'p' must be between 1.0 and 5.0"):
        GPIMetrics(s=3, k=3, a=3, p=5.01)

    # Non-numeric types
    with pytest.raises(TypeError, match="must be numeric"):
        GPIMetrics(s="high", k=3, a=3, p=2)  # type: ignore[arg-type]


# =====================================================================
# 2. Stage 1: Structural Invariant Gates Tests
# =====================================================================


def test_stage_1_gate_0_determinism_gate() -> None:
    """Gate 0: 100% deterministic task halts at Tier 1 and forbids standalone skill."""
    req = DecisionRequest(
        name="table-regex-parser",
        is_deterministic=True,
        is_orchestrated=False,
    )
    result = evaluate_two_stage_decision(req)

    assert result.tier == ArchitectureTier.TIER_1_PACKAGE
    assert result.passed_gate_0 is False
    assert result.passed_gate_1 is False
    assert result.gpi_score is None
    assert result.allow_standalone_skill is False
    assert result.target_location == "packages/*/src"
    assert "Cổng 0 (Determinism Gate)" in result.rationale
    assert "Cấm tạo Skill độc lập" in result.rationale


def test_stage_1_gate_1_orchestration_gate() -> None:
    """Gate 1: Multi-agent/checkpoints/HITL task halts at Tier 3 Composite Orchestrator."""
    req = DecisionRequest(
        name="multi-agent-qc-audit",
        is_deterministic=False,
        is_orchestrated=True,
    )
    result = evaluate_two_stage_decision(req)

    assert result.tier == ArchitectureTier.TIER_3_ORCHESTRATOR
    assert result.passed_gate_0 is True
    assert result.passed_gate_1 is False
    assert result.gpi_score is None
    assert result.allow_standalone_skill is False
    assert "Tầng 3" in result.target_location
    assert "Cổng 1 (Orchestration Gate)" in result.rationale


def test_stage_1_determinism_takes_precedence_over_orchestration() -> None:
    """If both flags are set, Gate 0 evaluates first as the foundational invariant."""
    req = DecisionRequest(
        name="deterministic-batch-job",
        is_deterministic=True,
        is_orchestrated=True,
    )
    result = evaluate_two_stage_decision(req)
    assert result.tier == ArchitectureTier.TIER_1_PACKAGE
    assert result.passed_gate_0 is False


# =====================================================================
# 3. Stage 2: Granularity & Placement Index (GPI) Routing Tests
# =====================================================================


def test_stage_2_missing_metrics_raises_error() -> None:
    """If task passes Gate 0 and Gate 1, gpi_metrics is mandatory."""
    req = DecisionRequest(
        name="cognitive-classifier",
        is_deterministic=False,
        is_orchestrated=False,
        gpi_metrics=None,
    )
    with pytest.raises(ValueError, match="Stage 2 evaluation requires 'gpi_metrics'"):
        evaluate_two_stage_decision(req)


def test_stage_2_tier_2a_progressive_reference_routing() -> None:
    """GPI < 12.0 routes to Tier 2A Progressive Reference in references/*.md."""
    # S=2, K=1, A=2, P=4 -> GPI = 5.0 < 12.0
    req = DecisionRequest(
        name="table-reconstruction",
        is_deterministic=False,
        is_orchestrated=False,
        gpi_metrics=GPIMetrics(s=2, k=1, a=2, p=4),
        parent_skill="ccba-markdown-document-processing",
    )
    result = evaluate_two_stage_decision(req)

    assert result.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert result.passed_gate_0 is True
    assert result.passed_gate_1 is True
    assert result.gpi_score == 5.0
    assert result.allow_standalone_skill is False
    assert "references/table-reconstruction.md" in result.target_location
    assert "ccba-markdown-document-processing" in result.target_location
    assert "Tier 2A (Progressive Reference)" in result.rationale
    assert result.breakdown is not None
    assert result.breakdown["gpi_total"] == 5.0


def test_stage_2_tier_2b_standalone_kernel_skill_routing() -> None:
    """GPI >= 12.0 routes to Tier 2B Standalone Kernel Skill in .agents/skills/ccba-<name>/."""
    # S=4, K=3, A=4, P=1 -> GPI = 22.5 >= 12.0
    req = DecisionRequest(
        name="legal-advisor",
        is_deterministic=False,
        is_orchestrated=False,
        gpi_metrics=GPIMetrics(s=4, k=3, a=4, p=1),
    )
    result = evaluate_two_stage_decision(req)

    assert result.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert result.passed_gate_0 is True
    assert result.passed_gate_1 is True
    assert result.gpi_score == 22.5
    assert result.allow_standalone_skill is True
    assert result.target_location == ".agents/skills/ccba-legal-advisor/"
    assert "Tier 2B (Standalone Kernel Skill)" in result.rationale


def test_stage_2_standalone_naming_with_existing_namespace() -> None:
    """Pre-namespaced names (ccba-*, bigbim-*) keep their prefix."""
    req1 = DecisionRequest(
        name="ccba-maskara",
        gpi_metrics=GPIMetrics(s=3, k=3, a=3, p=1),  # 7.5 + 6.0 + 6.0 - 1.5 = 18.0
    )
    result1 = evaluate_two_stage_decision(req1)
    assert result1.target_location == ".agents/skills/ccba-maskara/"

    req2 = DecisionRequest(
        name="bigbim-classification",
        gpi_metrics=GPIMetrics(s=3, k=3, a=3, p=1),
    )
    result2 = evaluate_two_stage_decision(req2)
    assert result2.target_location == ".agents/skills/bigbim-classification/"


# =====================================================================
# 4. SkillValidator Integration Tests
# =====================================================================


def test_skill_validator_delegation_methods() -> None:
    """Verify SkillValidator helper methods for two-stage decision and gpi calculation."""
    validator = SkillValidator()
    score = validator.calculate_gpi(s=3, k=2, a=4, p=1)
    assert score == 18.0

    req = DecisionRequest(name="test-cap", is_deterministic=True)
    res = validator.evaluate_two_stage_decision(req)
    assert res.tier == ArchitectureTier.TIER_1_PACKAGE


def test_skill_validator_detects_gate_0_determinism_violation() -> None:
    """Skill with 'is-deterministic: true' triggers DETERMINISM_GATE_VIOLATION."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        content = _make_dummy_skill_md(
            "ccba-det-skill",
            extra_frontmatter={"is-deterministic": "true"},
        )
        file_path.write_text(content, encoding="utf-8")
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)

        assert any(i.category == "DETERMINISM_GATE_VIOLATION" for i in issues)
        det_issue = next(i for i in issues if i.category == "DETERMINISM_GATE_VIOLATION")
        assert "Gate 0 (Determinism Gate)" in det_issue.message
        assert "packages/*" in det_issue.message


def test_skill_validator_detects_gate_1_orchestration_violation() -> None:
    """Skill with 'is-orchestrated: true' triggers ORCHESTRATION_GATE_VIOLATION."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        content = _make_dummy_skill_md(
            "ccba-orch-skill",
            extra_frontmatter={"is-orchestrated": "true"},
        )
        file_path.write_text(content, encoding="utf-8")
        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)

        assert any(i.category == "ORCHESTRATION_GATE_VIOLATION" for i in issues)
        orch_issue = next(i for i in issues if i.category == "ORCHESTRATION_GATE_VIOLATION")
        assert "Gate 1 (Orchestration Gate)" in orch_issue.message
        assert "Composite Orchestrator" in orch_issue.message


def test_skill_validator_detects_insufficient_gpi_score() -> None:
    """Skill with GPI < 12.0 triggers INSUFFICIENT_GPI_SCORE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # s=1, k=1, a=1, p=4 -> GPI = 2.5 + 2.0 + 2.0 - 6.0 = 0.5 < 12.0
        gpi_yaml = "\ngpi:\n  s: 1\n  k: 1\n  a: 1\n  p: 4"
        lines = [
            "---",
            "name: ccba-sub-skill",
            "description: Sub-threshold capability.",
            "bundle: _core",
            f"{gpi_yaml}",
            "---",
            "# Ccba Sub Skill",
            "## Quy trình thực hiện",
            "### Bước 1: Khởi tạo",
            "- **Tiêu chí hoàn thành:** Xong.",
        ]
        lines.extend(["Line"] * 30)
        file_path.write_text("\n".join(lines), encoding="utf-8")

        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path, enforce_gpi=True)

        assert any(i.category == "INSUFFICIENT_GPI_SCORE" for i in issues)
        gpi_issue = next(i for i in issues if i.category == "INSUFFICIENT_GPI_SCORE")
        assert "GPI 0.50 < 12.0" in gpi_issue.message
        assert "Tier 2A" in gpi_issue.message

        # Verify that without enforce_gpi, sub-threshold GPI does not raise hard error
        issues_no_enforce = validator.audit_skill(file_path, enforce_gpi=False)
        assert not any(i.category == "INSUFFICIENT_GPI_SCORE" for i in issues_no_enforce)


def test_skill_validator_accepts_compliant_gpi_score() -> None:
    """Skill with GPI >= 12.0 passes without GPI issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        # s=4, k=3, a=4, p=1 -> GPI = 22.5 >= 12.0
        gpi_yaml = "\ngpi:\n  s: 4\n  k: 3\n  a: 4\n  p: 1"
        lines = [
            "---",
            "name: ccba-good-skill",
            "description: High complexity capability.",
            "bundle: _core",
            f"{gpi_yaml}",
            "---",
            "# Ccba Good Skill",
            "## Quy trình thực hiện",
            "### Bước 1: Khởi tạo",
            "- **Tiêu chí hoàn thành:** Xong.",
        ]
        lines.extend(["Line"] * 30)
        file_path.write_text("\n".join(lines), encoding="utf-8")

        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)

        assert not any("GPI" in i.category for i in issues)


def test_skill_validator_detects_invalid_gpi_frontmatter() -> None:
    """Invalid GPI frontmatter formats emit INVALID_GPI_METRICS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"

        # Case 1: gpi is not a dict
        file_path.write_text(
            _make_dummy_skill_md("ccba-bad-gpi", {"gpi": "not-a-dict"}),
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues1 = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_GPI_METRICS" for i in issues1)

        # Case 2: missing key in gpi dict
        lines = [
            "---",
            "name: ccba-bad-gpi-missing",
            "description: Desc.",
            "bundle: _core",
            "gpi:\n  s: 2\n  k: 2",
            "---",
            "# Title",
        ]
        file_path.write_text("\n".join(lines), encoding="utf-8")
        issues2 = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_GPI_METRICS" for i in issues2)

        # Case 3: value out of bounds
        lines = [
            "---",
            "name: ccba-bad-gpi-bounds",
            "description: Desc.",
            "bundle: _core",
            "gpi:\n  s: 10\n  k: 2\n  a: 3\n  p: 1",
            "---",
            "# Title",
        ]
        file_path.write_text("\n".join(lines), encoding="utf-8")
        issues3 = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_GPI_METRICS" for i in issues3)


def test_skill_validator_enforce_gpi_flag() -> None:
    """Under enforce_gpi=True, missing gpi block raises MISSING_GPI_METRICS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text(_make_dummy_skill_md("ccba-nogpi-skill"), encoding="utf-8")

        validator = SkillValidator(project_root=Path(tmpdir))
        # Without enforce_gpi -> no issue
        issues_normal = validator.audit_skill(file_path, enforce_gpi=False)
        assert not any(i.category == "MISSING_GPI_METRICS" for i in issues_normal)

        # With enforce_gpi -> triggers MISSING_GPI_METRICS
        issues_enforced = validator.audit_skill(file_path, enforce_gpi=True)
        assert any(i.category == "MISSING_GPI_METRICS" for i in issues_enforced)


# =====================================================================
# 5. CLI evaluate-gpi and validate-skill Tests
# =====================================================================


def test_cli_evaluate_gpi_deterministic() -> None:
    """CLI evaluates Gate 0 deterministic flag."""
    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        code = run_evaluate_gpi_cli(["--name", "regex-strip", "--deterministic"])
    assert code == 0
    output = stdout_capture.getvalue()
    assert "Tier 1: Package Function / Deep Seam" in output
    assert "packages/*/src" in output
    assert "NOT PERMITTED" in output


def test_cli_evaluate_gpi_orchestrated() -> None:
    """CLI evaluates Gate 1 orchestrated flag."""
    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        code = run_evaluate_gpi_cli(["--name", "qc-supervisor", "--orchestrated"])
    assert code == 0
    output = stdout_capture.getvalue()
    assert "Tier 3: Composite Orchestrator" in output


def test_cli_evaluate_gpi_standalone_and_json() -> None:
    """CLI evaluates Stage 2 standalone skill with JSON format."""
    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        code = run_evaluate_gpi_cli(
            [
                "--name",
                "legal-intel",
                "--s",
                "4",
                "--k",
                "3",
                "--a",
                "4",
                "--p",
                "1",
                "--json",
            ]
        )
    assert code == 0
    payload = json.loads(stdout_capture.getvalue())
    assert payload["name"] == "legal-intel"
    assert payload["tier"] == "Tier 2B: Standalone Kernel Skill"
    assert payload["allow_standalone_skill"] is True
    assert payload["gpi_score"] == 22.5
    assert payload["breakdown"]["gpi_total"] == 22.5


def test_cli_evaluate_gpi_progressive_reference() -> None:
    """CLI evaluates Stage 2 progressive reference (GPI < 12.0)."""
    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        code = run_evaluate_gpi_cli(
            [
                "--name",
                "table-extractor",
                "--s",
                "1",
                "--k",
                "1",
                "--a",
                "1",
                "--p",
                "5",
                "--parent",
                "ccba-markdown-document-processing",
            ]
        )
    assert code == 0
    output = stdout_capture.getvalue()
    assert "Tier 2A: Progressive Reference" in output
    assert "NOT PERMITTED" in output
    assert "references/table-extractor.md" in output


def test_cli_evaluate_gpi_missing_metrics_fails() -> None:
    """CLI returns error code 1 when Stage 2 metrics are incomplete."""
    stderr_capture = io.StringIO()
    with patch("sys.stderr", stderr_capture):
        code = run_evaluate_gpi_cli(["--name", "incomplete-metrics", "--s", "3"])
    assert code == 1
    assert "all 4 GPI metrics" in stderr_capture.getvalue()


def test_cli_evaluate_gpi_invalid_metric_range_fails() -> None:
    """CLI returns error code 1 when a metric is outside [1, 5]."""
    stderr_capture = io.StringIO()
    with patch("sys.stderr", stderr_capture):
        code = run_evaluate_gpi_cli(
            [
                "--name",
                "invalid-range",
                "--s",
                "10",
                "--k",
                "2",
                "--a",
                "3",
                "--p",
                "1",
            ]
        )
    assert code == 1
    assert "Invalid GPI metric values" in stderr_capture.getvalue()


def test_main_cli_routing_evaluate_gpi() -> None:
    """Main CLI entry point routes to evaluate-gpi subcommand."""
    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        code = main(["evaluate-gpi", "--name", "pure-calc", "--deterministic"])
    assert code == 0
    assert "Tier 1: Package Function" in stdout_capture.getvalue()


def test_cli_validate_skill_enforce_gpi_flag() -> None:
    """run_skill_validation_cli with --enforce-gpi blocks skills without GPI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        file_path.write_text(_make_dummy_skill_md("ccba-test-gpi-cli"), encoding="utf-8")

        # Running validate-skill with --enforce-gpi should fail
        code = run_skill_validation_cli(
            ["--file", str(file_path), "--root", tmpdir, "--enforce-gpi"]
        )
        assert code == 1


# =====================================================================
# 6. Edge Cases & Robustness Tests (Adversarial Probes)
# =====================================================================


def test_gpi_metric_nan_and_inf_rejected() -> None:
    """Ensure float('nan'), float('inf'), and float('-inf') are strictly rejected."""
    import math

    with pytest.raises(ValueError, match="Metric 's' must be between"):
        GPIMetrics(s=float("nan"), k=3, a=3, p=2)

    with pytest.raises(ValueError, match="Metric 'k' must be between"):
        GPIMetrics(s=3, k=float("inf"), a=3, p=2)

    with pytest.raises(ValueError, match="Metric 'a' must be between"):
        GPIMetrics(s=3, k=3, a=float("-inf"), p=2)

    with pytest.raises(ValueError, match="Metric 'p' must be between"):
        GPIMetrics(s=3, k=3, a=3, p=math.nan)


def test_gpi_metric_boolean_rejected() -> None:
    """Ensure bool types are strictly rejected with TypeError despite being int subclass."""
    with pytest.raises(TypeError, match="must be numeric"):
        GPIMetrics(s=True, k=3, a=3, p=2)

    with pytest.raises(TypeError, match="must be numeric"):
        GPIMetrics(s=3, k=False, a=3, p=2)


def test_decision_request_name_validation() -> None:
    """Ensure empty or whitespace capability name raises ValueError."""
    with pytest.raises(ValueError, match="must be a non-empty string"):
        DecisionRequest(name="")

    with pytest.raises(ValueError, match="must be a non-empty string"):
        DecisionRequest(name="   ")

    # Leading slash in name is stripped cleanly
    req = DecisionRequest(
        name="/ccba-slash-skill",
        gpi_metrics=GPIMetrics(s=4, k=3, a=4, p=1),
    )
    res = evaluate_two_stage_decision(req)
    assert res.target_location == ".agents/skills/ccba-slash-skill/"


def test_decision_request_with_dict_metrics() -> None:
    """Ensure DecisionRequest accepts dictionary metrics and handles case-insensitivity."""
    req1 = DecisionRequest(
        name="dict-skill",
        gpi_metrics={"s": 4, "k": 3, "a": 4, "p": 1},
    )
    assert isinstance(req1.gpi_metrics, GPIMetrics)
    assert req1.gpi_metrics.calculate() == 22.5

    # Uppercase keys
    req2 = DecisionRequest(
        name="dict-skill-upper",
        gpi_metrics={"S": 4, "K": 3, "A": 4, "P": 1},
    )
    assert isinstance(req2.gpi_metrics, GPIMetrics)
    assert req2.gpi_metrics.calculate() == 22.5

    # Missing key in dict
    with pytest.raises(ValueError, match="missing required metric keys"):
        DecisionRequest(name="bad-dict", gpi_metrics={"s": 4, "k": 3})


def test_stage_2_platform_loader_namespace_preserved() -> None:
    """Ensure platform-loader is preserved without ccba- double prefix."""
    req = DecisionRequest(
        name="platform-loader",
        gpi_metrics=GPIMetrics(s=3, k=3, a=3, p=1),
    )
    res = evaluate_two_stage_decision(req)
    assert res.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert res.target_location == ".agents/skills/platform-loader/"


def test_stage_2_reference_name_without_double_md_extension() -> None:
    """Ensure name with .md suffix does not produce references/*.md.md."""
    req = DecisionRequest(
        name="table_cleaner.md",
        gpi_metrics=GPIMetrics(s=1, k=1, a=1, p=5),
        parent_skill="ccba-doc-master",
    )
    res = evaluate_two_stage_decision(req)
    assert res.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert "references/table_cleaner.md" in res.target_location
    assert not res.target_location.endswith(".md.md")


def test_frontmatter_case_insensitive_gpi_keys() -> None:
    """Ensure uppercase S, K, A, P and GPI in frontmatter parse successfully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        lines = [
            "---",
            "name: ccba-upper-gpi",
            "description: Valid description.",
            "bundle: _core",
            "gpi:",
            "  S: 4",
            "  K: 3",
            "  A: 4",
            "  P: 1",
            "---",
            "# Ccba Upper Gpi",
            "## Quy trình thực hiện",
            "### Bước 1: Khởi tạo",
            "- **Tiêu chí hoàn thành:** Xong.",
        ]
        lines.extend(["Line"] * 30)
        file_path.write_text("\n".join(lines), encoding="utf-8")

        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path, enforce_gpi=True)
        assert not any("GPI" in i.category for i in issues)


def test_frontmatter_boolean_metric_rejected() -> None:
    """Ensure boolean value in frontmatter gpi emits INVALID_GPI_METRICS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "SKILL.md"
        lines = [
            "---",
            "name: ccba-bool-gpi",
            "description: Valid description.",
            "bundle: _core",
            "gpi:",
            "  s: true",
            "  k: 3",
            "  a: 4",
            "  p: 1",
            "---",
            "# Title",
        ]
        file_path.write_text("\n".join(lines), encoding="utf-8")

        validator = SkillValidator(project_root=Path(tmpdir))
        issues = validator.audit_skill(file_path)
        assert any(i.category == "INVALID_GPI_METRICS" for i in issues)


def test_stage_1_violations_do_not_emit_missing_gpi_under_enforce_gpi() -> None:
    """Gate 0 and Gate 1 violations must not emit MISSING_GPI_METRICS even if enforce_gpi=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Gate 0 skill without GPI
        file_0 = Path(tmpdir) / "skill0.md"
        file_0.write_text(
            _make_dummy_skill_md("ccba-det-skill", {"is-deterministic": "true"}),
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))
        issues_0 = validator.audit_skill(file_0, enforce_gpi=True)
        assert any(i.category == "DETERMINISM_GATE_VIOLATION" for i in issues_0)
        assert not any(i.category == "MISSING_GPI_METRICS" for i in issues_0)

        # Gate 1 skill without GPI
        file_1 = Path(tmpdir) / "skill1.md"
        file_1.write_text(
            _make_dummy_skill_md("ccba-orch-skill", {"is-orchestrated": "true"}),
            encoding="utf-8",
        )
        issues_1 = validator.audit_skill(file_1, enforce_gpi=True)
        assert any(i.category == "ORCHESTRATION_GATE_VIOLATION" for i in issues_1)
        assert not any(i.category == "MISSING_GPI_METRICS" for i in issues_1)


def test_skill_validator_evaluate_skill_file() -> None:
    """Verify evaluate_skill_file correctly evaluates SKILL.md files for each tier."""
    with tempfile.TemporaryDirectory() as tmpdir:
        validator = SkillValidator(project_root=Path(tmpdir))

        # Tier 1 file
        f_tier1 = Path(tmpdir) / "skill_t1.md"
        f_tier1.write_text(
            _make_dummy_skill_md("ccba-det", {"is-deterministic": "true"}),
            encoding="utf-8",
        )
        res1 = validator.evaluate_skill_file(f_tier1)
        assert res1.tier == ArchitectureTier.TIER_1_PACKAGE
        assert res1.passed_gate_0 is False

        # Tier 3 file
        f_tier3 = Path(tmpdir) / "skill_t3.md"
        f_tier3.write_text(
            _make_dummy_skill_md("ccba-orch", {"is-orchestrated": "true"}),
            encoding="utf-8",
        )
        res3 = validator.evaluate_skill_file(f_tier3)
        assert res3.tier == ArchitectureTier.TIER_3_ORCHESTRATOR
        assert res3.passed_gate_1 is False

        # Tier 2B file
        f_tier2b = Path(tmpdir) / "skill_t2b.md"
        f_tier2b.write_text(
            "---\nname: ccba-advisor\ndescription: Desc.\nbundle: _core\ngpi:\n  s: 4\n  k: 3\n  a: 4\n  p: 1\n---\n# Title\n",
            encoding="utf-8",
        )
        res2b = validator.evaluate_skill_file(f_tier2b)
        assert res2b.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
        assert res2b.allow_standalone_skill is True
        assert res2b.gpi_score == 22.5

        # Tier 2A file
        f_tier2a = Path(tmpdir) / "skill_t2a.md"
        f_tier2a.write_text(
            "---\nname: ref-helper\ndescription: Desc.\nbundle: _core\nparent-skill: ccba-advisor\ngpi:\n  s: 1\n  k: 1\n  a: 1\n  p: 4\n---\n# Title\n",
            encoding="utf-8",
        )
        res2a = validator.evaluate_skill_file(f_tier2a)
        assert res2a.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
        assert res2a.allow_standalone_skill is False
        assert "ccba-advisor" in res2a.target_location


def test_cli_evaluate_gpi_file_flag() -> None:
    """Verify ccba-harness evaluate-gpi --file directly evaluates SKILL.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text(
            "---\nname: ccba-audit-tool\ndescription: Desc.\nbundle: _core\ngpi:\n  s: 4\n  k: 3\n  a: 4\n  p: 1\n---\n# Title\n",
            encoding="utf-8",
        )

        # Text mode
        stdout_text = io.StringIO()
        with patch("sys.stdout", stdout_text):
            code = run_evaluate_gpi_cli(["--file", str(skill_file)])
        assert code == 0
        assert "Tier 2B: Standalone Kernel Skill" in stdout_text.getvalue()

        # JSON mode
        stdout_json = io.StringIO()
        with patch("sys.stdout", stdout_json):
            code_json = run_evaluate_gpi_cli(["--file", str(skill_file), "--json"])
        assert code_json == 0
        data = json.loads(stdout_json.getvalue())
        assert data["tier"] == "Tier 2B: Standalone Kernel Skill"
        assert data["gpi_score"] == 22.5

        # Nonexistent file
        stderr_err = io.StringIO()
        with patch("sys.stderr", stderr_err):
            code_missing = run_evaluate_gpi_cli(["--file", str(Path(tmpdir) / "missing.md")])
        assert code_missing == 1
        assert "does not exist" in stderr_err.getvalue()


def test_cli_evaluate_gpi_file_with_metric_overrides() -> None:
    """Verify evaluating a SKILL.md without gpi block using CLI metric flags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        # Skill without gpi block
        skill_file.write_text(
            "---\nname: ccba-custom-tool\ndescription: Desc.\nbundle: _core\n---\n# Title\n",
            encoding="utf-8",
        )

        stdout_text = io.StringIO()
        with patch("sys.stdout", stdout_text):
            code = run_evaluate_gpi_cli(
                [
                    "--file",
                    str(skill_file),
                    "--s",
                    "4",
                    "--k",
                    "3",
                    "--a",
                    "4",
                    "--p",
                    "1",
                ]
            )
        assert code == 0
        assert "Tier 2B: Standalone Kernel Skill" in stdout_text.getvalue()
        assert "GPI Score       : 22.50" in stdout_text.getvalue()


# =====================================================================
# 8. 30 Canonical GPI Benchmark Anchors & Deadband Hysteresis Tests
# =====================================================================


def test_30_canonical_anchors_invariants() -> None:
    """Verify 30 canonical anchors: 10 Tier 1, 10 Tier 2A, 10 Tier 2B."""
    assert len(CANONICAL_ANCHORS) == 30
    assert all(isinstance(a, CanonicalAnchor) for a in CANONICAL_ANCHORS)

    tier1_anchors = [
        a for a in CANONICAL_ANCHORS if a.expected_tier == ArchitectureTier.TIER_1_PACKAGE
    ]
    tier2a_anchors = [
        a
        for a in CANONICAL_ANCHORS
        if a.expected_tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    ]
    tier2b_anchors = [
        a
        for a in CANONICAL_ANCHORS
        if a.expected_tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    ]

    assert len(tier1_anchors) == 10
    assert len(tier2a_anchors) == 10
    assert len(tier2b_anchors) == 10

    # Verify each anchor evaluates to its exact expected tier
    for anchor in CANONICAL_ANCHORS:
        if anchor.is_deterministic:
            req = DecisionRequest(
                name=anchor.name,
                is_deterministic=True,
                is_orchestrated=False,
            )
            res = evaluate_two_stage_decision(req)
            assert res.tier == ArchitectureTier.TIER_1_PACKAGE
            assert res.allow_standalone_skill is False
            assert res.passed_gate_0 is False
        else:
            assert anchor.s is not None
            assert anchor.k is not None
            assert anchor.a is not None
            assert anchor.p is not None
            metrics = GPIMetrics(s=anchor.s, k=anchor.k, a=anchor.a, p=anchor.p)
            req = DecisionRequest(
                name=anchor.name,
                is_deterministic=False,
                is_orchestrated=False,
                gpi_metrics=metrics,
            )
            res = evaluate_two_stage_decision(req)
            assert res.tier == anchor.expected_tier
            if anchor.expected_tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
                assert res.gpi_score is not None and res.gpi_score < 12.0
                assert res.allow_standalone_skill is False
            elif anchor.expected_tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL:
                assert res.gpi_score is not None and res.gpi_score >= 12.0
                assert res.allow_standalone_skill is True


def test_deadband_hysteresis_preserves_existing_tier() -> None:
    """Verify deadband hysteresis preserves prior tier within [11.5, 12.5) without flip flag."""
    # Sub-test 1: Score 11.5 (normally Tier 2A) preserves existing Tier 2B
    # S=2, K=2, A=2, P=1 -> 5.0 + 4.0 + 4.0 - 1.5 = 11.5
    metrics_11_5 = GPIMetrics(s=2, k=2, a=2, p=1)
    assert metrics_11_5.calculate() == 11.5

    # Without existing_tier: routes to Tier 2A
    req_fresh = DecisionRequest(name="ccba-border-skill", gpi_metrics=metrics_11_5)
    res_fresh = evaluate_two_stage_decision(req_fresh)
    assert res_fresh.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert res_fresh.breakdown is not None
    assert res_fresh.breakdown["deadband_active"] == 1.0
    assert res_fresh.breakdown["preserved_by_hysteresis"] == 0.0

    # With existing Tier 2B: preserved as Tier 2B
    req_preserved_2b = DecisionRequest(
        name="ccba-border-skill",
        gpi_metrics=metrics_11_5,
        existing_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    )
    res_preserved_2b = evaluate_two_stage_decision(req_preserved_2b)
    assert res_preserved_2b.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert res_preserved_2b.allow_standalone_skill is True
    assert res_preserved_2b.breakdown is not None
    assert res_preserved_2b.breakdown["deadband_active"] == 1.0
    assert res_preserved_2b.breakdown["preserved_by_hysteresis"] == 1.0
    assert "BẢO LƯU do cơ chế Hysteresis" in res_preserved_2b.rationale

    # Sub-test 2: Score 12.0 (normally Tier 2B) preserves existing Tier 2A
    # S=2, K=2, A=3, P=2 -> 5.0 + 4.0 + 6.0 - 3.0 = 12.0
    metrics_12_0 = GPIMetrics(s=2, k=2, a=3, p=2)
    assert metrics_12_0.calculate() == 12.0

    # Without existing_tier: routes to Tier 2B
    req_fresh_2 = DecisionRequest(name="ref-border-doc", gpi_metrics=metrics_12_0)
    res_fresh_2 = evaluate_two_stage_decision(req_fresh_2)
    assert res_fresh_2.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert res_fresh_2.breakdown is not None
    assert res_fresh_2.breakdown["deadband_active"] == 1.0
    assert res_fresh_2.breakdown["preserved_by_hysteresis"] == 0.0

    # With existing Tier 2A: preserved as Tier 2A
    req_preserved_2a = DecisionRequest(
        name="ref-border-doc",
        gpi_metrics=metrics_12_0,
        existing_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    )
    res_preserved_2a = evaluate_two_stage_decision(req_preserved_2a)
    assert res_preserved_2a.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert res_preserved_2a.allow_standalone_skill is False
    assert res_preserved_2a.breakdown is not None
    assert res_preserved_2a.breakdown["deadband_active"] == 1.0
    assert res_preserved_2a.breakdown["preserved_by_hysteresis"] == 1.0
    assert "BẢO LƯU do cơ chế Hysteresis" in res_preserved_2a.rationale


def test_deadband_hysteresis_force_tier_flip() -> None:
    """Verify --force-tier-flip overrides deadband hysteresis within [11.5, 12.5)."""
    # Score 11.5 with existing Tier 2B and force_tier_flip=True -> flips to Tier 2A
    metrics_11_5 = GPIMetrics(s=2, k=2, a=2, p=1)
    req_flip_2a = DecisionRequest(
        name="ccba-border-skill",
        gpi_metrics=metrics_11_5,
        existing_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        force_tier_flip=True,
    )
    res_flip_2a = evaluate_two_stage_decision(req_flip_2a)
    assert res_flip_2a.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert res_flip_2a.allow_standalone_skill is False
    assert res_flip_2a.breakdown is not None
    assert res_flip_2a.breakdown["deadband_active"] == 1.0
    assert res_flip_2a.breakdown["preserved_by_hysteresis"] == 0.0
    assert "force_tier_flip=True" in res_flip_2a.rationale

    # Score 12.0 with existing Tier 2A and force_tier_flip=True -> flips to Tier 2B
    metrics_12_0 = GPIMetrics(s=2, k=2, a=3, p=2)
    req_flip_2b = DecisionRequest(
        name="ref-border-doc",
        gpi_metrics=metrics_12_0,
        existing_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        force_tier_flip=True,
    )
    res_flip_2b = evaluate_two_stage_decision(req_flip_2b)
    assert res_flip_2b.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert res_flip_2b.allow_standalone_skill is True
    assert res_flip_2b.breakdown is not None
    assert res_flip_2b.breakdown["deadband_active"] == 1.0
    assert res_flip_2b.breakdown["preserved_by_hysteresis"] == 0.0
    assert "force_tier_flip=True" in res_flip_2b.rationale


def test_deadband_hysteresis_outside_deadband_flips_normally() -> None:
    """Verify scores strictly outside [11.5, 12.5) transition tiers normally without hysteresis."""
    # Score 10.0 (< 11.5): S=2, K=2, A=2, P=2 -> 5.0 + 4.0 + 4.0 - 3.0 = 10.0
    metrics_10_0 = GPIMetrics(s=2, k=2, a=2, p=2)
    assert metrics_10_0.calculate() == 10.0

    req_low = DecisionRequest(
        name="ccba-dropped-skill",
        gpi_metrics=metrics_10_0,
        existing_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    )
    res_low = evaluate_two_stage_decision(req_low)
    assert res_low.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
    assert res_low.breakdown is not None
    assert res_low.breakdown["deadband_active"] == 0.0
    assert res_low.breakdown["preserved_by_hysteresis"] == 0.0

    # Score 13.5 (>= 12.5): S=2, K=2, A=3, P=1 -> 5.0 + 4.0 + 6.0 - 1.5 = 13.5
    metrics_13_5 = GPIMetrics(s=2, k=2, a=3, p=1)
    assert metrics_13_5.calculate() == 13.5

    req_high = DecisionRequest(
        name="ref-promoted-doc",
        gpi_metrics=metrics_13_5,
        existing_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    )
    res_high = evaluate_two_stage_decision(req_high)
    assert res_high.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    assert res_high.breakdown is not None
    assert res_high.breakdown["deadband_active"] == 0.0
    assert res_high.breakdown["preserved_by_hysteresis"] == 0.0


def test_decision_request_existing_tier_normalization() -> None:
    """Verify existing_tier string normalization and error handling."""
    req1 = DecisionRequest(name="test", is_deterministic=True, existing_tier="tier-2b")
    assert req1.existing_tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL

    req2 = DecisionRequest(name="test", is_deterministic=True, existing_tier="tier-2a")
    assert req2.existing_tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE

    req3 = DecisionRequest(name="test", is_deterministic=True, existing_tier="tier-1")
    assert req3.existing_tier == ArchitectureTier.TIER_1_PACKAGE

    req4 = DecisionRequest(name="test", is_deterministic=True, existing_tier="tier-3")
    assert req4.existing_tier == ArchitectureTier.TIER_3_ORCHESTRATOR

    with pytest.raises(ValueError, match="Unknown existing_tier"):
        DecisionRequest(name="test", is_deterministic=True, existing_tier="tier-invalid")

    with pytest.raises(TypeError, match="existing_tier must be an ArchitectureTier or str"):
        DecisionRequest(name="test", is_deterministic=True, existing_tier=123)  # type: ignore[arg-type]


def test_cli_evaluate_gpi_deadband_and_force_flip() -> None:
    """Verify CLI evaluate-gpi with --existing-tier and --force-tier-flip."""
    # Test preservation via CLI text mode
    stdout_pres = io.StringIO()
    with patch("sys.stdout", stdout_pres):
        code_pres = run_evaluate_gpi_cli(
            [
                "--name",
                "border-skill",
                "--s",
                "2",
                "--k",
                "2",
                "--a",
                "2",
                "--p",
                "1",
                "--existing-tier",
                "tier-2b",
            ]
        )
    assert code_pres == 0
    val_pres = stdout_pres.getvalue()
    assert "Tier 2B: Standalone Kernel Skill" in val_pres
    assert "Hysteresis      : PRESERVED" in val_pres

    # Test forced flip via CLI text mode
    stdout_flip = io.StringIO()
    with patch("sys.stdout", stdout_flip):
        code_flip = run_evaluate_gpi_cli(
            [
                "--name",
                "border-skill",
                "--s",
                "2",
                "--k",
                "2",
                "--a",
                "2",
                "--p",
                "1",
                "--existing-tier",
                "tier-2b",
                "--force-tier-flip",
            ]
        )
    assert code_flip == 0
    val_flip = stdout_flip.getvalue()
    assert "Tier 2A: Progressive Reference" in val_flip

    # Test preservation via JSON mode
    stdout_json = io.StringIO()
    with patch("sys.stdout", stdout_json):
        code_json = run_evaluate_gpi_cli(
            [
                "--name",
                "border-skill",
                "--s",
                "2",
                "--k",
                "2",
                "--a",
                "2",
                "--p",
                "1",
                "--existing-tier",
                "tier-2b",
                "--json",
            ]
        )
    assert code_json == 0
    data = json.loads(stdout_json.getvalue())
    assert data["tier"] == "Tier 2B: Standalone Kernel Skill"
    assert data["breakdown"]["deadband_active"] == 1.0
    assert data["breakdown"]["preserved_by_hysteresis"] == 1.0


def test_skill_validator_evaluate_skill_file_with_hysteresis() -> None:
    """Verify SkillValidator evaluate_skill_file handles existing_tier and hysteresis overrides."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        # GPI: S=2, K=2, A=2, P=1 -> 11.5
        skill_file.write_text(
            "---\nname: ccba-border\ndescription: Desc.\nbundle: _core\ngpi:\n  s: 2\n  k: 2\n  a: 2\n  p: 1\n---\n# Title\n",
            encoding="utf-8",
        )
        validator = SkillValidator(project_root=Path(tmpdir))

        # Without override: routes to Tier 2A
        res1 = validator.evaluate_skill_file(skill_file)
        assert res1.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE

        # With override_existing_tier="tier-2b": stays Tier 2B
        res2 = validator.evaluate_skill_file(skill_file, override_existing_tier="tier-2b")
        assert res2.tier == ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
        assert res2.allow_standalone_skill is True
        assert res2.breakdown is not None
        assert res2.breakdown["preserved_by_hysteresis"] == 1.0

        # With override_force_tier_flip=True: flips to Tier 2A
        res3 = validator.evaluate_skill_file(
            skill_file,
            override_existing_tier="tier-2b",
            override_force_tier_flip=True,
        )
        assert res3.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
        assert res3.allow_standalone_skill is False
