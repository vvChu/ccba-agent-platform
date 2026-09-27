"""bim_classification.py - BIM Uniclass 200 & ISO 12006-2 Domain Simulator.

Simulates responses for BIM classification skills (e.g. bigbim-classification),
including Uniclass 200 tables (En, SL, EF, Ss, Pr, PM), ISO 12006-2 Result vs Resource disambiguation,
ISO 19650 Room Naming, IFC Alignment, Digital Memory preservation, and Red-Team disambiguation traps.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class BimClassificationDomainSimulator(BaseDomainSimulator):
    """Simulator for Uniclass 200 and ISO 12006-2 BIM object classification."""

    archetype_name = "bim"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return any(
            k in prompt_l
            for k in [
                "uniclass",
                "iso 19650",
                "iso 12006",
                "iso 21511",
                "ifc",
                "bim",
                "cấu kiện",
                "hộp kỹ thuật",
                "dam d1",
                "boq",
                "đoạn đường cong",
                "khoang đệm",
                "air-lock",
                "sơn phồng nở",
                "kiosk",
                "thang máy",
                "barrette",
                "mc d800",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt = str(item.input_prompt)
        prompt_l = prompt.lower()
        content = ctx.content

        has_bim_grounding = "Uniclass" in content or "ISO 12006-2" in content
        has_bim_naming = "ISO 19650" in content or "IFC Alignment" in content
        has_digital_memory = "Trí Nhớ Số" in content or "Digital Memory" in content
        has_redteam_rules = (
            "Red-Team" in content
            or "EF_25_10" in content
            or "SL_25_30_70" in content
            or "EF_20_20" in content
        )

        # Specific Red-Team Traps Disambiguation
        if "hộp kỹ thuật" in prompt_l:
            if has_redteam_rules or "EF_25_10" in content:
                return ctx.wrap_response(
                    "Phân loại: EF_25_10 (Vách bao che hộp kỹ thuật kiến trúc Result), chứa các hệ thống MEP (Ss_50, Ss_70, Ss_65) bên trong theo ISO 12006-2 và bảo tồn Trí Nhớ Số."
                )
            return "Phân loại Hộp kỹ thuật là Hệ thống MEP Ss_65..."

        if "dam d1" in prompt_l:
            if has_redteam_rules or "EF_20_20" in content:
                return ctx.wrap_response(
                    "Chuẩn hóa viết tắt: Dầm bê tông cốt thép dự ứng lực sàn L03. Mã Uniclass: EF_20_20. Định danh ISO 19650: SUN-CITY-VP1-L03-EF_20_20-D1."
                )
            return "Phân loại dầm btct..."

        if "cửa trượt tự động" in prompt_l:
            if has_redteam_rules or "Result" in content:
                return ctx.wrap_response(
                    "Phân định 2 góc nhìn ISO 12006-2: Mô hình BIM Object Result = EF_25_30 vs Mua sắm BOQ Resource = Pr_30_59_24 (Cửa trượt tự động) bảo tồn Trí Nhớ Số (Digital Memory)."
                )
            return "Cửa tự động là EF_25_30..."

        if "đoạn đường cong" in prompt_l or "siêu cao" in prompt_l:
            if has_bim_naming or "IFC Alignment" in content:
                return ctx.wrap_response(
                    "Hạ tầng tuyến tính IFC Alignment: CT05-KM002_150_KM002_450-EF_10_10 (Spatial Structure dọc tim tuyến) bảo tồn Trí Nhớ Số."
                )
            return "Phân loại đường cong tầng 1..."

        if "khoang đệm" in prompt_l or "air-lock" in prompt_l:
            if has_redteam_rules or "SL_25_30_70" in content:
                return ctx.wrap_response(
                    "Khoang đệm ngăn cháy tăng áp: SL_25_30_70 (Không gian đệm an toàn) tuân thủ QCVN 06:2022/BXD và định danh ISO 19650 PRJ-T1-B02-SL_25_30_70-001 bảo tồn BIM Object Spatial Structure."
                )
            return "Khoang đệm là phòng điện SL_70..."

        if "barrette" in prompt_l and "vách thạch cao" in prompt_l:
            if has_redteam_rules or "EF_20_05" in content:
                return ctx.wrap_response(
                    "Phân định kết cấu ngầm EF_20_05 (Tường vây Barrette Result) tách biệt với vách ngăn nhẹ EF_25_10 bảo tồn Trí Nhớ Số."
                )
            return "Tường vây là vách ngăn EF_25..."

        if "mc d800" in prompt_l or "coc ly tam" in prompt_l:
            if has_redteam_rules or "EF_20_10" in content:
                return ctx.wrap_response(
                    "Chuẩn hóa viết tắt: Móng cọc bê tông ly tâm D800. Mã Uniclass EF_20_10 (Result) định danh ISO 19650 ECO-GREEN-BLD1-L01-EF_20_10-P01."
                )
            return "Móng cọc ly tâm là mc..."

        if "thang máy" in prompt_l and "phối hợp kiến trúc" in prompt_l:
            if has_redteam_rules or "EF_25_50" in content:
                return ctx.wrap_response(
                    "Phân định 2 góc nhìn: Mô hình kiến trúc Result = EF_25_50 (Lưu thông đứng) vs Hệ thống cơ điện = Ss_70_50_10 (Thang máy) bảo tồn Trí Nhớ Số BIM Object."
                )
            return "Thang máy là EF_25..."

        if "sơn phồng nở" in prompt_l or "r90" in prompt_l:
            if has_redteam_rules or "Pr_60_60_15" in content:
                return ctx.wrap_response(
                    "Phân định bóc tách mua sắm Resource = Pr_60_60_15 vs Thuộc tính mô hình BIM Object Property Set (Pset_FireRating) bảo tồn Trí Nhớ Số."
                )
            return "Sơn chống cháy là lớp hoàn thiện..."

        if "kiosk" in prompt_l or "hợp bộ ngoài trời" in prompt_l:
            if has_redteam_rules or "En_50_10" in content:
                return ctx.wrap_response(
                    "Phân định phân tách cấp độ ISO 12006-2: Thực thể quy hoạch En_50_10 Result vs Hệ thống thiết bị điện Ss_70_10_10 bảo tồn Trí Nhớ Số BIM Object."
                )
            return "Trạm Kiosk là hệ thống điện..."

        if has_bim_grounding and has_bim_naming and has_digital_memory:
            bim_resp = (
                "Phân loại cấu kiện và đặt tên thực thể theo chuẩn Uniclass 200 & ISO 12006-2:\n"
                "- Bảng phân loại: Uniclass (En, SL, EF, Ss, Pr, PM) tuân thủ ISO 22274 và ISO 21511 WBS.\n"
                "- Phân định rõ ràng giữa Result (EF/Ss/SL) và Resource (Pr/PM) theo ISO 12006-2.\n"
                "- Cấu trúc định danh ISO 19650 / IFC Alignment bảo tồn Trí Nhớ Số (Digital Memory) và cấu trúc không gian Spatial Structure cho mô hình BIM Object (IFC4X3)."
            )
            if "qcvn 06" in prompt_l or "pccc" in prompt_l:
                bim_resp += "\n\nĐảm bảo đáp ứng đầy đủ yêu cầu an toàn cháy và thoát nạn theo QCVN 06:2022/BXD."
            return ctx.wrap_response(bim_resp)

        if has_bim_grounding:
            return ctx.wrap_response("Phân loại theo bảng Uniclass 200 và ISO 12006-2.")

        return "Xử lý phân loại chung không theo chuẩn Uniclass..."
