"""scorers/domain.py - Domain-specific scorers and factory functions for CCBA skill archetypes."""

from __future__ import annotations

import re
from typing import Any

from ..models import EvalItem, ScoreResult
from ._domain_bim_pccc import (
    BimClassificationScorer,
    PcccParametricScorer,
    _build_quad_regex_scorers,
    get_bigbim_governance_scorers,
    get_bigbim_rase_scorers,
    get_bigbim_risk_scorers,
    get_bim_classification_scorers,
    get_pccc_scorers,
)
from ._domain_legal import (
    AntiDebrisScorer,
    ExecutionGuardrailScorer,
    LegalToolingIntegrityScorer,
    LegalVerbatimProvenanceScorer,
    PlatformToolingIntegrityScorer,
    ProgressiveDisclosureScorer,
    Sha256ProvenanceScorer,
    get_legal_scorers,
    get_legal_tooling_scorers,
    get_platform_tooling_scorers,
)
from .base import BaseScorer, get_scorer_params
from .rule_based import LengthBoundsScorer, RegexScorer

__all__ = [
    "AntiDebrisScorer",
    "BimClassificationScorer",
    "DiagramSyntaxScorer",
    "EngineeringDisciplineScorer",
    "ExecutionGuardrailScorer",
    "HandoffProtocolScorer",
    "HardCompletionLockScorer",
    "LeanStructuralScorer",
    "LegalToolingIntegrityScorer",
    "LegalVerbatimProvenanceScorer",
    "OfficeStandardScorer",
    "PcccParametricScorer",
    "PlatformToolingIntegrityScorer",
    "ProgressiveDisclosureScorer",
    "Sha256ProvenanceScorer",
    "SingleWriterInvariantScorer",
    "get_academic_scorers",
    "get_adr_lifecycle_scorers",
    "get_bigbim_governance_scorers",
    "get_bigbim_rase_scorers",
    "get_bigbim_risk_scorers",
    "get_bim_classification_scorers",
    "get_coding_scorers",
    "get_grilling_scorers",
    "get_lean_structural_scorers",
    "get_legal_scorers",
    "get_legal_tooling_scorers",
    "get_office_scorers",
    "get_orchestration_scorers",
    "get_pccc_scorers",
    "get_platform_tooling_scorers",
    "get_skill_repair_scorers",
    "get_visual_design_scorers",
    "get_visual_diagram_scorers",
]


class SingleWriterInvariantScorer(BaseScorer):
    """Validates that agent coordination outputs respect Single-Writer invariants and isolated sandboxes."""

    def __init__(
        self,
        name: str = "single_writer_invariant",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(single-writer|isolated|sandbox|working directory|thư mục làm việc|riêng biệt|độc lập|mutex|flock|\.agents/|append-only)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Single-Writer invariant verified (isolated sandbox / separate directory / lock)"
                if matched
                else "Single-Writer violation: missing working directory isolation, sandbox, or mutex guardrail"
            ),
            is_critical_fail=is_crit_fail,
        )


class HandoffProtocolScorer(BaseScorer):
    """Validates agent handoff protocol, parent notification, RACI alignment, and completion verdicts."""

    def __init__(
        self,
        name: str = "handoff_protocol",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.protocol_pattern = re.compile(
            r"(handoff|send_message|parent|verdict|kết luận|bàn giao|raci|chủ trì|bộ môn|clean|violation|hoàn tất|báo cáo)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.protocol_pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Handoff protocol verified (send_message / handoff report / verdict / role boundary)"
                if matched
                else "Missing handoff protocol, completion verdict, or parent notification pattern"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_orchestration_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for multi-agent orchestration skills."""
    p_sw = get_scorer_params(
        "orchestration",
        "single_writer_invariant",
        {"weight": 0.35, "is_critical": True},
        override_config,
    )
    p_pd = get_scorer_params(
        "orchestration",
        "progressive_disclosure",
        {"weight": 0.35, "is_critical": False},
        override_config,
    )
    p_ho = get_scorer_params(
        "orchestration",
        "handoff_protocol",
        {"weight": 0.30, "is_critical": False},
        override_config,
    )
    return [
        SingleWriterInvariantScorer(weight=p_sw["weight"], is_critical=p_sw["is_critical"]),
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        HandoffProtocolScorer(weight=p_ho["weight"], is_critical=p_ho["is_critical"]),
    ]


class HardCompletionLockScorer(BaseScorer):
    """Validates that coding/engineering tasks enforce deterministic verification and Hard Completion Lock (ADR-0058)."""

    def __init__(
        self,
        name: str = "hard_completion_lock",
        weight: float = 0.4,
        is_critical: bool = True,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(python -m ccba_harness verify-patch|verify-patch|pytest|test execution|deterministic verification|khóa cứng hoàn tất|hard completion lock)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Hard Completion Lock verified (python -m ccba_harness verify-patch / deterministic verification)"
                if matched
                else "Missing Hard Completion Lock: must verify via `python -m ccba_harness verify-patch` or deterministic test suite"
            ),
            is_critical_fail=is_crit_fail,
        )


class EngineeringDisciplineScorer(BaseScorer):
    """Validates engineering rigor: Double-Pass Review, KISS, idempotency, RCA, and explicit error handling."""

    def __init__(
        self,
        name: str = "engineering_discipline",
        weight: float = 0.35,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.double_pass_pattern = re.compile(
            r"(double-pass|self-adversarial|root cause|rca|code-first|rà soát hai vòng)",
            re.IGNORECASE,
        )
        self.engineering_rigor_pattern = re.compile(
            r"(kiss|idempotent|idempotency|error handling|test coverage|type hint|deep module|seam|refactor)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        has_dp = bool(self.double_pass_pattern.search(out_str))
        has_rigor = bool(self.engineering_rigor_pattern.search(out_str))

        if has_dp and has_rigor:
            score = 1.0
            reasoning = "Engineering discipline fully verified (Double-Pass Review + KISS / Rigor Guardrails)"
        elif has_dp or has_rigor:
            score = 0.5
            reasoning = "Partial engineering discipline verified: " + (
                "Double-Pass present, missing KISS/Rigor"
                if has_dp
                else "KISS/Rigor present, missing Double-Pass"
            )
        else:
            score = 0.0
            reasoning = "Missing engineering discipline guardrails (Double-Pass Review, KISS, RCA, or Error Handling)"

        is_crit_fail = self.is_critical and score == 0.0

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"double_pass": has_dp, "rigor": has_rigor},
            reasoning=reasoning,
            is_critical_fail=is_crit_fail,
        )


def get_coding_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for coding and software engineering skills."""
    p_lock = get_scorer_params(
        "coding",
        "hard_completion_lock",
        {"weight": 0.40, "is_critical": True},
        override_config,
    )
    p_eng = get_scorer_params(
        "coding",
        "engineering_discipline",
        {"weight": 0.35, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "coding",
        "depth",
        {"weight": 0.25, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        HardCompletionLockScorer(weight=p_lock["weight"], is_critical=p_lock["is_critical"]),
        EngineeringDisciplineScorer(weight=p_eng["weight"], is_critical=p_eng["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


class LeanStructuralScorer(BaseScorer):
    """Composite lean structural scorer evaluating progressive disclosure, length bounds, and anti-debris."""

    def __init__(
        self,
        name: str = "lean_structural",
        weight: float = 1.0,
        is_critical: bool = False,
        min_length: int = 20,
        max_length: int = 25000,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.progressive_scorer = ProgressiveDisclosureScorer(weight=0.4)
        self.length_scorer = LengthBoundsScorer(
            name="depth", min_length=min_length, max_length=max_length, weight=0.3
        )
        self.debris_scorer = AntiDebrisScorer(weight=0.3)

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        res_prog = await self.progressive_scorer.score(output, item)
        res_len = await self.length_scorer.score(output, item)
        res_deb = await self.debris_scorer.score(output, item)

        combined_score = (res_prog.score * 0.4) + (res_len.score * 0.3) + (res_deb.score * 0.3)
        is_crit = self.is_critical and (
            res_prog.is_critical_fail or res_len.is_critical_fail or res_deb.is_critical_fail
        )

        reasons = [r for r in (res_prog.reasoning, res_len.reasoning, res_deb.reasoning) if r]
        return ScoreResult(
            scorer_name=self.name,
            score=combined_score,
            raw_output={
                "progressive": res_prog.score,
                "length": res_len.score,
                "anti_debris": res_deb.score,
            },
            reasoning="; ".join(reasons),
            is_critical_fail=is_crit,
        )


def get_lean_structural_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard safe lean structural scorer suite for generic and non-coding skills."""
    p_pd = get_scorer_params(
        "lean_structural",
        "progressive_disclosure",
        {"weight": 0.40, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "lean_structural",
        "depth",
        {"weight": 0.30, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    p_deb = get_scorer_params(
        "lean_structural",
        "anti_debris",
        {"weight": 0.30, "is_critical": False},
        override_config,
    )
    return [
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
        AntiDebrisScorer(weight=p_deb["weight"], is_critical=p_deb["is_critical"]),
    ]


class OfficeStandardScorer(BaseScorer):
    """Evaluates Office document formatting, typography, administrative standards (NĐ 30/2020), presentation slides, seminars, and technical copywriting."""

    def __init__(
        self,
        name: str = "office_standard",
        weight: float = 0.45,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(Nghị định 30/2020|NĐ 30/2020|thể thức|soạn thảo|Quốc hiệu|Tiêu ngữ|Nơi nhận|thẩm quyền|số/ký hiệu|địa danh|trích yếu|công văn|hành chính|"
            r"Times New Roman|bố cục|tiêu đề|phông chữ|typography|heading|mục lục|canh lề|căn lề|hierarchy|phân cấp|bullet point|callout|"
            r"bảng|bảng biểu|markdown table|gfm|ngắt dòng|line break|<br\s*/?>|"
            r"docx|pptx|slide|trình bày|thuyết trình|presentation|visual bullet|"
            r"seminar|agenda|curriculum|đề cương|bài giảng|mục tiêu đào tạo|handout|tài liệu phát tay|timeline|"
            r"copywriting|truyền thông|bài viết|hook|call-to-action|cta|giải pháp công nghệ|giải pháp kỹ thuật|giải pháp đột phá)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Office document standard verified (NĐ 30/2020 / typography / layout / slide / seminar / copywriting guidelines)"
                if matched
                else "Missing office document formatting, typography, slide, seminar, or copywriting standards"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_office_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for Office, Docx, Pptx, and typography skills."""
    p_off = get_scorer_params(
        "office",
        "office_standard",
        {"weight": 0.45, "is_critical": False},
        override_config,
    )
    p_pd = get_scorer_params(
        "office",
        "progressive_disclosure",
        {"weight": 0.25, "is_critical": False},
        override_config,
    )
    p_deb = get_scorer_params(
        "office",
        "anti_debris",
        {"weight": 0.15, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "office",
        "depth",
        {"weight": 0.15, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        OfficeStandardScorer(weight=p_off["weight"], is_critical=p_off["is_critical"]),
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        AntiDebrisScorer(weight=p_deb["weight"], is_critical=p_deb["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


class DiagramSyntaxScorer(BaseScorer):
    """Evaluates Mermaid, Excalidraw, and architectural visual diagram syntax."""

    def __init__(
        self,
        name: str = "diagram_syntax",
        weight: float = 0.45,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(graph\s+(?:TD|LR|TB|BT)|flowchart\s+(?:TD|LR|TB|BT)|sequenceDiagram|classDiagram|erDiagram|stateDiagram|-->|---|subgraph|style|fill:|stroke:|```mermaid|```excalidraw|nodes|edges)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        matched = bool(self.pattern.search(out_str))
        score = 1.0 if matched else 0.0
        is_crit_fail = self.is_critical and not matched

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=matched,
            reasoning=(
                "Diagram syntax verified (Mermaid / Excalidraw notation or visual flow syntax)"
                if matched
                else "Missing visual diagram syntax (Mermaid flowchart, sequence, or Excalidraw block)"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_visual_diagram_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for Mermaid, Excalidraw, and diagram skills."""
    p_dia = get_scorer_params(
        "visual_diagram",
        "diagram_syntax",
        {"weight": 0.45, "is_critical": False},
        override_config,
    )
    p_pd = get_scorer_params(
        "visual_diagram",
        "progressive_disclosure",
        {"weight": 0.25, "is_critical": False},
        override_config,
    )
    p_deb = get_scorer_params(
        "visual_diagram",
        "anti_debris",
        {"weight": 0.15, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "visual_diagram",
        "depth",
        {"weight": 0.15, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        DiagramSyntaxScorer(weight=p_dia["weight"], is_critical=p_dia["is_critical"]),
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        AntiDebrisScorer(weight=p_deb["weight"], is_critical=p_deb["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_academic_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for academic and scientific writing skills."""
    p_str = get_scorer_params("academic", "academic_structure", override_config, default_weight=0.5)
    p_rig = get_scorer_params(
        "academic",
        "academic_rigor_hard_floor",
        override_config,
        default_weight=0.3,
        default_is_critical=True,
    )
    p_len = get_scorer_params(
        "academic",
        "depth",
        override_config,
        default_weight=0.2,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="academic_structure",
            pattern=r"(IMRAD|CARS|Move 1|Move 2|Move 3|Materials|Methods|Results|Discussion|References|Style|Yale|APA)",
            weight=p_str["weight"],
            is_critical=p_str["is_critical"],
        ),
        RegexScorer(
            name="academic_rigor_hard_floor",
            pattern=r"(Swales|Kallestinova|APA|BibTeX|limitations|giới hạn|bị động|passive|De-nominalization)",
            weight=p_rig["weight"],
            is_critical=p_rig["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_grilling_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for Socratic grilling, design stress-testing, and prototype review."""
    return _build_quad_regex_scorers(
        "grilling",
        [
            (
                "grilling_one_by_one_and_recommendation",
                r"(câu hỏi|one-by-one|đề xuất|phương án|recommended|stress-test|chất vấn|front-end|picker)",
                0.35,
                False,
            ),
            (
                "grilling_anti_trap_hard_floor",
                r"(từng câu|đề xuất trước|facts vs decisions|tra cứu|tự tra cứu|codebase|NOTES\.md|ccba-issue-tree|vi phạm|bất biến)",
                0.35,
                True,
            ),
            (
                "grilling_escalation_guard",
                r"(ccba-issue-tree|How-Tree|Why-Tree|Solution How-Tree|ma trận|Giá trị|Độ phức tạp|Rủi ro|KISS|Frontier|prerequisites)",
                0.20,
                False,
            ),
        ],
        override_config,
    )


def get_adr_lifecycle_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for Architecture Decision Record (ADR) lifecycle governance."""
    return _build_quad_regex_scorers(
        "adr_lifecycle",
        [
            (
                "adr_scaffolding_and_lifecycle",
                r"(ADR|HUB-ADR|SPOKE-ADR|ACCEPTED|SUPERSEDED|DEPRECATED|docs/adr/|TRACEABILITY_MATRIX|matrix)",
                0.35,
                False,
            ),
            (
                "adr_anti_trap_hard_floor",
                r"(superseded_by|supersedes|validate_adr_traceability|CI Parity|Context|Decision|Consequences|Invariants)",
                0.35,
                True,
            ),
            (
                "adr_governance_guard",
                r"(Hub vs Spoke|SPOKE-ADR|HUB-ADR|Living Traceability Matrix|README\.md|YAML Frontmatter|parity)",
                0.20,
                False,
            ),
        ],
        override_config,
    )


def get_skill_repair_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for SKILL.md linter, GPI, and ADR-0057 governance repair."""
    return _build_quad_regex_scorers(
        "skill_repair",
        [
            (
                "skill_repair_gpi_and_frontmatter",
                r"(gpi|yaml|frontmatter|adr-0057|tier 2b|kernel|res-2026-arch-001|khối gpi)",
                0.35,
                False,
            ),
            (
                "skill_repair_anti_trap_hard_floor",
                r"(cổng 0|gate 0|determinism|deep seam|packages/|cổng 1|gate 1|composite orchestrator|tiêu chí hoàn thành|completion criterion|validate_skills|evaluate-gpi)",
                0.35,
                True,
            ),
            (
                "skill_repair_debloat_and_verification",
                r"(script bloat|100 loc|compile_catalog|tương đối|relative|linter|cú pháp yaml|phục hồi)",
                0.20,
                False,
            ),
        ],
        override_config,
    )


def get_visual_design_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for brand identity, design tokens, typography, and CIP."""
    return _build_quad_regex_scorers(
        "visual_design",
        [
            (
                "visual_design_tokens_and_colors",
                r"(design token|color|palette|primary|secondary|neutral|semantic|#[0-9a-fA-F]{3,8}|hex|mã màu)",
                0.35,
                False,
            ),
            (
                "visual_design_brand_and_guidelines",
                r"(brand|logo|safe zone|clear space|vùng an toàn|cip|corporate identity|ấn phẩm|nhận diện|quy chuẩn)",
                0.35,
                True,
            ),
            (
                "visual_design_typography_and_assets",
                r"(typography|font|scale|hierarchy|phân cấp|banner|generate_image|prompt|tỷ lệ|aspect ratio)",
                0.20,
                False,
            ),
        ],
        override_config,
    )
