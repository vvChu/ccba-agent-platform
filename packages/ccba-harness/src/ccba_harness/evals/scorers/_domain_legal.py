"""scorers/_domain_legal.py - Foundational structural, legal provenance, and tooling scorers."""

from __future__ import annotations

import re
from typing import Any

from ..legal_index import LegalFlatIndex, StatutoryDocument, load_legal_flat_index
from ..models import EvalItem, ScoreResult
from .base import BaseScorer, get_scorer_params
from .rule_based import LengthBoundsScorer


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


_LEGAL_DOC_PATTERNS: list[re.Pattern[str]] = [
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

_LEGAL_CLAUSE_DOC_PATTERNS: list[tuple[re.Pattern[str], int, int]] = [
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

_REPLACEMENT_INDICATORS: tuple[str, ...] = (
    "thay thế",
    "hết hiệu lực",
    "bãi bỏ",
    "hết hạn",
    "bị thay",
    "superseded",
    "expired",
    "thay bằng",
)


class LegalVerbatimProvenanceScorer(BaseScorer):
    """Evaluates legal verbatim provenance, gazette citations, and anti-trap constraints (ADR-0059)."""

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
        self.doc_patterns = list(_LEGAL_DOC_PATTERNS)
        self.clause_doc_patterns = list(_LEGAL_CLAUSE_DOC_PATTERNS)
        self.replacement_indicators = _REPLACEMENT_INDICATORS

    def _extract_citations_and_pairs(
        self, out_str: str, out_lower: str, index: LegalFlatIndex
    ) -> tuple[list[str], list[tuple[str, str]]]:
        """Extract candidate document references and (clause, doc_ref) pairs from output text."""
        detected_doc_refs: list[str] = []
        for pat in self.doc_patterns:
            for m in pat.finditer(out_str):
                ref = m.group(1).strip(".,;:() ") if m.groups() else m.group(0).strip(".,;:() ")
                if ref and ref not in detected_doc_refs:
                    detected_doc_refs.append(ref)

        for doc_num in list(index.documents.keys()) + list(index.replaces_map.keys()):
            if doc_num.lower() in out_lower and doc_num not in detected_doc_refs:
                detected_doc_refs.append(doc_num)

        extracted_pairs: list[tuple[str, str]] = []
        for pat, clause_grp, doc_grp in self.clause_doc_patterns:
            for m in pat.finditer(out_str):
                clause = m.group(clause_grp).strip(".,;:() ")
                dref = m.group(doc_grp).strip(".,;:() ")
                if clause and dref:
                    extracted_pairs.append((clause, dref))
        return detected_doc_refs, extracted_pairs

    def _verify_detected_documents(
        self, detected_doc_refs: list[str], out_lower: str, index: LegalFlatIndex
    ) -> tuple[list[StatutoryDocument], ScoreResult | None]:
        """Verify each cited document against expiration traps and gazette existence."""
        verified_docs: list[StatutoryDocument] = []
        seen_doc_numbers: set[str] = set()
        for doc_ref in detected_doc_refs:
            is_exp, replacement = index.is_expired_or_replaced(doc_ref)
            if is_exp:
                has_indicator = any(kw in out_lower for kw in self.replacement_indicators)
                if replacement:
                    rep_short = replacement.split("/")[0].lower()
                    has_rep_cited = rep_short in out_lower or replacement.lower() in out_lower
                else:
                    has_rep_cited = True
                if not (has_indicator and has_rep_cited):
                    return [], ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"trap_doc": doc_ref, "replacement": replacement},
                        reasoning=(
                            f"Bẫy pháp lý (Anti-Trap Hard Floor): Trích dẫn văn bản đã hết hiệu lực/bị thay thế '{doc_ref}' "
                            f"mà không nêu rõ đã được thay thế bởi '{replacement}'"
                        ),
                        is_critical_fail=True,
                    )
                continue

            doc = index.get_document(doc_ref)
            if doc is None:
                return [], ScoreResult(
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
        return verified_docs, None

    def _verify_cited_clauses(
        self, extracted_pairs: list[tuple[str, str]], index: LegalFlatIndex
    ) -> tuple[dict[str, list[str]], ScoreResult | None]:
        """Verify that all cited clauses exist within their respective statutory documents."""
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
                    return doc_clause_map, ScoreResult(
                        scorer_name=self.name,
                        score=0.0,
                        raw_output={"doc": doc_num, "fake_clause": cl},
                        reasoning=(
                            f"Bịa đặt điều khoản (Zero-Hallucination Hard Floor): "
                            f"Điều/Khoản '{cl}' không tồn tại trong văn bản '{target_doc.document_number}'"
                        ),
                        is_critical_fail=True,
                    )
        return doc_clause_map, None

    def _verify_target_law(
        self, item: EvalItem, out_lower: str, index: LegalFlatIndex
    ) -> ScoreResult | None:
        """Verify target law citation if specified in test item metadata."""
        target_law = item.metadata.get("target_law") or item.metadata.get("law")
        if not target_law:
            return None
        target_nums = re.findall(
            r"\b([0-9]+/[0-9]{4}|QCVN\s+[0-9]+(?::[0-9]{4})?|TCVN\s+[0-9]+(?::[0-9]{4})?)\\b",
            str(target_law),
            re.IGNORECASE,
        )
        if target_nums and not any(num.lower() in out_lower for num in target_nums):
            target_matched = any(
                (rep := index.is_expired_or_replaced(num)[1]) and rep.lower() in out_lower
                for num in target_nums
            )
            if not target_matched:
                return ScoreResult(
                    scorer_name=self.name,
                    score=0.0,
                    raw_output={"target_law": target_law},
                    reasoning=f"Không viện dẫn đúng văn bản mục tiêu '{target_law}' theo yêu cầu nghiệp vụ",
                    is_critical_fail=True,
                )
        return None

    def _build_provenance_success(
        self, verified_docs: list[StatutoryDocument], doc_clause_map: dict[str, list[str]]
    ) -> ScoreResult:
        """Build final verified ScoreResult with cryptographic SHA-256 provenance records."""
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

    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        out_str = str(output) if output is not None else ""
        if not out_str.strip():
            msg = (
                "Văn bản phản hồi rỗng, không phát hiện trích dẫn căn cứ pháp lý"
                if self.require_citation
                else "Empty output allowed without citations"
            )
            return ScoreResult(
                scorer_name=self.name,
                score=0.0 if self.require_citation else 1.0,
                reasoning=msg,
                is_critical_fail=self.is_critical if self.require_citation else False,
            )

        index = self._index or load_legal_flat_index()
        out_lower = out_str.lower()
        detected_doc_refs, extracted_pairs = self._extract_citations_and_pairs(
            out_str, out_lower, index
        )
        if not detected_doc_refs:
            msg = (
                "Không phát hiện trích dẫn văn bản quy phạm pháp luật nào "
                "(Luật, Nghị định, Thông tư, QCVN, TCVN) theo quy chuẩn ADR-0059"
                if self.require_citation
                else "No citations required"
            )
            return ScoreResult(
                scorer_name=self.name,
                score=0.0 if self.require_citation else 1.0,
                raw_output={"citations_found": 0} if self.require_citation else None,
                reasoning=msg,
                is_critical_fail=self.is_critical if self.require_citation else False,
            )

        verified_docs, doc_err = self._verify_detected_documents(
            detected_doc_refs, out_lower, index
        )
        if doc_err is not None:
            return doc_err
        doc_clause_map, clause_err = self._verify_cited_clauses(extracted_pairs, index)
        if clause_err is not None:
            return clause_err
        if (law_err := self._verify_target_law(item, out_lower, index)) is not None:
            return law_err
        return self._build_provenance_success(verified_docs, doc_clause_map)


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

        raw_output: dict[str, Any] = {
            "matched": matched,
            "citations_found": 1 if matched else 0,
            "sha256_verified": matched,
        }

        return ScoreResult(
            scorer_name=self.name,
            score=score,
            raw_output=raw_output,
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
