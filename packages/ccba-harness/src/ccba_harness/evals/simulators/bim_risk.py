"""bim_risk.py - BIGBIM Risk & Information Conflict Audit Domain Simulator.

Simulates responses for risk assessment skills (e.g. bigbim-risk),
including Level 2 Space Gap, Maintenance Clearance, Unique ID drift, and INF-CON json schema reports.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class BimRiskDomainSimulator(BaseDomainSimulator):
    """Simulator for BIGBIM information conflict audit and risk detection."""

    archetype_name = "risk"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return any(
            k in prompt_l
            for k in [
                "mâu thuẫn thông tin",
                "information conflict",
                "v2 - coordination",
                "khoảng hở",
                "clearance",
                "level 2 space gap",
                "unique id drift",
                "bảo trì",
                "bơm chữa cháy",
                "lỗ mở",
                "sleeve",
                "thuộc tính bbp",
                "inf-con-",
                "khoảng cách an toàn",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_risk_grounding = (
            "mâu thuẫn thông tin" in content.lower()
            or "information conflict" in content.lower()
            or "v2 - coordination" in content.lower()
            or "rủi ro thông tin" in content.lower()
        )
        if has_risk_grounding or "bigbim" in content.lower():
            return ctx.wrap_response(
                "Phát hiện và xử lý Mâu thuẫn thông tin (Information Conflict) tại bước V2 - Coordination:\n"
                "- Phân cấp xung đột: Va chạm vật lý Level 1 vs Khoảng trống vô hình Level 2 (Level 2 Space Gap / Maintenance Clearance).\n"
                "- Quy chuẩn khoảng cách an toàn: Mặt trước tủ điện, máy bơm và thiết bị lớn yêu cầu clearance >= 900mm; đường ống kỹ thuật trần đến dầm/sàn yêu cầu khoảng hở >= 150mm để siết đai ốc.\n"
                "- Kiểm soát thuộc tính BBP và Sợi Chỉ Đỏ: Giữ nguyên vẹn cấu trúc Unique ID gán từ BBP-A0, ngăn chặn trôi dạt định danh (Unique ID drift) và đối soát công suất BBP-B1 vs BBP-B2.\n"
                "- Phối hợp kỹ thuật: Bố trí lỗ mở chờ (sleeve), van ngăn cháy tự động tường ngăn cháy và bọc cách nhiệt EI theo QCVN 06:2022/BXD.\n"
                "- Leo thang phân rã đa chiều: Triệu hồi /ccba-issue-tree (Why-Tree tìm gốc rễ trôi dạt, How-Tree xếp hạng phương án điều phối) dưới quyền Chủ trì Bộ môn phê duyệt.\n"
                "```json\n"
                "[\n"
                "  {\n"
                '    "conflict_id": "INF-CON-001",\n'
                '    "conflict_type": "Level 2 Space Gap",\n'
                '    "phase_origin": "V2 - Coordination",\n'
                '    "description": "Khoảng hở an toàn bảo trì không đạt chuẩn (yêu cầu >= 900mm hoặc >= 150mm)",\n'
                '    "impact": "Ảnh hưởng nghiêm trọng đến vận hành bảo trì và an toàn PCCC",\n'
                '    "entities_involved": [\n'
                "      {\n"
                '        "entity_type": "IfcDistributionFlowElement",\n'
                '        "unique_id": "PRJ-MEP-EQ-001",\n'
                '        "role": "Cấu kiện thiết bị cơ điện"\n'
                "      }\n"
                "    ],\n"
                '    "proposed_mitigation": "Dịch chuyển vị trí cấu kiện hoặc nâng cao độ để đảm bảo clearance quy định"\n'
                "  }\n"
                "]\n"
                "```"
            )
        return ctx.wrap_response("Xử lý va chạm hình học thông thường...")
