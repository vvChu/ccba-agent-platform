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

# Hysteresis Deadband per ADR-0057 & Wayfinder Ticket 2
GPI_DEADBAND_LOWER: float = 11.5
GPI_DEADBAND_UPPER: float = 12.5

# Metric Bounds
MIN_METRIC_SCORE: float = 1.0
MAX_METRIC_SCORE: float = 5.0


class ArchitectureTier(str, Enum):
    """Architectural placement tier classification."""

    TIER_1_PACKAGE = "Tier 1: Package Function / Deep Seam"
    TIER_2A_PROGRESSIVE_REFERENCE = "Tier 2A: Progressive Reference"
    TIER_2B_STANDALONE_KERNEL_SKILL = "Tier 2B: Standalone Kernel Skill"
    TIER_3_ORCHESTRATOR = "Tier 3: Composite Orchestrator"


TIER_STR_MAP: dict[str, ArchitectureTier] = {
    "tier-1": ArchitectureTier.TIER_1_PACKAGE,
    "tier_1": ArchitectureTier.TIER_1_PACKAGE,
    "tier 1": ArchitectureTier.TIER_1_PACKAGE,
    "tier 1: package function / deep seam": ArchitectureTier.TIER_1_PACKAGE,
    "tier-2a": ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    "tier_2a": ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    "tier 2a": ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    "tier 2a: progressive reference": ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
    "tier-2b": ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    "tier_2b": ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    "tier 2b": ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    "tier 2b: standalone kernel skill": ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    "tier-3": ArchitectureTier.TIER_3_ORCHESTRATOR,
    "tier_3": ArchitectureTier.TIER_3_ORCHESTRATOR,
    "tier 3": ArchitectureTier.TIER_3_ORCHESTRATOR,
    "tier 3: composite orchestrator": ArchitectureTier.TIER_3_ORCHESTRATOR,
}


@dataclass(frozen=True)
class CanonicalAnchor:
    """A canonical invariant benchmark anchor representing architectural tiers."""

    name: str
    expected_tier: ArchitectureTier
    is_deterministic: bool = False
    is_orchestrated: bool = False
    s: float | None = None
    k: float | None = None
    a: float | None = None
    p: float | None = None
    description: str = ""


CANONICAL_ANCHORS: tuple[CanonicalAnchor, ...] = (
    # 10 Tier 1 Anchors: Package Functions / Deep Seams (Gate 0 Deterministic)
    CanonicalAnchor(
        name="ccba_ooxml.format",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="OOXML document formatting and table styling deep seam",
    ),
    CanonicalAnchor(
        name="ccba_pdf_prep.chunker",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="PDF page segmentation and chunking deep seam",
    ),
    CanonicalAnchor(
        name="ccba_legal.crawler",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Legal document crawler and raw HTML DOM parser",
    ),
    CanonicalAnchor(
        name="ccba_maskara.redact",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Regex-based secret and credential redaction engine",
    ),
    CanonicalAnchor(
        name="ccba_qc_core.geometry",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Geometric intersection and bounding box calculation algorithms",
    ),
    CanonicalAnchor(
        name="mdconverter.pandoc",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Pandoc markdown document conversion wrapper",
    ),
    CanonicalAnchor(
        name="ccba_core.config",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Platform configuration and environment loader",
    ),
    CanonicalAnchor(
        name="ccba_harness.gpi",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Mathematical formula calculation and invariant gating engine",
    ),
    CanonicalAnchor(
        name="ccba_harness.telemetry",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Otel span exporter and session metrics aggregator",
    ),
    CanonicalAnchor(
        name="ccba_harness.verifier",
        expected_tier=ArchitectureTier.TIER_1_PACKAGE,
        is_deterministic=True,
        description="Subprocess test runner and status code verification engine",
    ),
    # 10 Tier 2A Anchors: Progressive References (GPI < 12.0)
    CanonicalAnchor(
        name="qto_table_mapping.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=1.0,
        a=2.0,
        p=4.0,
        description="QTO table mapping specification (GPI: 5.0)",
    ),
    CanonicalAnchor(
        name="meeting_minutes_guide.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=1.0,
        a=2.0,
        p=3.0,
        description="Meeting minutes authoring guideline (GPI: 6.5)",
    ),
    CanonicalAnchor(
        name="pccc_standards_ref.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=2.0,
        a=2.0,
        p=3.0,
        description="Fire safety standard clause cross-reference (GPI: 8.5)",
    ),
    CanonicalAnchor(
        name="uniclass_element_table.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=3.0,
        k=1.0,
        a=2.0,
        p=3.0,
        description="Uniclass 2015 element classification lookup (GPI: 9.0)",
    ),
    CanonicalAnchor(
        name="legal_term_glossary.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=2.0,
        a=2.0,
        p=4.0,
        description="Vietnamese legal construction terminology glossary (GPI: 7.0)",
    ),
    CanonicalAnchor(
        name="room_naming_convention.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=2.0,
        a=2.0,
        p=3.0,
        description="ISO 19650 room naming syntax guidelines (GPI: 8.5)",
    ),
    CanonicalAnchor(
        name="bim_lod_checklist.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=2.0,
        a=2.0,
        p=4.0,
        description="BIM Level of Development checklist (GPI: 7.0)",
    ),
    CanonicalAnchor(
        name="fire_damper_specs.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=2.0,
        a=2.0,
        p=3.0,
        description="Fire damper technical specifications (GPI: 8.5)",
    ),
    CanonicalAnchor(
        name="imrad_structure_guide.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=3.0,
        k=1.0,
        a=2.0,
        p=3.0,
        description="IMRaD academic article structure guideline (GPI: 9.0)",
    ),
    CanonicalAnchor(
        name="git_checkpoint_sop.md",
        expected_tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        s=2.0,
        k=1.0,
        a=2.0,
        p=3.0,
        description="Git checkpoint and rollback procedures (GPI: 6.5)",
    ),
    # 10 Tier 2B Anchors: Standalone Kernel Skills (GPI >= 12.0)
    CanonicalAnchor(
        name="ccba-ai-qc-pccc-audit",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=4.0,
        p=1.0,
        description="Multi-disciplinary fire safety design audit (GPI: 22.5)",
    ),
    CanonicalAnchor(
        name="ccba-legal-intel",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=4.0,
        p=1.0,
        description="Autonomous legal intelligence and compliance checklist (GPI: 22.5)",
    ),
    CanonicalAnchor(
        name="bigbim-classification",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=4.0,
        p=1.0,
        description="Uniclass 200 entity and product classification (GPI: 22.5)",
    ),
    CanonicalAnchor(
        name="ccba-academic-writing",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=3.0,
        k=2.0,
        a=4.0,
        p=1.0,
        description="Construction scientific paper and thesis composition (GPI: 18.0)",
    ),
    CanonicalAnchor(
        name="ccba-legal-advisor",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=4.0,
        p=1.0,
        description="Adaptive legal interview and formal opinion memo generation (GPI: 22.5)",
    ),
    CanonicalAnchor(
        name="bigbim-rase",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=3.0,
        p=1.0,
        description="RASE semantic analysis against IFC4X3 schema (GPI: 20.5)",
    ),
    CanonicalAnchor(
        name="bigbim-risk",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=4.0,
        k=3.0,
        a=4.0,
        p=1.0,
        description="Non-geometric information conflict detection (GPI: 22.5)",
    ),
    CanonicalAnchor(
        name="ccba-completion-checklist",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=3.0,
        k=2.0,
        a=4.0,
        p=1.0,
        description="Construction completion checklist synthesis per regulations (GPI: 18.0)",
    ),
    CanonicalAnchor(
        name="ccba-copywriting",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=3.0,
        k=2.0,
        a=3.0,
        p=1.0,
        description="Brand voice copywriting and public announcement generation (GPI: 16.0)",
    ),
    CanonicalAnchor(
        name="ccba-hybrid-rag-search",
        expected_tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        s=3.0,
        k=3.0,
        a=3.0,
        p=2.0,
        description="Hybrid BM25 + dense embedding RRF retrieval engine (GPI: 16.5)",
    ),
)


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
            if (
                math.isnan(val)
                or math.isinf(val)
                or val < MIN_METRIC_SCORE
                or val > MAX_METRIC_SCORE
            ):
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
        existing_tier: Prior architecture tier if capability already exists.
        force_tier_flip: Force tier transition when score falls within hysteresis deadband [11.5, 12.5).
    """

    name: str
    is_deterministic: bool = False
    is_orchestrated: bool = False
    gpi_metrics: GPIMetrics | dict[str, Any] | None = None
    description: str = ""
    parent_skill: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    existing_tier: ArchitectureTier | str | None = None
    force_tier_flip: bool = False

    def __post_init__(self) -> None:
        """Validate input parameters."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Capability 'name' must be a non-empty string.")
        if self.existing_tier is not None:
            if isinstance(self.existing_tier, ArchitectureTier):
                pass
            elif isinstance(self.existing_tier, str):
                cleaned_tier = self.existing_tier.strip().lower()
                matched_tier = TIER_STR_MAP.get(cleaned_tier)
                if matched_tier is not None:
                    self.existing_tier = matched_tier
                else:
                    raise ValueError(
                        f"Unknown existing_tier: '{self.existing_tier}'. "
                        f"Valid choices include: 'tier-1', 'tier-2a', 'tier-2b', 'tier-3'"
                    )
            else:
                raise TypeError(
                    f"existing_tier must be an ArchitectureTier or str, got {type(self.existing_tier).__name__}"
                )
        if isinstance(self.gpi_metrics, dict):
            normalized = {str(k).lower(): v for k, v in self.gpi_metrics.items()}
            missing = [k for k in ("s", "k", "a", "p") if k not in normalized]
            if missing:
                raise ValueError(
                    f"gpi_metrics dictionary is missing required metric keys: {missing}"
                )
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
      - Deadband Hysteresis Engine:
        - When GPI is within [11.5, 12.5) and existing_tier is set (Tier 2A or 2B):
          - If force_tier_flip is False: Existing tier is preserved to prevent architectural churn.
          - If force_tier_flip is True: Standard 12.0 threshold routing is forced.

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

    # Determine default placement from standard threshold (12.0)
    raw_tier = (
        ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE
        if gpi_score < GPI_STANDALONE_THRESHOLD
        else ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL
    )

    in_deadband = GPI_DEADBAND_LOWER <= gpi_score < GPI_DEADBAND_UPPER
    preserved_by_hysteresis = False
    final_tier = raw_tier

    if in_deadband and request.existing_tier in (
        ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
        ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
    ):
        if not request.force_tier_flip:
            final_tier = ArchitectureTier(request.existing_tier)
            preserved_by_hysteresis = True
        else:
            final_tier = raw_tier

    breakdown["deadband_active"] = 1.0 if in_deadband else 0.0
    breakdown["preserved_by_hysteresis"] = 1.0 if preserved_by_hysteresis else 0.0

    parent_hint = (
        f"của Master Skill '{request.parent_skill}'"
        if request.parent_skill
        else "của Master Skill sở hữu"
    )
    base_ref_name = clean_name[:-3] if clean_name.endswith(".md") else clean_name

    if clean_name.startswith(("ccba-", "bigbim-")) or clean_name == "platform-loader":
        folder_name = clean_name
    else:
        folder_name = f"ccba-{clean_name}"

    if final_tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
        target = f"references/{base_ref_name}.md ({parent_hint})"
        if preserved_by_hysteresis:
            rationale = (
                f"Chỉ số GPI ({gpi_score:.2f}) nằm trong vùng đệm trễ "
                f"[{GPI_DEADBAND_LOWER}, {GPI_DEADBAND_UPPER}) (ngưỡng cơ sở {GPI_STANDALONE_THRESHOLD}). "
                f"Phân tầng Tier 2A (Progressive Reference) được BẢO LƯU do cơ chế Hysteresis per ADR-0057 "
                f"để ngăn chặn chao đảo kiến trúc (Architectural Churn). Cần lưu trữ dưới dạng tài liệu tham chiếu "
                f"trong references/*.md {parent_hint}; cảnh báo/từ chối tạo thư mục Skill độc lập. "
                f"(Dùng cờ force_tier_flip nếu muốn cưỡng chế lật tầng)."
            )
        elif in_deadband and request.force_tier_flip:
            rationale = (
                f"Chỉ số GPI ({gpi_score:.2f}) nằm trong vùng đệm trễ "
                f"[{GPI_DEADBAND_LOWER}, {GPI_DEADBAND_UPPER}), nhưng cờ force_tier_flip=True "
                f"được thiết lập; cưỡng chế lật phân tầng sang Tier 2A (Progressive Reference). "
                f"Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md {parent_hint}."
            )
        else:
            rationale = (
                f"Chỉ số GPI ({gpi_score:.2f}) < {GPI_STANDALONE_THRESHOLD}. Phân loại: "
                f"Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu "
                f"trong references/*.md {parent_hint}; cảnh báo/từ chối tạo thư mục Skill độc lập."
            )

        return DecisionResult(
            name=request.name,
            tier=ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE,
            passed_gate_0=True,
            passed_gate_1=True,
            gpi_score=gpi_score,
            allow_standalone_skill=False,
            target_location=target,
            rationale=rationale,
            breakdown=breakdown,
            metadata=request.metadata,
        )

    # Tier 2B Standalone Kernel Skill
    target = f".agents/skills/{folder_name}/"
    if preserved_by_hysteresis:
        rationale = (
            f"Chỉ số GPI ({gpi_score:.2f}) nằm trong vùng đệm trễ "
            f"[{GPI_DEADBAND_LOWER}, {GPI_DEADBAND_UPPER}) (ngưỡng cơ sở {GPI_STANDALONE_THRESHOLD}). "
            f"Phân tầng Tier 2B (Standalone Kernel Skill) được BẢO LƯU do cơ chế Hysteresis per ADR-0057 "
            f"để ngăn chặn chao đảo kiến trúc (Architectural Churn). Được phép duy trì thư mục Skill riêng "
            f"trong {target}. (Dùng cờ force_tier_flip nếu muốn cưỡng chế lật tầng)."
        )
    elif in_deadband and request.force_tier_flip:
        rationale = (
            f"Chỉ số GPI ({gpi_score:.2f}) nằm trong vùng đệm trễ "
            f"[{GPI_DEADBAND_LOWER}, {GPI_DEADBAND_UPPER}), nhưng cờ force_tier_flip=True "
            f"được thiết lập; cưỡng chế lật phân tầng sang Tier 2B (Standalone Kernel Skill). "
            f"Được phép tạo thư mục Skill riêng trong {target}."
        )
    else:
        rationale = (
            f"Chỉ số GPI ({gpi_score:.2f}) >= {GPI_STANDALONE_THRESHOLD}. Phân loại: "
            f"Tier 2B (Standalone Kernel Skill). Được phép tạo thư mục Skill riêng "
            f"trong {target}."
        )

    return DecisionResult(
        name=request.name,
        tier=ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL,
        passed_gate_0=True,
        passed_gate_1=True,
        gpi_score=gpi_score,
        allow_standalone_skill=True,
        target_location=target,
        rationale=rationale,
        breakdown=breakdown,
        metadata=request.metadata,
    )
