"""bim_governance.py - BIGBIM Governance & Golden/Red Thread Domain Simulator.

Simulates responses for governance skills (e.g. bigbim-governance),
including Golden Thread (75 years, PM_80, ST2, Đoạn Đò-3), Red Thread (RK_50_40_35,
RK_10_70_04, RK_50_40_45, RK_50_60_28), and 3-way Unique ID traceability.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class BimGovernanceDomainSimulator(BaseDomainSimulator):
    """Simulator for BIGBIM information governance and thread audit."""

    archetype_name = "bim_governance"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return "governance" in ctx.skill_name.lower() or any(
            k in prompt_l
            for k in [
                "sợi chỉ vàng",
                "sợi chỉ đỏ",
                "golden thread",
                "red thread",
                "unique id",
                "governance",
                "iso 19650-5",
                "st2",
                "pm_80",
                "75 năm",
                "rk_50_40_35",
                "rk_10_70_04",
                "rk_50_40_45",
                "rk_50_60_28",
                "đoạn đò-3",
                "lms vendor lock-in",
                "đối soát 3 chiều",
                "3-way traceability",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_gov_grounding = (
            "sợi chỉ vàng" in content.lower()
            or "golden thread" in content.lower()
            or "governance" in content.lower()
            or "iso 19650-5" in content.lower()
            or "st2" in content.lower()
            or "unique id" in content.lower()
        )
        if has_gov_grounding or "bigbim" in content.lower():
            return ctx.wrap_response(
                "Kiểm duyệt Sợi Chỉ Vàng & Rào chắn Sợi Chỉ Đỏ (BIGBIM Governance Core):\n"
                "- Trụ cột Sợi Chỉ Vàng (Golden Thread): Quản trị thông tin dài hạn 75 năm (PM_80), phân cấp an ninh thông tin đạt cấp ST2 theo ISO 19650-5, kiểm soát chuyển giao Đoạn Đò-3 triệt tiêu nguy cơ LMS vendor lock-in.\n"
                "- Trụ cột Sợi Chỉ Đỏ (Red Thread Risk Matrix): Quét và kích hoạt 4 mã rủi ro chuẩn hóa:\n"
                "  + RK_50_40_35 — No-Risk: Bàn giao vận hành pha C2 thiếu người nhận hoặc không khớp sơ đồ tổ chức.\n"
                "  + RK_10_70_04 — Time-Risk: Nghiệm thu kỹ thuật C1 thiếu đội ngũ FM hoặc quy trình tự vận hành.\n"
                "  + RK_50_40_45 — Do-Risk: Sai lệch cấu trúc dữ liệu IFC hoặc thiếu ICT protocol đồng bộ vượt ngưỡng tới hạn.\n"
                "  + RK_50_60_28 — Use-Risk: Thiếu Mô hình Thông tin Tài sản (AIM) hoàn thiện, nguy cơ đứt gãy Trí Nhớ Số En_25_70_47.\n"
                "- Cưỡng chế Unique ID Bất biến & Đối soát 3 Chiều: Khóa mã Unique ID từ pha khởi đầu BBP-A0; đối soát 3 chiều (Bản vẽ thiết kế == Hệ thống AIM == Biển hiệu thực tế tại công trình) phát hiện trôi dạt định danh (Unique ID drift).\n"
                "```markdown\n"
                "### BÁO CÁO KIỂM DUYỆT GOVERNANCE\n"
                "1. Sợi Chỉ Vàng: Cấp độ an ninh ST2 (ISO 19650-5), thời hạn 75 năm (PM_80), Đoạn Đò-3 tuân thủ.\n"
                "2. Sợi Chỉ Đỏ: Đánh giá RK_50_40_35 (No-Risk), RK_10_70_04 (Time-Risk), RK_50_40_45 (Do-Risk), RK_50_60_28 (Use-Risk).\n"
                "3. Đối soát 3 chiều Unique ID: Cưỡng chế BBP-A0, đối soát bản vẽ thiết kế, AIM và biển hiệu thực tế.\n"
                "```"
            )
        return ctx.wrap_response("Kiểm tra governance thông thường...")
