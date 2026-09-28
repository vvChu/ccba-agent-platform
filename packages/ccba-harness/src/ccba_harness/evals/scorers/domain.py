"""scorers/domain.py - Domain-specific scorers and factory functions for CCBA skill archetypes."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from ..legal_index import LegalFlatIndex, StatutoryDocument, load_legal_flat_index
from ..models import EvalItem, ScoreResult
from ..uniclass_index import UniclassFlatIndex, load_uniclass_flat_index
from .base import BaseScorer, get_scorer_params
from .rule_based import LengthBoundsScorer, RegexScorer


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


class ProgressiveDisclosureScorer(BaseScorer):
    """Validates Markdown link integrity and Level 1/2/3 Progressive Disclosure architecture."""

    def __init__(
        self,
        name: str = "progressive_disclosure_links",
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self.disclosure_pattern = re.compile(
            r"(progressive disclosure|bộc lộ dần|references/|tham chiếu|level [123]|pha [123]|chỉ mục)",
            re.IGNORECASE,
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        has_links = bool(self.link_pattern.search(out_str))
        has_disclosure = bool(self.disclosure_pattern.search(out_str))
        valid = has_links or has_disclosure
        score = 1.0 if valid else 0.0
        is_crit_fail = self.is_critical and not valid

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"has_links": has_links, "has_disclosure": has_disclosure},
            reasoning=(
                "Progressive disclosure structure or valid markdown links detected"
                if valid
                else "Missing progressive disclosure cues or valid markdown reference links"
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


class AntiDebrisScorer(BaseScorer):
    """Validates that skill outputs do not contain dead wood, junk HTML comments, or template debris."""

    def __init__(
        self,
        name: str = "anti_debris",
        weight: float = 0.3,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.debris_patterns: list[tuple[re.Pattern[str], str]] = [
            (
                re.compile(r"<!--\s*Ratchet Optimization Refinement", re.IGNORECASE),
                "Ratchet optimization junk comment",
            ),
            (
                re.compile(r"<!--\s*(TODO|FIXME|TEMP|TEST)\b", re.IGNORECASE),
                "Temporary debris comment",
            ),
            (
                re.compile(
                    r"(/ck:[a-zA-Z0-9_\-]+|/ultrathink\b|<tasks\b|TaskCreate|AskUserQuestion)"
                ),
                "ClaudeKit dead wood remnant",
            ),
        ]

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        detected: list[str] = []
        for pattern, label in self.debris_patterns:
            if pattern.search(out_str):
                detected.append(label)

        clean = len(detected) == 0
        score = 1.0 if clean else 0.0
        is_crit_fail = self.is_critical and not clean

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output={"clean": clean, "detected": detected},
            reasoning=(
                "Output is clean of debris and junk comments"
                if clean
                else f"Debris detected in output: {', '.join(detected)}"
            ),
            is_critical_fail=is_crit_fail,
        )


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


class LegalVerbatimProvenanceScorer(BaseScorer):
    """Evaluates legal verbatim provenance, gazette citations, and anti-trap constraints (ADR-0059).

    Enforces the Zero-Hallucination & Anti-Trap Critical Hard Floor:
    1. Output must cite valid statutory documents (Decrees, Laws, Circulars, QCVN, TCVN).
    2. Citing expired/superseded documents (e.g. NĐ 136/2020, Luật 50/2014, QCVN 06:2020) without
       acknowledging replacement results in score=0.0 with is_critical_fail=True.
    3. Citing fabricated/non-existent statutory documents results in score=0.0 with is_critical_fail=True.
    4. Citing non-existent clauses (Điều, Khoản, Mục, Bảng, Phụ lục) in a document results in
       score=0.0 with is_critical_fail=True.
    5. Records cryptographic SHA-256 provenance and official gazette numbers in metadata.
    """

    def __init__(
        self,
        name: str = "legal_verbatim_provenance",
        weight: float = 0.5,
        is_critical: bool = True,
        require_citation: bool = True,
        index: LegalFlatIndex | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.require_citation = require_citation
        self._index = index

        self.doc_patterns: list[re.Pattern[str]] = [
            re.compile(
                r"(?:Nghị\s*định|NĐ)\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/[A-ZĐa-z0-9\-]+)?)",
                re.IGNORECASE,
            ),
            re.compile(
                r"Luật(?:\s+[A-Za-zÀ-ỹ\s]+)?\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/QH[0-9]+)?)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:Thông\s*tư|TT)\s+(?:số\s+)?([0-9]+/[0-9]{4}(?:/[A-Z0-9\-]+)?)",
                re.IGNORECASE,
            ),
            re.compile(r"(QCVN\s+[0-9]+(?::[0-9]{4})?(?:/[A-Z0-9\-]+)?)", re.IGNORECASE),
            re.compile(r"(TCVN\s+[0-9]+(?::[0-9]{4})?(?:/[A-Z0-9\-]+)?)", re.IGNORECASE),
            re.compile(
                r"\b([0-9]+/[0-9]{4}/(?:NĐ-CP|ND-CP|QH[0-9]+|TT-[A-Z0-9]+|QĐ-[A-Z0-9]+))\b",
                re.IGNORECASE,
            ),
        ]

        self.clause_doc_patterns: list[tuple[re.Pattern[str], int, int]] = [
            (
                re.compile(
                    r"((?:Khoản\s+\d+\s+)?Điều\s+\d+|Mục\s+[0-9\.]+|Bảng\s+[A-Za-z0-9\.]+|Phụ\s+lục\s+[A-Za-z0-9\.]+)\s*(?:của|tại|theo)?\s*[^,\.\n]{0,30}?(?:Nghị\s*định|NĐ|Luật|Thông\s*tư|TT|QCVN|TCVN)\s+(?:số\s+)?([A-Za-z0-9_:\/\-Đđ]+)",
                    re.IGNORECASE,
                ),
                1,
                2,
            ),
            (
                re.compile(
                    r"(?:Nghị\s*định|NĐ|Luật|Thông\s*tư|TT|QCVN|TCVN)\s+(?:số\s+)?([A-Za-z0-9_:\/\-Đđ]+)[^,\.\n]{0,30}?(?:tại|theo|khoản|điều|mục|bảng|phụ\s+lục)?\s*((?:Khoản\s+\d+\s+)?Điều\s+\d+|Mục\s+[0-9\.]+|Bảng\s+[A-Za-z0-9\.]+|Phụ\s+lục\s+[A-Za-z0-9\.]+)",
                    re.IGNORECASE,
                ),
                2,
                1,
            ),
        ]

        self.replacement_indicators: tuple[str, ...] = (
            "thay thế",
            "hết hiệu lực",
            "bãi bỏ",
            "hết hạn",
            "bị thay",
            "superseded",
            "expired",
            "thay bằng",
        )

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        if not out_str.strip():
            if self.require_citation:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    reasoning="Văn bản phản hồi rỗng, không phát hiện trích dẫn căn cứ pháp lý",
                    is_critical_fail=self.is_critical,
                )
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                reasoning="Empty output allowed without citations",
                is_critical_fail=False,
            )

        index = self._index or load_legal_flat_index()
        out_lower = out_str.lower()

        # 1. Extract candidate document references
        detected_doc_refs: list[str] = []
        for pat in self.doc_patterns:
            for m in pat.finditer(out_str):
                ref = m.group(1).strip(".,;:() ") if m.groups() else m.group(0).strip(".,;:() ")
                if ref and ref not in detected_doc_refs:
                    detected_doc_refs.append(ref)

        # Also check known documents & replacements mentioned by string in text
        for doc_num in list(index.documents.keys()) + list(index.replaces_map.keys()):
            if doc_num.lower() in out_lower and doc_num not in detected_doc_refs:
                detected_doc_refs.append(doc_num)

        # 2. Extract clause-document pairs
        extracted_pairs: list[tuple[str, str]] = []
        for pat, clause_grp, doc_grp in self.clause_doc_patterns:
            for m in pat.finditer(out_str):
                clause = m.group(clause_grp).strip(".,;:() ")
                dref = m.group(doc_grp).strip(".,;:() ")
                if clause and dref:
                    extracted_pairs.append((clause, dref))

        # 3. Check zero citations
        if not detected_doc_refs:
            if self.require_citation:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"citations_found": 0},
                    reasoning=(
                        "Không phát hiện trích dẫn văn bản quy phạm pháp luật nào "
                        "(Luật, Nghị định, Thông tư, QCVN, TCVN) theo quy chuẩn ADR-0059"
                    ),
                    is_critical_fail=self.is_critical,
                )
            return ScoreResult(
                scorer_name=self.name,
                score=1.0,
                reasoning="No citations required",
                is_critical_fail=False,
            )

        # 4. Verify each detected document reference
        verified_docs: list[StatutoryDocument] = []
        seen_doc_numbers: set[str] = set()

        for doc_ref in detected_doc_refs:
            is_exp, replacement = index.is_expired_or_replaced(doc_ref)
            if is_exp:
                # Must acknowledge expiration or replacement
                has_indicator = any(kw in out_lower for kw in self.replacement_indicators)
                has_rep_cited = False
                if replacement:
                    rep_short = replacement.split("/")[0].lower()
                    has_rep_cited = rep_short in out_lower or replacement.lower() in out_lower
                else:
                    has_rep_cited = True

                if not (has_indicator and has_rep_cited):
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"trap_doc": doc_ref, "replacement": replacement},
                        reasoning=(
                            f"Bẫy pháp lý (Anti-Trap Hard Floor): Trích dẫn văn bản đã hết hiệu lực/bị thay thế '{doc_ref}' "
                            f"mà không nêu rõ đã được thay thế bởi '{replacement}'"
                        ),
                        is_critical_fail=True,
                    )
                # Properly acknowledged expired trap, continue
                continue

            doc = index.get_document(doc_ref)
            if doc is None:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"unknown_doc": doc_ref},
                    reasoning=(
                        f"Bịa đặt căn cứ pháp lý (Zero-Hallucination Hard Floor): "
                        f"Văn bản '{doc_ref}' không tồn tại trong công báo hoặc chỉ mục pháp luật"
                    ),
                    is_critical_fail=True,
                )

            if doc.document_number not in seen_doc_numbers:
                verified_docs.append(doc)
                seen_doc_numbers.add(doc.document_number)

        # 5. Verify clauses
        doc_clause_map: dict[str, list[str]] = {}
        for clause, dref in extracted_pairs:
            matched_doc = index.get_document(dref)
            if matched_doc:
                doc_clause_map.setdefault(matched_doc.document_number, []).append(clause)

        for doc_num, clauses in doc_clause_map.items():
            target_doc = index.documents.get(doc_num)
            if not target_doc:
                continue
            for cl in clauses:
                if not target_doc.has_clause(cl):
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"doc": doc_num, "fake_clause": cl},
                        reasoning=(
                            f"Bịa đặt điều khoản (Zero-Hallucination Hard Floor): "
                            f"Điều/Khoản '{cl}' không tồn tại trong văn bản '{target_doc.document_number}'"
                        ),
                        is_critical_fail=True,
                    )

        # 6. Verify target law match if specified in test item metadata
        target_law = item.metadata.get("target_law") or item.metadata.get("law")
        if target_law:
            target_nums = re.findall(
                r"\b([0-9]+/[0-9]{4}|QCVN\s+[0-9]+(?::[0-9]{4})?|TCVN\s+[0-9]+(?::[0-9]{4})?)\\b",
                str(target_law),
                re.IGNORECASE,
            )
            if target_nums and not any(num.lower() in out_lower for num in target_nums):
                target_matched = False
                for num in target_nums:
                    is_exp, rep = index.is_expired_or_replaced(num)
                    if rep and rep.lower() in out_lower:
                        target_matched = True
                        break
                if not target_matched:
                    return ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"target_law": target_law},
                        reasoning=f"Không viện dẫn đúng văn bản mục tiêu '{target_law}' theo yêu cầu nghiệp vụ",
                        is_critical_fail=True,
                    )

        provenance_records = [
            {
                "document_number": d.document_number,
                "title": d.title,
                "cong_bao_number": d.cong_bao_number,
                "pdf_sha256": d.pdf_sha256,
                "verified_clauses": doc_clause_map.get(d.document_number, []),
            }
            for d in verified_docs
        ]

        return ScoreResult(
            scorer_name=self.name,
            score=1.0,
            raw_output={
                "verified_documents": [d.document_number for d in verified_docs],
                "provenance": provenance_records,
            },
            reasoning=(
                f"Xác thực căn cứ pháp lý thành công: {len(verified_docs)} văn bản hợp lệ "
                f"(SHA-256 đối soát công báo)"
            ),
            is_critical_fail=False,
            metadata={"provenance": provenance_records},
        )


def get_legal_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for legal domain skills (ADR-0059)."""
    p_leg = get_scorer_params(
        "legal",
        "legal_verbatim_provenance",
        {"weight": 0.50, "is_critical": True},
        override_config,
    )
    p_pd = get_scorer_params(
        "legal",
        "progressive_disclosure",
        {"weight": 0.20, "is_critical": False},
        override_config,
    )
    p_deb = get_scorer_params(
        "legal",
        "anti_debris",
        {"weight": 0.15, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "legal",
        "depth",
        {"weight": 0.15, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        LegalVerbatimProvenanceScorer(weight=p_leg["weight"], is_critical=p_leg["is_critical"]),
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


class LegalToolingIntegrityScorer(BaseScorer):
    """Evaluates Statutory Engineering pipelines: TVPL VIP crawler, OKF v2.4, VBHN diffing, and HSHT completion dossiers."""

    def __init__(
        self,
        name: str = "legal_tooling_integrity",
        weight: float = 0.45,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(tvpl|thư viện pháp luật|vip|session|cookie|captcha|exponential backoff|retry|rate limit|429|"
            r"okf v2\.4|okf|frontmatter|verbatim|nguyên văn|sha-256|sha256|mã băm|băm mật mã|provenance|"
            r"vbhn|văn bản hợp nhất|diff|so khớp|sửa đổi|bổ sung|bãi bỏ|thay thế|amendment|"
            r"hồ sơ hoàn thành|hsht|nghiệm thu|nghị định 06/2021|nđ 06/2021|nghị định 35/2023|bản vẽ hoàn công|cây thư mục|checklist|"
            r"adr-0059|mandatory acquisition|anti-synthetic|thu thập bắt buộc)",
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
                "Legal tooling pipeline standard verified (TVPL VIP session, OKF v2.4, SHA-256, VBHN diff, HSHT checklist, ADR-0059)"
                if matched
                else "Missing statutory engineering standards (TVPL crawler, OKF v2.4, SHA-256 provenance, VBHN diff, or HSHT checklist)"
            ),
            is_critical_fail=is_crit_fail,
        )


class Sha256ProvenanceScorer(BaseScorer):
    """Evaluates cryptographic SHA-256 provenance stamping and verbatim grounding per ADR-0059."""

    def __init__(
        self,
        name: str = "sha256_provenance",
        weight: float = 0.25,
        is_critical: bool = True,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(sha-256|sha256|[a-f0-9]{64}|mã băm|cryptographic|provenance|verbatim|adr-0059)",
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
                "Cryptographic SHA-256 provenance / verbatim grounding verified (ADR-0059)"
                if matched
                else "Missing cryptographic SHA-256 provenance stamping or verbatim grounding (ADR-0059)"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_legal_tooling_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for legal tooling and statutory engineering skills."""
    p_tool = get_scorer_params(
        "legal_tooling",
        "legal_tooling_integrity",
        {"weight": 0.45, "is_critical": False},
        override_config,
    )
    p_sha = get_scorer_params(
        "legal_tooling",
        "sha256_provenance",
        {"weight": 0.25, "is_critical": True},
        override_config,
    )
    p_pd = get_scorer_params(
        "legal_tooling",
        "progressive_disclosure",
        {"weight": 0.15, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "legal_tooling",
        "depth",
        {"weight": 0.15, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        LegalToolingIntegrityScorer(weight=p_tool["weight"], is_critical=p_tool["is_critical"]),
        Sha256ProvenanceScorer(weight=p_sha["weight"], is_critical=p_sha["is_critical"]),
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


class PlatformToolingIntegrityScorer(BaseScorer):
    """Evaluates developer utilities and platform maintenance protocols (Git CLI, Hub-Spoke sync, Connectors, ADR-0058)."""

    def __init__(
        self,
        name: str = "platform_tooling_integrity",
        weight: float = 0.45,
        is_critical: bool = False,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(gh pr create|pull request|branch naming|feat/issue-|git checkout|"
            r"git cleanliness|check_spoke_cleanliness|maskara|redact|secrets?|credentials?|"
            r"spoke|hub|sync_spoke|non-destructive|constitution|virtual hub fallback|"
            r"multimodal|connector|youtube|notebooklm|transcript|circuit-?breaker|rate limit|soft cooldown|auto-?downgrade|exponential backoff|jitter|"
            r"adr-0058|hard completion lock|verify-patch|seam catalog|compile_catalog)",
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
                "Platform tooling integrity standard verified (Git lifecycle, Maskara cleanliness, Spoke-Hub sync, Connectors, ADR-0058 lock)"
                if matched
                else "Missing platform tooling standards (Git CLI, cleanliness, Spoke sync, connector protocol, or ADR-0058 verification)"
            ),
            is_critical_fail=is_crit_fail,
        )


class ExecutionGuardrailScorer(BaseScorer):
    """Evaluates safety invariants, idempotency, lease push, and ADR-0058 Hard Completion Lock."""

    def __init__(
        self,
        name: str = "execution_guardrail",
        weight: float = 0.25,
        is_critical: bool = True,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.pattern = re.compile(
            r"(--force-with-lease|idempotent|idempotency|trạng thái remote|remote state|"
            r"ccba_hub_path|# ccba:allow-machine-path|maskara|"
            r"verify-patch|exit code 0|hard completion lock|adr-0058|reactive wakeup|manage_task)",
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
                "Execution guardrails & safety invariants verified (--force-with-lease, idempotency, path isolation, ADR-0058 lock)"
                if matched
                else "Violated or missing execution guardrails (--force-with-lease, remote state idempotency, CCBA_HUB_PATH, or ADR-0058 lock)"
            ),
            is_critical_fail=is_crit_fail,
        )


def get_platform_tooling_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for platform tooling and developer utility skills."""
    p_plat = get_scorer_params(
        "platform_tooling",
        "platform_tooling_integrity",
        {"weight": 0.45, "is_critical": False},
        override_config,
    )
    p_guard = get_scorer_params(
        "platform_tooling",
        "execution_guardrail",
        {"weight": 0.25, "is_critical": True},
        override_config,
    )
    p_pd = get_scorer_params(
        "platform_tooling",
        "progressive_disclosure",
        {"weight": 0.15, "is_critical": False},
        override_config,
    )
    p_len = get_scorer_params(
        "platform_tooling",
        "depth",
        {"weight": 0.15, "min_length": 20, "max_length": 25000, "is_critical": False},
        override_config,
    )
    return [
        PlatformToolingIntegrityScorer(weight=p_plat["weight"], is_critical=p_plat["is_critical"]),
        ExecutionGuardrailScorer(weight=p_guard["weight"], is_critical=p_guard["is_critical"]),
        ProgressiveDisclosureScorer(weight=p_pd["weight"], is_critical=p_pd["is_critical"]),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
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


class PcccParametricScorer(BaseScorer):
    """Evaluates Fire Protection (PCCC) & Technical QC parametric audit compliance (QCVN 06:2022/BXD).

    Uses a Decoupled Pluggable Two-Tier Architecture:
    - Gate 1 (Deterministic Schema Filter - Primary Default): Validates expected verdict,
      required engineering parameters, forbidden anti-trap misconceptions, and statutory basis
      against item.metadata["parametric_rules"]. Enforces Dual Critical Hard Floor:
        1. Safety-critical reversal (e.g. approving a non-compliant design) -> 0.0 critical fail.
        2. Prohibited anti-trap patterns (e.g. accepting 30m corridor without smoke exhaust) -> 0.0 critical fail.
      Runs in < 1ms on RAM, consumes 0 LLM tokens, ensuring 100% ADR-0058 deterministic verification.
    - Gate 2 (Escalation LLM Judge - Advisory Plugin): Optional plugin called when Gate 1 score is in
      the deadband [0.40, 0.85] to evaluate semantic synonyms, with graceful fallback to Gate 1 score
      upon network or timeout exceptions (never blocking CI or nightly ratchets).
    """

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

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        rules = meta.get("parametric_rules")

        # Fallback to standard regex if parametric_rules not defined (Backward compatibility)
        if not isinstance(rules, dict):
            matched = bool(self.default_pccc_pattern.search(out_str))
            score = 1.0 if matched else 0.0
            is_crit_fail = self.is_critical and not matched
            return ScoreResult(
                scorer_name=self.name,
                score=score,
                raw_output={"mode": "fallback_regex", "matched": matched},
                reasoning="Standard PCCC terminology detected"
                if matched
                else "Missing basic PCCC terminology",
                is_critical_fail=is_crit_fail,
            )

        # Gate 1: Deterministic Schema Filter
        # 1. Check forbidden verdict patterns (Dual Critical hard floor #1)
        forbidden_verdicts = rules.get("forbidden_verdict_patterns", [])
        for p in forbidden_verdicts:
            if re.search(p, out_str, re.IGNORECASE):
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"gate": 1, "violation": "forbidden_verdict", "matched_pattern": p},
                    reasoning=f"Critical safety failure: Model approved a non-compliant PCCC design ({p})",
                    is_critical_fail=True,
                )

        # 2. Check forbidden parameter anti-traps (Dual Critical hard floor #2)
        forbidden_params = rules.get("forbidden_parameters", [])
        for fp in forbidden_params:
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

        # 3. Check expected verdict
        verdict_patterns = rules.get("verdict_patterns", [])
        exp = rules.get("expected_verdict", "")
        verdict_matched = False
        if verdict_patterns:
            verdict_matched = any(re.search(p, out_str, re.IGNORECASE) for p in verdict_patterns)
            if not verdict_matched and exp:
                verdict_matched = bool(re.search(re.escape(exp), out_str, re.IGNORECASE))
        elif exp:
            verdict_matched = bool(re.search(re.escape(exp), out_str, re.IGNORECASE))
        else:
            verdict_matched = True

        if not verdict_matched:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output={"gate": 1, "violation": "missing_expected_verdict"},
                reasoning="Verdict incorrect: Model failed to state the required PCCC audit conclusion",
                is_critical_fail=self.is_critical,
            )

        # 4. Check required parameters
        req_params = rules.get("required_parameters", [])
        matched_params_count = 0
        total_params_count = len(req_params)
        missing_params = []
        for rp in req_params:
            pat = rp.get("pattern", "") if isinstance(rp, dict) else str(rp)
            name = rp.get("name", pat) if isinstance(rp, dict) else pat
            if pat and re.search(pat, out_str, re.IGNORECASE):
                matched_params_count += 1
            else:
                missing_params.append(name)

        param_score = (matched_params_count / total_params_count) if total_params_count > 0 else 1.0

        # 5. Check legal basis
        legal_basis_pat = rules.get("legal_basis", "")
        legal_basis_matched = True
        if legal_basis_pat:
            legal_basis_matched = bool(re.search(legal_basis_pat, out_str, re.IGNORECASE))

        legal_score = 1.0 if legal_basis_matched else 0.5

        # Weighted Gate 1 score: Verdict (0.4) + Parameters (0.4) + Legal Basis (0.2)
        gate1_score = 0.4 * 1.0 + 0.4 * param_score + 0.2 * legal_score

        final_score = gate1_score
        reasoning = f"Gate 1: Verdict verified; {matched_params_count}/{total_params_count} parameters verified"
        if missing_params:
            reasoning += f" (missing: {', '.join(str(p) for p in missing_params)})"

        # Gate 2: Escalation LLM Judge (Advisory Plugin)
        if (
            self.enable_llm_judge
            and self.escalation_judge is not None
            and 0.40 <= gate1_score <= 0.85
        ):
            try:
                if asyncio.iscoroutinefunction(self.escalation_judge):
                    judge_res = await self.escalation_judge(out_str, item, rules)
                else:
                    judge_res = self.escalation_judge(out_str, item, rules)
                if isinstance(judge_res, (int, float)):
                    final_score = float(judge_res)
                    reasoning += f"; Gate 2 LLM Judge adjudicated: {final_score:.2f}"
            except Exception as e:
                reasoning += f"; Gate 2 LLM Judge fallback triggered ({e})"

        return ScoreResult(
            scorer_name=self.name,
            score=final_score,
            raw_output={
                "gate": 1,
                "gate1_score": gate1_score,
                "verdict_matched": verdict_matched,
                "matched_params": matched_params_count,
                "total_params": total_params_count,
                "missing_params": missing_params,
                "legal_basis_matched": legal_basis_matched,
            },
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
    """BIM Classification & Uniclass 200 / ISO 12006-2 Validator (TICKET-005).

    Evaluates:
    - Dimension 1: Uniclass Code & Table Validity (Weight 0.4, Critical Hard Floor on anti-trap violations).
      Checks whether candidate Uniclass codes (e.g. EF_20_10_15, SL_25_10_72, Ss_60_40_36, Pr_60_65_62)
      are present in output and match expected code or table from golden_answer / metadata.
      Enforces Anti-Trap Hard Floor: If output triggers a prohibited anti-trap misconception (e.g. confusing
      BIM object Result EF_25_30 with BOQ Procurement Resource Pr_30_59_24) -> 0.0 critical failure.
    - Dimension 2: ISO 12006-2 Classification Layer (Weight 0.3).
      Verifies model correctly distinguishes Results (Complexes, Entities, Spaces, Elements, Systems)
      from Resources (Products/Materials) or Processes (Project Management).
    - Dimension 3: Container Naming Convention & Standards Compliance (Weight 0.3).
      Checks ISO 19650 Room Naming syntax ([Project]-[Building]-[Floor]-[Uniclass]-[Seq]) or
      IFC Alignment linear naming syntax ([Route]-[KM]-[Element]-[Uniclass]), and mentions of ISO 22274/12006-2.
    """

    def __init__(
        self,
        name: str = "bim_classification",
        weight: float = 0.5,
        is_critical: bool = True,
        index: UniclassFlatIndex | None = None,
    ) -> None:
        super().__init__(name=name, weight=weight, is_critical=is_critical)
        self.index = index or load_uniclass_flat_index()

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        ga = item.golden_answer if isinstance(item.golden_answer, dict) else {}

        # 1. Anti-Trap Hard Floor (Dual Critical Hard Floor)
        has_trap, trap_reason = self.index.check_anti_traps(out_str)
        if has_trap:
            return ScoreResult(
                scorer_name=self.name,
                score=0.0,
                raw_output={"violation": "anti_trap", "reason": trap_reason},
                reasoning=f"Critical Hard Floor Failure: {trap_reason}",
                is_critical_fail=True,
            )

        # 2. Extract Candidate Uniclass codes from output
        extracted_codes = self.index.extract_uniclass_codes(out_str)
        expected_code = str(ga.get("uniclass_code", "")).strip().upper()

        # Dimension 1: Uniclass Code & Table Validity (0.4)
        code_score = 0.0
        if expected_code:
            if expected_code in extracted_codes:
                code_score = 1.0
            elif any(c.startswith(expected_code[:5]) for c in extracted_codes):
                code_score = 0.7  # Matching table and branch prefix
            elif any(c.split("_")[0] == expected_code.split("_")[0] for c in extracted_codes):
                code_score = 0.5  # Matching table prefix
            else:
                code_score = 0.0
        elif extracted_codes:
            # Check if extracted codes are valid in index
            valid_count = sum(1 for c in extracted_codes if self.index.is_valid_code(c))
            code_score = 1.0 if valid_count > 0 else 0.5
        else:
            # Fallback if no specific code expected but mentions Uniclass
            if re.search(
                r"\b(Uniclass|ISO\s*12006|EF_|SL_|Ss_|Pr_|En_|Co_|PM_)\b", out_str, re.IGNORECASE
            ):
                code_score = 0.5
            else:
                code_score = 0.0

        # Dimension 2: ISO 12006-2 Layer Classification (0.3)
        expected_layer = str(ga.get("iso_12006_layer", "")).strip()
        layer_score = 0.0
        if expected_layer:
            layer_kw = expected_layer.split()[0].lower()  # 'result', 'resource', 'process'
            if re.search(rf"\b{re.escape(layer_kw)}\b", out_str, re.IGNORECASE):
                layer_score = 1.0
            elif "iso 12006" in out_str.lower() or "iso 22274" in out_str.lower():
                layer_score = 0.6
            else:
                layer_score = 0.3
        else:
            if re.search(
                r"(ISO\s*12006|Result|Resource|Process|Property|kết quả|nguồn lực|quy trình)",
                out_str,
                re.IGNORECASE,
            ):
                layer_score = 1.0
            else:
                layer_score = 0.5

        # Dimension 3: Container Naming Convention & Standards Compliance (0.3)
        expected_naming = ga.get("iso_19650_naming") or ga.get("ifc_alignment_naming")
        naming_score = 0.0
        if expected_naming:
            expected_naming_str = str(expected_naming).strip()
            if expected_naming_str in out_str:
                naming_score = 1.0
            elif self.index.validate_iso_19650_naming(expected_naming_str) and any(
                self.index.validate_iso_19650_naming(line.strip()) for line in out_str.splitlines()
            ):
                naming_score = 0.8
            elif self.index.validate_ifc_alignment_naming(expected_naming_str) and any(
                self.index.validate_ifc_alignment_naming(line.strip())
                for line in out_str.splitlines()
            ):
                naming_score = 0.8
            elif re.search(
                r"ISO\s*19650|IFC\s*Alignment|Container|đặt tên", out_str, re.IGNORECASE
            ):
                naming_score = 0.5
            else:
                naming_score = 0.2
        else:
            if any(
                self.index.validate_iso_19650_naming(line.strip()) for line in out_str.splitlines()
            ) or any(
                self.index.validate_ifc_alignment_naming(line.strip())
                for line in out_str.splitlines()
            ):
                naming_score = 1.0
            elif re.search(
                r"(ISO\s*19650|IFC\s*Alignment|ISO\s*22274|ISO\s*21511|Digital Memory|Trí Nhớ Số)",
                out_str,
                re.IGNORECASE,
            ):
                naming_score = 0.8
            else:
                naming_score = 0.4

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


def get_bigbim_risk_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM risk and information conflict detection."""
    p_conf = get_scorer_params(
        "bigbim_risk", "risk_conflict_audit", override_config, default_weight=0.35
    )
    p_trap = get_scorer_params(
        "bigbim_risk",
        "risk_anti_trap_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_mit = get_scorer_params(
        "bigbim_risk", "risk_mitigation_guard", override_config, default_weight=0.2
    )
    p_len = get_scorer_params(
        "bigbim_risk",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="risk_conflict_audit",
            pattern=r"(mâu thuẫn thông tin|information conflict|V2 - Coordination|khoảng cách|clearance|không gian bảo trì|không gian thao tác|va chạm)",
            weight=p_conf["weight"],
            is_critical=p_conf["is_critical"],
        ),
        RegexScorer(
            name="risk_anti_trap_hard_floor",
            pattern=r"(900mm|150mm|Level 2|BBP|Unique ID|tủ điện|khoảng hở|hành lang|van ngăn cháy|Chủ trì)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="risk_mitigation_guard",
            pattern=r"(proposed_mitigation|INF-CON-|giải pháp|dịch chuyển|cao độ|IFC4X3|IfcDistributionFlowElement|ccba-issue-tree|Why-Tree|How-Tree)",
            weight=p_mit["weight"],
            is_critical=p_mit["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_bigbim_governance_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM governance and golden thread audit."""
    p_thr = get_scorer_params(
        "bigbim_governance", "governance_thread_audit", override_config, default_weight=0.35
    )
    p_trap = get_scorer_params(
        "bigbim_governance",
        "governance_anti_trap_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_rm = get_scorer_params(
        "bigbim_governance", "governance_risk_matrix_guard", override_config, default_weight=0.2
    )
    p_len = get_scorer_params(
        "bigbim_governance",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="governance_thread_audit",
            pattern=r"(Sợi Chỉ Vàng|Sợi Chỉ Đỏ|golden thread|red thread|PM_80|75 năm|Đoạn Đò-3|LMS vendor lock-in|governance)",
            weight=p_thr["weight"],
            is_critical=p_thr["is_critical"],
        ),
        RegexScorer(
            name="governance_anti_trap_hard_floor",
            pattern=r"(ST2|ISO\s*19650-5|BBP-A0|Unique\s*ID|3\s*chiều|đối soát|biển hiệu thực tế)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="governance_risk_matrix_guard",
            pattern=r"(RK_50_40_35|RK_10_70_04|RK_50_40_45|RK_50_60_28|No-Risk|Time-Risk|Do-Risk|Use-Risk)",
            weight=p_rm["weight"],
            is_critical=p_rm["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_bigbim_rase_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for BigBIM RASE decomposition and IFC4X3 property mapping."""
    p_dec = get_scorer_params(
        "bigbim_rase", "rase_decomposition_audit", override_config, default_weight=0.35
    )
    p_trap = get_scorer_params(
        "bigbim_rase",
        "rase_ifc4x3_pmapping_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_qto = get_scorer_params(
        "bigbim_rase", "rase_qto_mapping_guard", override_config, default_weight=0.2
    )
    p_len = get_scorer_params(
        "bigbim_rase",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="rase_decomposition_audit",
            pattern=r"(Requirement|Applicability|Selection|Exception|R-A-S-E|RASE|Bóc tách RASE)",
            weight=p_dec["weight"],
            is_critical=p_dec["is_critical"],
        ),
        RegexScorer(
            name="rase_ifc4x3_pmapping_hard_floor",
            pattern=r"(IfcRelDefinesByProperties|IfcPropertySet|Pset_|IFC4X3|ISO 16739)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="rase_qto_mapping_guard",
            pattern=r"(Qto_|Quantity\s*Take-Off|BaseQuantities|GrossVolume|Qto_SpaceBaseQuantities|Qto_WallBaseQuantities|Qto_SlabBaseQuantities)",
            weight=p_qto["weight"],
            is_critical=p_qto["is_critical"],
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
    p_one = get_scorer_params(
        "grilling",
        "grilling_one_by_one_and_recommendation",
        override_config,
        default_weight=0.35,
    )
    p_trap = get_scorer_params(
        "grilling",
        "grilling_anti_trap_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_esc = get_scorer_params(
        "grilling", "grilling_escalation_guard", override_config, default_weight=0.2
    )
    p_len = get_scorer_params(
        "grilling",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="grilling_one_by_one_and_recommendation",
            pattern=r"(câu hỏi|one-by-one|đề xuất|phương án|recommended|stress-test|chất vấn|front-end|picker)",
            weight=p_one["weight"],
            is_critical=p_one["is_critical"],
        ),
        RegexScorer(
            name="grilling_anti_trap_hard_floor",
            pattern=r"(từng câu|đề xuất trước|facts vs decisions|tra cứu|tự tra cứu|codebase|NOTES\.md|ccba-issue-tree|vi phạm|bất biến)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="grilling_escalation_guard",
            pattern=r"(ccba-issue-tree|How-Tree|Why-Tree|Solution How-Tree|ma trận|Giá trị|Độ phức tạp|Rủi ro|KISS|Frontier|prerequisites)",
            weight=p_esc["weight"],
            is_critical=p_esc["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_adr_lifecycle_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for Architecture Decision Record (ADR) lifecycle governance."""
    p_scaff = get_scorer_params(
        "adr_lifecycle",
        "adr_scaffolding_and_lifecycle",
        override_config,
        default_weight=0.35,
    )
    p_trap = get_scorer_params(
        "adr_lifecycle",
        "adr_anti_trap_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_gov = get_scorer_params(
        "adr_lifecycle", "adr_governance_guard", override_config, default_weight=0.2
    )
    p_len = get_scorer_params(
        "adr_lifecycle",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="adr_scaffolding_and_lifecycle",
            pattern=r"(ADR|HUB-ADR|SPOKE-ADR|ACCEPTED|SUPERSEDED|DEPRECATED|docs/adr/|TRACEABILITY_MATRIX|matrix)",
            weight=p_scaff["weight"],
            is_critical=p_scaff["is_critical"],
        ),
        RegexScorer(
            name="adr_anti_trap_hard_floor",
            pattern=r"(superseded_by|supersedes|validate_adr_traceability|CI Parity|Context|Decision|Consequences|Invariants)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="adr_governance_guard",
            pattern=r"(Hub vs Spoke|SPOKE-ADR|HUB-ADR|Living Traceability Matrix|README\.md|YAML Frontmatter|parity)",
            weight=p_gov["weight"],
            is_critical=p_gov["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_skill_repair_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for SKILL.md linter, GPI, and ADR-0057 governance repair."""
    p_rep = get_scorer_params(
        "skill_repair",
        "skill_repair_gpi_and_frontmatter",
        override_config,
        default_weight=0.35,
    )
    p_trap = get_scorer_params(
        "skill_repair",
        "skill_repair_anti_trap_hard_floor",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_deb = get_scorer_params(
        "skill_repair",
        "skill_repair_debloat_and_verification",
        override_config,
        default_weight=0.2,
    )
    p_len = get_scorer_params(
        "skill_repair",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="skill_repair_gpi_and_frontmatter",
            pattern=r"(gpi|yaml|frontmatter|adr-0057|tier 2b|kernel|res-2026-arch-001|khối gpi)",
            weight=p_rep["weight"],
            is_critical=p_rep["is_critical"],
        ),
        RegexScorer(
            name="skill_repair_anti_trap_hard_floor",
            pattern=r"(cổng 0|gate 0|determinism|deep seam|packages/|cổng 1|gate 1|composite orchestrator|tiêu chí hoàn thành|completion criterion|validate_skills|evaluate-gpi)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="skill_repair_debloat_and_verification",
            pattern=r"(script bloat|100 loc|compile_catalog|tương đối|relative|linter|cú pháp yaml|phục hồi)",
            weight=p_deb["weight"],
            is_critical=p_deb["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]


def get_visual_design_scorers(
    override_config: dict[str, Any] | None = None,
) -> list[BaseScorer]:
    """Returns the standard scorer suite for brand identity, design tokens, typography, and CIP."""
    p_tok = get_scorer_params(
        "visual_design",
        "visual_design_tokens_and_colors",
        override_config,
        default_weight=0.35,
    )
    p_trap = get_scorer_params(
        "visual_design",
        "visual_design_brand_and_guidelines",
        override_config,
        default_weight=0.35,
        default_is_critical=True,
    )
    p_typ = get_scorer_params(
        "visual_design",
        "visual_design_typography_and_assets",
        override_config,
        default_weight=0.2,
    )
    p_len = get_scorer_params(
        "visual_design",
        "depth",
        override_config,
        default_weight=0.1,
        default_min_length=20,
        default_max_length=20000,
    )
    return [
        RegexScorer(
            name="visual_design_tokens_and_colors",
            pattern=r"(design token|color|palette|primary|secondary|neutral|semantic|#[0-9a-fA-F]{3,8}|hex|mã màu)",
            weight=p_tok["weight"],
            is_critical=p_tok["is_critical"],
        ),
        RegexScorer(
            name="visual_design_brand_and_guidelines",
            pattern=r"(brand|logo|safe zone|clear space|vùng an toàn|cip|corporate identity|ấn phẩm|nhận diện|quy chuẩn)",
            weight=p_trap["weight"],
            is_critical=p_trap["is_critical"],
        ),
        RegexScorer(
            name="visual_design_typography_and_assets",
            pattern=r"(typography|font|scale|hierarchy|phân cấp|banner|generate_image|prompt|tỷ lệ|aspect ratio)",
            weight=p_typ["weight"],
            is_critical=p_typ["is_critical"],
        ),
        LengthBoundsScorer(
            name="depth",
            min_length=p_len["min_length"],
            max_length=p_len["max_length"],
            weight=p_len["weight"],
            is_critical=p_len.get("is_critical", False),
        ),
    ]
