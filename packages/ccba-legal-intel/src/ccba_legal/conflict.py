"""Lex Conflict Engine & Quantitative Risk Scoring Component.

Evaluates conflicts between Vietnamese legal documents (Laws, Decrees, Circulars)
using Lex Superior, Lex Posterior, and Lex Specialis rules, and assigns Risk Scores (Green/Yellow/Red).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLabel(str, Enum):
    """Risk classification labels for legal advisory outputs."""

    GREEN = "GREEN"  # Score 80-100 (Safe, full alignment)
    YELLOW = "YELLOW"  # Score 50-79 (Conditional compliance / Justification dossier required)
    RED = "RED"  # Score < 50 (High risk / Gray area / Official Consultation Dispatch suggested)


HIERARCHY_RANK = {
    "Hiến pháp": 100,
    "Luật": 90,
    "Bộ luật": 90,
    "Nghị định": 70,
    "Thông tư": 50,
    "Quyết định": 40,
    "Dự thảo": 20,
}


@dataclass
class RiskAssessmentScore:
    """Dataclass encapsulating quantitative risk evaluation results."""

    score: int
    risk_label: RiskLabel
    conflict_rules_applied: list[str] = field(default_factory=list)
    transitional_clause_flag: bool = False
    summary: str = ""


class LexConflictEngine:
    """Engine for evaluating conflicts between legal documents."""

    def evaluate_conflict(
        self, doc_a: dict[str, Any], doc_b: dict[str, Any], event_date: str = ""
    ) -> RiskAssessmentScore:
        """Evaluate conflict between doc_a and doc_b considering event_date."""
        rules_applied = []
        score = 90
        transitional_flag = False

        status_a = doc_a.get("status", "effective")
        status_b = doc_b.get("status", "effective")

        # Check for expired or draft status (RED condition)
        if (
            status_a == "expired"
            or status_b == "expired"
            or status_a == "draft"
            or status_b == "draft"
        ):
            rules_applied.append("Status Check: Expired/Draft document detected")
            return RiskAssessmentScore(
                score=40,
                risk_label=RiskLabel.RED,
                conflict_rules_applied=rules_applied,
                transitional_clause_flag=True,
                summary="Khoảng xám pháp lý: Có văn bản hết hiệu lực hoặc đang ở dạng dự thảo chưa hướng dẫn.",
            )

        type_a = doc_a.get("doc_type", "")
        type_b = doc_b.get("doc_type", "")
        rank_a = HIERARCHY_RANK.get(type_a, 50)
        rank_b = HIERARCHY_RANK.get(type_b, 50)
        domain_a = doc_a.get("domain")
        domain_b = doc_b.get("domain")

        # Lex Superior / Hierarchy check: Different hierarchy levels with domain mismatch
        if rank_a != rank_b:
            if domain_a and domain_b and domain_a != domain_b:
                rules_applied.append(
                    "Lex Superior: Hiệu lực văn bản cấp trên ưu tiên áp dụng do khác ngành"
                )
                score -= 25
            else:
                rules_applied.append(
                    "Lex Superior: Đối chiếu phân cấp VBQPPL (Luật/Nghị định/Thông tư)"
                )
                score -= 5

        # Lex Specialis / Domain mismatch for same rank
        elif domain_a and domain_b and domain_a != domain_b:
            rules_applied.append("Lex Specialis: Xung đột giữa quy chuẩn chuyên ngành và chung")
            score -= 15

        # Enactment date transition check
        date_a = doc_a.get("enactment_date", "")
        date_b = doc_b.get("enactment_date", "")
        if date_a and date_b and date_a != date_b:
            rules_applied.append("Lex Posterior: Văn bản ban hành sau áp dụng cho quan hệ mới")
            transitional_flag = True

        # Assign risk label based on score
        if score >= 80:
            label = RiskLabel.GREEN
            summary = "An toàn: Các văn bản đồng bộ, không phát hiện rủi ro pháp lý."
        elif score >= 50:
            label = RiskLabel.YELLOW
            summary = "Tuân thủ có điều kiện: Xuất hiện sự lệch pha cấp văn bản, cần lập Hồ sơ Giải trình."
        else:
            label = RiskLabel.RED
            summary = (
                "Rủi ro cao: Phát hiện xung đột trọng yếu hoặc khoảng xám chưa được hướng dẫn."
            )

        return RiskAssessmentScore(
            score=score,
            risk_label=label,
            conflict_rules_applied=rules_applied,
            transitional_clause_flag=transitional_flag,
            summary=summary,
        )
