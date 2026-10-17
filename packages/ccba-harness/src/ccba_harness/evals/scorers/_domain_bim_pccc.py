"""scorers/_domain_bim_pccc.py - PCCC parametric and BigBIM classification/risk/governance/RASE scorers."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from ..models import EvalItem, ScoreResult
from ..uniclass_index import UniclassFlatIndex, load_uniclass_flat_index
from ._domain_legal import AntiDebrisScorer, ProgressiveDisclosureScorer
from .base import BaseScorer, get_scorer_params
from .rule_based import LengthBoundsScorer, RegexScorer


def _build_quad_regex_scorers(
    archetype: str,
    specs: list[tuple[str, str, float, bool]],
    override_config: dict[str, Any] | None,
    depth_weight: float = 0.1,
    min_length: int = 20,
    max_length: int = 20000,
) -> list[BaseScorer]:
    """Build a 3-RegexScorer + 1-LengthBoundsScorer suite from declarative specs."""
    scorers: list[BaseScorer] = []
    for name, pattern, def_weight, def_crit in specs:
        params = get_scorer_params(
            archetype,
            name,
            override_config,
            default_weight=def_weight,
            default_is_critical=def_crit,
        )
        scorers.append(
            RegexScorer(
                name=name,
                pattern=pattern,
                weight=params["weight"],
                is_critical=params["is_critical"],
            )
        )
    p_len = get_scorer_params(
        archetype,
        "depth",
        override_config,
        default_weight=depth_weight,
        default_min_length=min_length,
        default_max_length=max_length,
    )
    scorers.append(
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        )
    )
    return scorers


class PcccParametricScorer(BaseScorer):
    """Evaluates Fire Protection (PCCC) & Technical QC parametric audit compliance (QCVN 06:2022/BXD)."""

    def __init__(
        self,
        name: str = "pccc_parametric",
        weight: float = 0.5,
        is_critical: bool = True,
        escalation_judge: Any | None = None,
        enable_llm_judge: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.escalation_judge = escalation_judge
        self.enable_llm_judge = enable_llm_judge
        self.default_pccc_pattern = re.compile(
            r"(QCVN|PCCC|bậc chịu lửa|khói|thẩm tra|tiêu chuẩn|thiết kế|hút khói|thoát nạn|ngăn cháy|sprinkler)",
            re.IGNORECASE,
        )

    def _check_forbidden_rules(self, out_str: str, rules: dict[str, Any]) -> ScoreResult | None:
        """Check Gate 1 dual critical hard floors (forbidden verdicts and forbidden parameters)."""
        for p in rules.get("forbidden_verdict_patterns", []):
            if re.search(p, out_str, re.IGNORECASE):
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"gate": 1, "violation": "forbidden_verdict", "matched_pattern": p},
                    reasoning=f"Critical safety failure: Model approved a non-compliant PCCC design ({p})",
                    is_critical_fail=True,
                )

        for fp in rules.get("forbidden_parameters", []):
            pat = fp.get("pattern", "") if isinstance(fp, dict) else str(fp)
            name = fp.get("name", pat) if isinstance(fp, dict) else pat
            if pat and re.search(pat, out_str, re.IGNORECASE):
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={
                        "gate": 1,
                        "violation": "forbidden_parameter",
                        "matched_pattern": pat,
                    },
                    reasoning=f"Critical anti-trap failure: Model adopted prohibited misconception ({name})",
                    is_critical_fail=True,
                )
        return None

    @staticmethod
    def _check_expected_verdict(out_str: str, rules: dict[str, Any]) -> bool:
        """Check whether output matches expected verdict patterns or literal expected_verdict."""
        verdict_patterns = rules.get("verdict_patterns", [])
        exp = rules.get("expected_verdict", "")
        if verdict_patterns:
            matched = any(re.search(p, out_str, re.IGNORECASE) for p in verdict_patterns)
            if not matched and exp:
                matched = bool(re.search(re.escape(exp), out_str, re.IGNORECASE))
            return matched
        if exp:
            return bool(re.search(re.escape(exp), out_str, re.IGNORECASE))
        return True

    @staticmethod
    def _score_parameters_and_legal(
        out_str: str, rules: dict[str, Any]
    ) -> tuple[int, int, list[Any], bool, float]:
        """Compute parameter match counts, missing parameter list, legal basis match, and Gate 1 score."""
        req_params = rules.get("required_parameters", [])
        matched_count = 0
        total_count = len(req_params)
        missing_params: list[Any] = []
        for rp in req_params:
            pat = rp.get("pattern", "") if isinstance(rp, dict) else str(rp)
            name = rp.get("name", pat) if isinstance(rp, dict) else pat
            if pat and re.search(pat, out_str, re.IGNORECASE):
                matched_count += 1
            else:
                missing_params.append(name)

        param_score = (matched_count / total_count) if total_count > 0 else 1.0
        legal_basis_pat = rules.get("legal_basis", "")
        legal_matched = (
            bool(re.search(legal_basis_pat, out_str, re.IGNORECASE)) if legal_basis_pat else True
        )
        legal_score = 1.0 if legal_matched else 0.5
        gate1_score = 0.4 * 1.0 + 0.4 * param_score + 0.2 * legal_score
        return matched_count, total_count, missing_params, legal_matched, gate1_score

    async def _apply_escalation_judge(
        self,
        out_str: str,
        item: EvalItem,
        rules: dict[str, Any],
        gate1_score: float,
        reasoning: str,
    ) -> tuple[float, str]:
        """Optionally run Gate 2 escalation LLM judge when Gate 1 score falls in [0.40, 0.85]."""
        if not (
            self.enable_llm_judge
            and self.escalation_judge is not None
            and 0.40 <= gate1_score <= 0.85
        ):
            return gate1_score, reasoning
        try:
            if asyncio.iscoroutinefunction(self.escalation_judge):
                judge_res = await self.escalation_judge(out_str, item, rules)
            else:
                judge_res = self.escalation_judge(out_str, item, rules)
            if isinstance(judge_res, (int, float)):
                final_score = float(judge_res)
                return final_score, f"{reasoning}; Gate 2 LLM Judge adjudicated: {final_score:.2f}"
        except Exception as e:
            return gate1_score, f"{reasoning}; Gate 2 LLM Judge fallback triggered ({e})"
        return gate1_score, reasoning

    def _fallback_regex_score(self, out_str: str) -> ScoreResult:
        """Evaluate output using fallback PCCC terminology regex when parametric_rules are absent."""
        matched = bool(self.default_pccc_pattern.search(out_str))
        msg = "Standard PCCC terminology detected" if matched else "Missing basic PCCC terminology"
        return ScoreResult(
            scorer_name=self.name,
            score=1.0 if matched else 0.0,
            raw_output={"mode": "fallback_regex", "matched": matched},
            reasoning=msg,
            is_critical_fail=self.is_critical and not matched,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        rules = meta.get("parametric_rules")
        if not isinstance(rules, dict):
            return self._fallback_regex_score(out_str)

        if (forbidden_res := self._check_forbidden_rules(out_str, rules)) is not None:
            return forbidden_res

        verdict_matched = self._check_expected_verdict(out_str, rules)
        if not verdict_matched:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output={"gate": 1, "violation": "missing_expected_verdict"},
                reasoning="Verdict incorrect: Model failed to state the required PCCC audit conclusion",
                is_critical_fail=self.is_critical,
            )

        matched_cnt, total_cnt, missing_params, legal_matched, gate1_score = (
            self._score_parameters_and_legal(out_str, rules)
        )
        reasoning = f"Gate 1: Verdict verified; {matched_cnt}/{total_cnt} parameters verified"
        if missing_params:
            reasoning += f" (missing: {', '.join(str(p) for p in missing_params)})"

        final_score, reasoning = await self._apply_escalation_judge(
            out_str, item, rules, gate1_score, reasoning
        )
        raw_out = {
            "gate": 1,
            "gate1_score": gate1_score,
            "verdict_matched": verdict_matched,
            "matched_params": matched_cnt,
            "total_params": total_cnt,
            "missing_params": missing_params,
            "legal_basis_matched": legal_matched,
        }
        return ScoreResult(
            scorer_name=self.name,
            score=final_score,
            raw_output=raw_out,
            reasoning=reasoning,
            is_critical_fail=False,
        )


def get_pccc_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for PCCC, Smoke Control, and Technical QC skills."""
    p_pccc = get_scorer_params(
        "pccc", "pccc_parametric", override_config, default_weight=0.5, default_is_critical=True
    )
    p_pd = get_scorer_params("pccc", "progressive_disclosure", override_config, default_weight=0.2)
    p_deb = get_scorer_params("pccc", "anti_debris", override_config, default_weight=0.15)
    p_len = get_scorer_params(
        "pccc",
        "depth",
        override_config,
        default_weight=0.15,
        default_min_length=20,
        default_max_length=25000,
    )
    return [
        PcccParametricScorer(weight=p_pccc["weight"], is_critical=p_pccc["is_critical"]),
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


class BimClassificationScorer(BaseScorer):
    """BIM Classification & Uniclass 200 / ISO 12006-2 Validator (TICKET-005)."""

    def __init__(
        self,
        name: str = "bim_classification",
        weight: float = 0.5,
        is_critical: bool = True,
        index: UniclassFlatIndex | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.index = index or load_uniclass_flat_index()

    def _score_uniclass_code(
        self, out_str: str, extracted_codes: list[str], expected_code: str
    ) -> float:
        """Compute Dimension 1 Uniclass Code & Table Validity score."""
        if expected_code:
            if expected_code in extracted_codes:
                return 1.0
            if any(c.startswith(expected_code[:5]) for c in extracted_codes):
                return 0.7
            if any(c.split("_")[0] == expected_code.split("_")[0] for c in extracted_codes):
                return 0.5
            return 0.0
        if extracted_codes:
            valid_count = sum(1 for c in extracted_codes if self.index.is_valid_code(c))
            return 1.0 if valid_count > 0 else 0.5
        if re.search(
            r"\b(Uniclass|ISO\s*12006|EF_|SL_|Ss_|Pr_|En_|Co_|PM_)\b", out_str, re.IGNORECASE
        ):
            return 0.5
        return 0.0

    @staticmethod
    def _score_iso_12006_layer(out_str: str, expected_layer: str) -> float:
        """Compute Dimension 2 ISO 12006-2 Layer Classification score."""
        if expected_layer:
            layer_kw = expected_layer.split()[0].lower()
            if re.search(rf"\b{re.escape(layer_kw)}\b", out_str, re.IGNORECASE):
                return 1.0
            if "iso 12006" in out_str.lower() or "iso 22274" in out_str.lower():
                return 0.6
            return 0.3
        if re.search(
            r"(ISO\s*12006|Result|Resource|Process|Property|kết quả|nguồn lực|quy trình)",
            out_str,
            re.IGNORECASE,
        ):
            return 1.0
        return 0.5

    def _score_naming_convention(self, out_str: str, expected_naming: Any) -> float:
        """Compute Dimension 3 Container Naming Convention & Standards Compliance score."""
        lines = [line.strip() for line in out_str.splitlines()]
        if expected_naming:
            expected_naming_str = str(expected_naming).strip()
            if expected_naming_str in out_str:
                return 1.0
            if self.index.validate_iso_19650_naming(expected_naming_str) and any(
                self.index.validate_iso_19650_naming(ln) for ln in lines
            ):
                return 0.8
            if self.index.validate_ifc_alignment_naming(expected_naming_str) and any(
                self.index.validate_ifc_alignment_naming(ln) for ln in lines
            ):
                return 0.8
            if re.search(r"ISO\s*19650|IFC\s*Alignment|Container|đặt tên", out_str, re.IGNORECASE):
                return 0.5
            return 0.2
        if any(self.index.validate_iso_19650_naming(ln) for ln in lines) or any(
            self.index.validate_ifc_alignment_naming(ln) for ln in lines
        ):
            return 1.0
        if re.search(
            r"(ISO\s*19650|IFC\s*Alignment|ISO\s*22274|ISO\s*21511|Digital Memory|Trí Nhớ Số)",
            out_str,
            re.IGNORECASE,
        ):
            return 0.8
        return 0.4

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        ga = item.golden_answer if isinstance(item.golden_answer, dict) else {}

        has_trap, trap_reason = self.index.check_anti_traps(out_str)
        if has_trap:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output={"violation": "anti_trap", "reason": trap_reason},
                reasoning=f"Critical Hard Floor Failure: {trap_reason}",
                is_critical_fail=True,
            )

        extracted_codes = self.index.extract_uniclass_codes(out_str)
        expected_code = str(ga.get("uniclass_code", "")).strip().upper()
        code_score = self._score_uniclass_code(out_str, extracted_codes, expected_code)
        layer_score = self._score_iso_12006_layer(
            out_str, str(ga.get("iso_12006_layer", "")).strip()
        )
        naming_score = self._score_naming_convention(
            out_str, ga.get("iso_19650_naming") or ga.get("ifc_alignment_naming")
        )

        final_score = 0.4 * code_score + 0.3 * layer_score + 0.3 * naming_score
        reasoning = (
            f"BIM Validation: Code score={code_score:.2f}, "
            f"ISO 12006-2 layer score={layer_score:.2f}, "
            f"Naming syntax score={naming_score:.2f}"
        )
        return ScoreResult(
            scorer_name=self.name,
            score=final_score,
            raw_output={
                "extracted_codes": extracted_codes,
                "expected_code": expected_code,
                "code_score": code_score,
                "layer_score": layer_score,
                "naming_score": naming_score,
            },
            reasoning=reasoning,
            is_critical_fail=False,
        )


def get_bim_classification_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BIM, Uniclass 200, and ISO 12006-2 classification skills."""
    p_bim = get_scorer_params(
        "bim_classification",
        "bim_classification",
        override_config,
        default_weight=0.5,
        default_is_critical=True,
    )
    p_pd = get_scorer_params(
        "bim_classification", "progressive_disclosure", override_config, default_weight=0.2
    )
    p_deb = get_scorer_params(
        "bim_classification", "anti_debris", override_config, default_weight=0.15
    )
    p_len = get_scorer_params(
        "bim_classification",
        "depth",
        override_config,
        default_weight=0.15,
        default_min_length=20,
        default_max_length=25000,
    )
    return [
        BimClassificationScorer(weight=p_bim["weight"], is_critical=p_bim["is_critical"]),
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


def get_bigbim_risk_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM risk and information conflict detection."""
    return _build_quad_regex_scorers(
        "bigbim_risk",
        [
            (
                "risk_conflict_audit",
                r"(mâu thuẫn thông tin|information conflict|V2 - Coordination|khoảng cách|clearance|không gian bảo trì|không gian thao tác|va chạm)",
                0.35,
                False,
            ),
            (
                "risk_anti_trap_hard_floor",
                r"(900mm|150mm|Level 2|BBP|Unique ID|tủ điện|khoảng hở|hành lang|van ngăn cháy|Chủ trì)",
                0.35,
                True,
            ),
            (
                "risk_mitigation_guard",
                r"(proposed_mitigation|INF-CON-|giải pháp|dịch chuyển|cao độ|IFC4X3|IfcDistributionFlowElement|ccba-issue-tree|Why-Tree|How-Tree)",
                0.20,
                False,
            ),
        ],
        override_config,
    )


def get_bigbim_governance_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM governance and golden thread audit."""
    return _build_quad_regex_scorers(
        "bigbim_governance",
        [
            (
                "governance_thread_audit",
                r"(Sợi Chỉ Vàng|Sợi Chỉ Đỏ|golden thread|red thread|PM_80|75 năm|Đoạn Đò-3|LMS vendor lock-in|governance)",
                0.35,
                False,
            ),
            (
                "governance_anti_trap_hard_floor",
                r"(ST2|ISO\s*19650-5|BBP-A0|Unique\s*ID|3\s*chiều|đối soát|biển hiệu thực tế)",
                0.35,
                True,
            ),
            (
                "governance_risk_matrix_guard",
                r"(RK_50_40_35|RK_10_70_04|RK_50_40_45|RK_50_60_28|No-Risk|Time-Risk|Do-Risk|Use-Risk)",
                0.20,
                False,
            ),
        ],
        override_config,
    )


def get_bigbim_rase_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM RASE decomposition and IFC4X3 property mapping."""
    return _build_quad_regex_scorers(
        "bigbim_rase",
        [
            (
                "rase_decomposition_audit",
                r"(Requirement|Applicability|Selection|Exception|R-A-S-E|RASE|Bóc tách RASE)",
                0.35,
                False,
            ),
            (
                "rase_ifc4x3_pmapping_hard_floor",
                r"(IfcRelDefinesByProperties|IfcPropertySet|Pset_|IFC4X3|ISO 16739)",
                0.35,
                True,
            ),
            (
                "rase_qto_mapping_guard",
                r"(Qto_|Quantity\s*Take-Off|BaseQuantities|GrossVolume|Qto_SpaceBaseQuantities|Qto_WallBaseQuantities|Qto_SlabBaseQuantities)",
                0.20,
                False,
            ),
        ],
        override_config,
    )
