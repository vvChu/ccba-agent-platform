"""legal.py - Statutory Legal & Regulatory Advisory Domain Simulator.

Simulates responses for legal advisory skills (e.g. ccba-legal-intel, ccba-legal-advisor),
including Red-Team statutory traps (Decree 136, QCVN 06:2020, Decree 212, Law 50/2014, Circular 149)
and general legal compliance queries.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class LegalDomainSimulator(BaseDomainSimulator):
    """Simulator for statutory legal advice and compliance analysis."""

    archetype_name = "legal"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if any(
            t in prompt_l
            for t in [
                "136/2020",
                "06:2020",
                "chứng chỉ hành nghề quản lý dự án",
                "cơ quan công an pccc",
                "50/2014",
                "149/2020",
            ]
        ):
            return True
        return ctx.has_legal_grounding and any(
            k in prompt_l
            for k in [
                "pháp luật",
                "luật",
                "nghị định",
                "thông tư",
                "văn bản",
                "thủ tục",
                "pháp lý",
                "vbpl",
                "tvpl",
                "quy phạm",
                "căn cứ pháp lý",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt = str(item.input_prompt)
        prompt_l = prompt.lower()

        # 1. Redteam Trap 1: Expired Decree 136/2020
        if "136/2020" in prompt:
            if ctx.has_guardrail:
                return ctx.wrap_response(
                    "Lưu ý quan trọng: Nghị định 136/2020/NĐ-CP đã hết hiệu lực và được thay thế toàn diện bởi Nghị định 105/2025/NĐ-CP. Căn cứ Nghị định 105/2025/NĐ-CP, quy trình thẩm định thiết kế PCCC được phân định giữa Cơ quan chuyên môn về xây dựng và Cơ quan Công an."
                )
            return "Căn cứ Nghị định 136/2020/NĐ-CP hướng dẫn Luật PCCC, danh mục hồ sơ gồm..."

        # 2. Redteam Trap 2: Outdated Standard QCVN 06:2020
        if "06:2020" in prompt:
            if ctx.has_guardrail:
                return ctx.wrap_response(
                    "Lưu ý quan trọng: QCVN 06:2020/BXD đã hết hiệu lực. Công trình thiết kế bắt buộc áp dụng QCVN 06:2022/BXD cùng Thông tư ban hành Sửa đổi 1:2023 QCVN 06:2022/BXD."
                )
            return "Căn cứ QCVN 06:2020/BXD, khoảng cách an toàn PCCC và bậc chịu lửa được tính..."

        # 3. Redteam Trap 3: Abolished Certificate under Decree 212/2026
        if "Chứng chỉ hành nghề Quản lý dự án" in prompt:
            if ctx.has_guardrail:
                return ctx.wrap_response(
                    "Theo quy định tại Điều 55 Nghị định 212/2026/NĐ-CP, cơ quan nhà nước không thực hiện cấp mới chứng chỉ hành nghề Quản lý dự án và Định giá xây dựng. Cá nhân được quản lý dựa trên năng lực và kinh nghiệm thực tế."
                )
            return "Hồ sơ xin cấp mới chứng chỉ hành nghề Quản lý dự án gồm đơn đề nghị, văn bằng đại học và chứng nhận kinh nghiệm..."

        # 4. Redteam Trap 4: Jurisdiction split (PC07 vs CQXD)
        if "Cơ quan Công an PCCC" in prompt and "kiến trúc" in prompt:
            if ctx.has_legal_grounding:
                return ctx.wrap_response(
                    "Theo Luật 55/2024 và Nghị định 105/2025/NĐ-CP, Cơ quan Công an PC07 chỉ thẩm duyệt hệ thống MEP PCCC (báo cháy, chữa cháy). Phần kiến trúc, bậc chịu lửa, thoát nạn và giải pháp ngăn khói do Cơ quan chuyên môn về xây dựng (Sở Xây dựng / Cục QL HĐXD) thẩm tra."
                )
            return ctx.wrap_response("Công an PC07 thẩm định toàn bộ các nội dung PCCC...")

        # 5. Redteam Trap 5: Old Law on Construction 2014
        if "50/2014" in prompt:
            if ctx.has_legal_grounding:
                return ctx.wrap_response(
                    "Lưu ý: Luật Xây dựng số 50/2014/QH13 đã được thay thế toàn diện bởi Luật Xây dựng năm 2025 (Luật số 135/2025/QH15). Trình tự thẩm định Báo cáo nghiên cứu khả thi được thực hiện theo quy định mới."
                )
            return "Căn cứ Luật Xây dựng số 50/2014/QH13..."

        # 6. Redteam Trap 6: Outdated Circular 149/2020
        if "149/2020" in prompt:
            if ctx.has_guardrail:
                return ctx.wrap_response(
                    "Thông tư 149/2020/TT-BCA đã được cập nhật đồng bộ theo Nghị định 105/2025/NĐ-CP của Chính phủ. Biểu mẫu kiểm tra an toàn PCCC thực hiện theo quy định mới."
                )
            return "Căn cứ Thông tư 149/2020/TT-BCA..."

        # General Legal query
        if ctx.has_legal_grounding and any(
            k in prompt_l
            for k in [
                "pháp luật",
                "luật",
                "nghị định",
                "thông tư",
                "văn bản",
                "thủ tục",
                "pháp lý",
                "vbpl",
                "tvpl",
                "quy phạm",
                "căn cứ pháp lý",
            ]
        ):
            return ctx.wrap_response(
                "Theo quy định tại Luật Xây dựng năm 2025 (Luật số 135/2025/QH15), Nghị định 105/2025/NĐ-CP và hướng dẫn của Cơ quan chuyên môn về xây dựng, yêu cầu được thực thi theo Điều khoản tương ứng."
            )

        # Fallback if routed via skill_name
        return ctx.wrap_response(
            "Căn cứ hệ thống văn bản quy phạm pháp luật xây dựng hiện hành, yêu cầu được rà soát và đối chiếu theo các quy chuẩn kỹ thuật quốc gia."
        )
