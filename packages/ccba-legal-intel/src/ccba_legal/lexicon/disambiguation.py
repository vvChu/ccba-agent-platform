"""Faceted Disambiguation Engine for CCILF (COND-16, ADR-0059).

Resolves polysemous construction terms, multi-law statutory definitions,
and internal governance terminology based on contextual window analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisambiguationResult:
    """Result of disambiguating a polysemous or context-sensitive term."""

    original_term: str
    canonical_id: str
    canonical_term: str
    domain: str
    facet_id: str | None = None
    statutory_ref: str | None = None
    confidence: float = 1.0
    notes: str | None = None
    warning: str | None = None


class FacetedDisambiguationEngine:
    """Engine for context-aware disambiguation of statutory and consulting terms."""

    # Domain keywords for "Chủ đầu tư" multi-law resolution (COND-16)
    INVESTOR_FACET_KEYWORDS: dict[str, tuple[str, str, set[str]]] = {
        "xay_dung": (
            "FACET-CHỦ-ĐẦU-TƯ-XD",
            "Điều 3 Khoản 9 Luật Xây dựng 2014",
            {
                "xây dựng",
                "thiết kế",
                "thi công",
                "nghiệm thu",
                "giám sát",
                "công trình",
                "bảo trì",
                "giấy phép xây dựng",
                "khởi công",
                "nhà thầu",
            },
        ),
        "dau_thau": (
            "FACET-CHỦ-ĐẦU-TƯ-ĐT",
            "Điều 4 Khoản 4 Luật Đấu thầu 2023",
            {
                "đấu thầu",
                "chỉ định thầu",
                "bên mời thầu",
                "hồ sơ mời thầu",
                "e-hsmt",
                "gói thầu",
                "chào hàng",
                "kế hoạch lựa chọn nhà thầu",
            },
        ),
        "dat_dai": (
            "FACET-CHỦ-ĐẦU-TƯ-ĐĐ",
            "Điều 3 Khoản 11 Luật Đất đai 2024",
            {
                "giao đất",
                "cho thuê đất",
                "thu hồi đất",
                "quy hoạch sử dụng đất",
                "chuyển mục đích",
                "sổ đỏ",
                "tiền sử dụng đất",
                "bồi thường giải phóng mặt bằng",
            },
        ),
        "nha_o": (
            "FACET-CHỦ-ĐẦU-TƯ-NO",
            "Điều 2 Khoản 6 Luật Nhà ở 2023",
            {
                "nhà ở",
                "chung cư",
                "bán nhà",
                "cho thuê mua",
                "bảo hành nhà",
                "quỹ bảo trì",
                "căn hộ",
                "ban quản trị nhà chung cư",
            },
        ),
    }

    # PCCC keywords
    PCCC_KEYWORDS = {
        "phòng cháy",
        "chữa cháy",
        "pccc",
        "cứu nạn",
        "cứu hộ",
        "thoát nạn",
        "khói",
        "gian lánh nạn",
        "xe thang",
    }

    def disambiguate_term(
        self,
        term: str,
        context: str,
        domain_hint: str | None = None,
    ) -> DisambiguationResult | None:
        """Disambiguates a term using surrounding context and optional domain hint."""
        norm_term = term.strip().lower()
        norm_context = context.lower()

        if "chủ đầu tư" in norm_term:
            return self._disambiguate_investor(term, norm_context, domain_hint)

        if "thẩm duyệt" in norm_term or "thẩm định" in norm_term or "thẩm tra" in norm_term:
            return self._disambiguate_appraisal_verification(term, norm_context)

        if "chiều cao" in norm_term:
            return self._disambiguate_height(term, norm_context)

        if norm_term in {"trung tâm ccba", "viện ibst", "ibst"}:
            return self._disambiguate_brand(term)

        return None

    def _disambiguate_investor(
        self,
        term: str,
        norm_context: str,
        domain_hint: str | None,
    ) -> DisambiguationResult:
        """Resolves polysemous 'Chủ đầu tư' across Construction, Procurement, Land, Housing."""
        scores: dict[str, int] = {}
        for domain, (_, _, keywords) in self.INVESTOR_FACET_KEYWORDS.items():
            hit_count = sum(1 for kw in keywords if kw in norm_context)
            if domain_hint and domain_hint == domain:
                hit_count += 3
            scores[domain] = hit_count

        best_domain = max(scores, key=lambda d: scores[d])
        facet_id, statutory_ref, _ = self.INVESTOR_FACET_KEYWORDS[best_domain]
        confidence = 0.95 if scores[best_domain] > 0 else 0.70

        return DisambiguationResult(
            original_term=term,
            canonical_id="STAT-CDT-001",
            canonical_term="Chủ đầu tư",
            domain=best_domain,
            facet_id=facet_id,
            statutory_ref=statutory_ref,
            confidence=confidence,
            notes=f"Resolved to domain '{best_domain}' based on contextual statutory markers.",
        )

    def _disambiguate_appraisal_verification(
        self, term: str, norm_context: str
    ) -> DisambiguationResult:
        """Disambiguates Thẩm tra vs Thẩm định vs Thẩm định thiết kế PCCC (Luật PCCC 2024)."""
        norm_term = term.strip().lower()
        has_pccc = any(kw in norm_context for kw in self.PCCC_KEYWORDS) or "pccc" in norm_term

        if has_pccc:
            warning = None
            if "thẩm duyệt" in norm_term:
                warning = (
                    "Thuật ngữ 'thẩm duyệt thiết kế PCCC' đã được thay thế bằng "
                    "'thẩm định thiết kế PCCC' theo Điều 2 Khoản 17 Luật PCCC 2024. "
                    "Áp dụng quy tắc chuyển tiếp đối với dự án trước 01/07/2025."
                )
            return DisambiguationResult(
                original_term=term,
                canonical_id="STAT-002",
                canonical_term="Thẩm định thiết kế PCCC",
                domain="pccc",
                facet_id="FACET-PCCC-APPRAISAL",
                statutory_ref="Điều 2 Khoản 17 Luật PCCC 2024",
                confidence=0.98,
                warning=warning,
            )

        if "thẩm tra" in norm_term or any(
            kw in norm_context for kw in {"tư vấn độc lập", "báo cáo thẩm tra"}
        ):
            return DisambiguationResult(
                original_term=term,
                canonical_id="STAT-001",
                canonical_term="Thẩm tra thiết kế",
                domain="xay_dung",
                facet_id="FACET-VERIFICATION",
                statutory_ref="Điều 82 Luật Xây dựng 2014",
                confidence=0.95,
                notes="Tư vấn độc lập kiểm tra sự tuân thủ kỹ thuật.",
            )

        return DisambiguationResult(
            original_term=term,
            canonical_id="STAT-001-APPRAISAL",
            canonical_term="Thẩm định thiết kế",
            domain="xay_dung",
            facet_id="FACET-APPRAISAL",
            statutory_ref="Điều 82 Luật Xây dựng 2014",
            confidence=0.95,
            notes="Hoạt động của cơ quan chuyên môn về xây dựng hoặc người quyết định đầu tư.",
        )

    def _disambiguate_height(self, term: str, norm_context: str) -> DisambiguationResult:
        """Disambiguates H_PCCC (QCVN 06:2022) vs Building Height (QCVN 01:2021)."""
        if any(kw in norm_context for kw in self.PCCC_KEYWORDS) or "pccc" in term.lower():
            return DisambiguationResult(
                original_term=term,
                canonical_id="STAT-003",
                canonical_term="Chiều cao PCCC (H_PCCC)",
                domain="pccc",
                facet_id="FACET-H-PCCC",
                statutory_ref="QCVN 06:2022/BXD Bảng A.1",
                confidence=0.95,
                notes="Xác định theo mặt đất xe thang chữa cháy tiếp cận được.",
            )

        return DisambiguationResult(
            original_term=term,
            canonical_id="TECH-001",
            canonical_term="Chiều cao công trình",
            domain="quy_hoach",
            facet_id="FACET-H-BUILDING",
            statutory_ref="QCVN 01:2021/BXD",
            confidence=0.90,
            notes="Tính từ cốt mặt đất quy hoạch đến điểm cao nhất của mái công trình.",
        )

    def _disambiguate_brand(self, term: str) -> DisambiguationResult:
        """Validates canonical institutional brand nomenclature (RULE-6.1)."""
        return DisambiguationResult(
            original_term=term,
            canonical_id="INT-GOV-001",
            canonical_term="IBST - CCBA",
            domain="internal_governance",
            facet_id="FACET-LEGAL-ENTITY",
            statutory_ref="Quy chế Tổ chức & Hoạt động CCBA 2026",
            confidence=1.0,
            warning="Nomenclature: Sử dụng tên thương hiệu chuẩn mực 'IBST - CCBA' theo RULE-6.1.",
        )
