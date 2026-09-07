"""gpi.py - Two-Stage Decision Framework and Granularity & Placement Index (GPI).

Implements the architectural decision framework from Research Report RES-2026-ARCH-001 v1.2:
- Stage 1: Two Structural Invariant Gates (Determinism Gate & Orchestration Gate).
- Stage 2: Granularity & Placement Index (GPI) calculation and routing:
    GPI = (S * 2.5) + (K * 2.0) + (A * 2.0) - (P * 1.5)
    - GPI < 12.0  -> Tier 2A (Progressive Reference in references/*.md)
    - GPI >= 12.0 -> Tier 2B (Standalone Kernel Skill in .agents/skills/ccba-<name>/)

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Provisional Heuristic Weights per RES-2026-ARCH-001 v1.2 Section 6.2
WEIGHT_REASONING_STEPS_S: float = 2.5
WEIGHT_INTERFACE_COMPLEXITY_K: float = 2.0
WEIGHT_AUTONOMOUS_INVOCATION_A: float = 2.0
WEIGHT_PARENT_COUPLING_P: float = 1.5

# Routing Threshold
GPI_STANDALONE_THRESHOLD: float = 12.0

# Metric Bounds
MIN_METRIC_SCORE: float = 1.0
MAX_METRIC_SCORE: float = 5.0


class ArchitectureTier(str, Enum):
    """Architectural placement tier classification."""

    TIER_1_PACKAGE = "Tier 1: Package Function / Deep Seam"
    TIER_2A_PROGRESSIVE_REFERENCE = "Tier 2A: Progressive Reference"
    TIER_2B_STANDALONE_KERNEL_SKILL = "Tier 2B: Standalone Kernel Skill"
    TIER_3_ORCHESTRATOR = "Tier 3: Composite Orchestrator"


@dataclass
class GPIMetrics:
    """Metrics container for Stage 2: Granularity & Placement Index (GPI).

    Attributes:
        s: Reasoning Steps (Số bước suy luận nhận thức, 1-5).
        k: Interface / Schema Complexity (Độ phức tạp tham số/schema, 1-5).
        a: Autonomous Model Invocation (Mức độ cần Agent tự gọi, 1-5).
        p: Parent Domain Coupling (Mức độ gắn kết với Master Skill hiện hữu, 1-5).
    """

    s: float
    k: float
    a: float
    p: float

    def __post_init__(self) -> None:
        """Validate that all metric scores are numeric (not bool), finite, and within [1.0, 5.0]."""
        for name, val in [("s", self.s), ("k", self.k), ("a", self.a), ("p", self.p)]:
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise TypeError(
                    f"Metric '{name}' must be numeric (int or float), got {type(val).__name__}"
                )
            if math.isnan(val) or math.isinf(val) or val < MIN_METRIC_SCORE or val > MAX_METRIC_SCORE:
                raise ValueError(
                    f"Metric '{name}' must be between {MIN_METRIC_SCORE} and "
                    f"{MAX_METRIC_SCORE}, got {val}"
                )

    def calculate(self) -> float:
        """Calculate GPI score using empirical weights.

        Formula: GPI = (S * 2.5) + (K * 2.0) + (A * 2.0) - (P * 1.5)
        """
        return round(
            (float(self.s) * WEIGHT_REASONING_STEPS_S)
            + (float(self.k) * WEIGHT_INTERFACE_COMPLEXITY_K)
            + (float(self.a) * WEIGHT_AUTONOMOUS_INVOCATION_A)
            - (float(self.p) * WEIGHT_PARENT_COUPLING_P),
            4,
        )

    def breakdown(self) -> dict[str, float]:
        """Return raw and weighted component values."""
        return {
            "s_raw": float(self.s),
            "s_weighted": round(float(self.s) * WEIGHT_REASONING_STEPS_S, 4),
            "k_raw": float(self.k),
            "k_weighted": round(float(self.k) * WEIGHT_INTERFACE_COMPLEXITY_K, 4),
            "a_raw": float(self.a),
            "a_weighted": round(float(self.a) * WEIGHT_AUTONOMOUS_INVOCATION_A, 4),
            "p_raw": float(self.p),
            "p_weighted": round(float(self.p) * WEIGHT_PARENT_COUPLING_P, 4),
            "gpi_total": self.calculate(),
        }


@dataclass
class DecisionRequest:
    """Input parameters for evaluating architecture placement via Two-Stage Decision Framework.

    Attributes:
        name: Name of the proposed skill, function, or capability.
        is_deterministic: Gate 0 flag. True if task is 100% solvable by deterministic code.
        is_orchestrated: Gate 1 flag. True if task coordinates multiple agents/checkpoints/HITL.
        gpi_metrics: Stage 2 metrics (s, k, a, p) for cognitive capabilities (GPIMetrics or dict).
        description: Description of the capability.
        parent_skill: Name of parent/master skill if coupled.
        metadata: Extra metadata or contextual parameters.
    """

    name: str
    is_deterministic: bool = False
    is_orchestrated: bool = False
    gpi_metrics: GPIMetrics | dict[str, Any] | None = None
    description: str = ""
    parent_skill: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate input parameters."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Capability 'name' must be a non-empty string.")
        if isinstance(self.gpi_metrics, dict):
            normalized = {str(k).lower(): v for k, v in self.gpi_metrics.items()}
            missing = [k for k in ("s", "k", "a", "p") if k not in normalized]
            if missing:
                raise ValueError(f"gpi_metrics dictionary is missing required metric keys: {missing}")
            self.gpi_metrics = GPIMetrics(
                s=float(normalized["s"]),
                k=float(normalized["k"]),
                a=float(normalized["a"]),
                p=float(normalized["p"]),
            )


@dataclass
class DecisionResult:
    """Evaluation result from Two-Stage Decision Framework.

    Attributes:
        name: Name of the evaluated capability.
        tier: Selected architectural tier.
        passed_gate_0: True if capability traversed Gate 0 (non-deterministic).
        passed_gate_1: True if capability traversed Gate 1 (non-orchestrator).
        gpi_score: Calculated GPI score (None if halted at Stage 1).
        allow_standalone_skill: True only if Tier 2B Standalone Kernel Skill.
        target_location: Prescribed filesystem or package location for code.
        rationale: Justification citing RES-2026-ARCH-001 architectural rules.
        breakdown: Detailed score breakdown for Stage 2 (if evaluated).
        metadata: Contextual metadata.
    """

    name: str
    tier: ArchitectureTier
    passed_gate_0: bool
    passed_gate_1: bool
    gpi_score: float | None
    allow_standalone_skill: bool
    target_location: str
    rationale: str
    breakdown: dict[str, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def calculate_gpi(s: float, k: float, a: float, p: float) -> float:
    """Compute Granularity & Placement Index (GPI) from raw metric scores.

    Args:
        s: Reasoning Steps (1-5).
        k: Interface / Schema Complexity (1-5).
        a: Autonomous Model Invocation (1-5).
        p: Parent Domain Coupling (1-5).

    Returns:
        float: Computed GPI score.
    """
    metrics = GPIMetrics(s=s, k=k, a=a, p=p)
    return metrics.calculate()


def evaluate_two_stage_decision(request: DecisionRequest) -> DecisionResult:
    """Evaluate capability placement through the Two-Stage Granularity Decision Framework.

    Stage 1:
      - Gate 0 (Determinism Gate): If 100% deterministic -> Tier 1 (Package Function).
      - Gate 1 (Orchestration Gate): If multi-agent / checkpoints / HITL -> Tier 3 (Orchestrator).

    Stage 2:
      - Granularity & Placement Index (GPI):
        - GPI < 12.0  -> Tier 2A (Progressive Reference in references/*.md).
        - GPI >= 12.0 -> Tier 2B (Standalone Kernel Skill in .agents/skills/ccba-<name>/).

    Args:
        request: DecisionRequest containing task characteristics and metrics.

    Returns:
        DecisionResult: Prescribed architecture tier, location, and rationale.
    """
    clean_name = request.name.strip().lstrip("/").lower()
    if not clean_name:
        raise ValueError("Capability 'name' must be a non-empty string.")

    # Stage 1: Gate 0 — Determinism Gate
    if request.is_deterministic:
        return DecisionResult(
            name=request.name,
            tier=ArchitectureTier.TIER_1_PACKAGE,
            passed_gate_0=False,
            passed_gate_1=False,
            gpi_score=None,
            allow_standalone_skill=False,
            target_location="packages/*/src",
            rationale=(
                "Cổng 0 (Determinism Gate): Tác vụ có thể giải quyết 100% bằng giải thuật xác định "
                "(regex, AST parse, math, file I/O). Bắt buộc triển khai tại Tầng 1 "
                "(Package Function / Deep Seam trong packages/*). Cấm tạo Skill độc lập."
            ),
            metadata=request.metadata,
        )

    # Stage 1: Gate 1 — Orchestration Gate
    if request.is_orchestrated:
        return DecisionResult(
            name=request.name,
            tier=ArchitectureTier.TIER_3_ORCHESTRATOR,
            passed_gate_0=True,
            passed_gate_1=False,
            gpi_score=None,
            allow_standalone_skill=False,
            target_location="Tầng 3: Composite Orchestrator (.agents/workflows/)",
            rationale=(
                "Cổng 1 (Orchestration Gate): Tác vụ có điều phối nhiều tác tử song song, "
                "chuyển trạng thái StateGraph checkpoints hoặc cần con người phê duyệt (HITL). "
                "Bắt buộc triển khai tại Tầng 3 (Composite Orchestrator)."
            ),
            metadata=request.metadata,
        )

    # Stage 2: Granularity & Placement Index (GPI)
    if request.gpi_metrics is None:
        raise ValueError(
            f"Stage 2 evaluation requires 'gpi_metrics' for capability '{request.name}' "
            "when Stage 1 invariant gates (Gate 0 and Gate 1) are passed."
        )

    if isinstance(request.gpi_metrics, dict):
        normalized = {str(k).lower(): v for k, v in request.gpi_metrics.items()}
        metrics = GPIMetrics(
            s=float(normalized["s"]),
            k=float(normalized["k"]),
            a=float(normalized["a"]),
            p=float(normalized["p"]),
        )
    else:
        metrics = request.gpi_metrics

    gpi_score = metrics.calculate()
    if math.isnan(gpi_score) or math.isinf(gpi_score):
        raise ValueError(f"Invalid calculated GPI score: {gpi_score}")

    breakdown = metrics.breakdown()

    if gpi_score < GPI_STANDALONE_THRESHOLD:
        parent_hint = (
            f"của Master Skill '{request.parent_skill}'"
            if request.parent_skill
            else "của Master Skill sở hữu"
        )
        base_ref_name = clean_name[:-3] if clean_name.endswith(".md") else clean_name
        target = f"references/{base_ref_name}.md ({parent_hint})"
        return DecisionResult(
            name=request.name,
            tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
            passed_gate_0=True,
            passed_gate_1=True,
            gpi_score=gpi_score,
            allow_standalone_skill=False,
            target_location=target,
            rationale=(
                f"Chỉ số GPI ({gpi_score:.2f}) < {GPI_STANDALONE_THRESHOLD}. Phân loại: "
                f"Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu "
                f"trong references/*.md {parent_hint}; cảnh báo/từ chối tạo thư mục Skill độc lập."
            ),
            breakdown=breakdown,
            metadata=request.metadata,
        )

    # GPI >= 12.0 -> Tier 2B Standalone Kernel Skill
    if clean_name.startswith(("ccba-", "bigbim-")) or clean_name == "platform-loader":
        folder_name = clean_name
    else:
        folder_name = f"ccba-{clean_name}"

    target = f".agents/skills/{folder_name}/"
    return DecisionResult(
        name=request.name,
        tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        passed_gate_0=True,
        passed_gate_1=True,
        gpi_score=gpi_score,
        allow_standalone_skill=True,
        target_location=target,
        rationale=(
            f"Chỉ số GPI ({gpi_score:.2f}) >= {GPI_STANDALONE_THRESHOLD}. Phân loại: "
            f"Tier 2B (Standalone Kernel Skill). Được phép tạo thư mục Skill riêng "
            f"trong {target}."
        ),
        breakdown=breakdown,
        metadata=request.metadata,
    )
