"""tech_qc.py - Technical QC & PCCC Fire Safety Audit Domain Simulator.

Simulates responses for PCCC audit skills (e.g. ccba-ai-qc, ccba-ai-qc-pccc-audit),
including QCVN 06:2022/BXD parametric audit traps and general PCCC compliance verifications.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class TechQCDomainSimulator(BaseDomainSimulator):
    """Simulator for PCCC fire protection and technical QC audit."""

    archetype_name = "tech_qc"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if (
            ("65m" in prompt_l and "bậc ii" in prompt_l)
            or ("25m" in prompt_l and "hút khói" in prompt_l)
            or ("45m" in prompt_l and "hành lang cụt" in prompt_l)
            or ("kết cấu vì kèo thép" in prompt_l and "để trần" in prompt_l)
            or ("cao 45m" in prompt_l and "thang bộ loại 1" in prompt_l)
            or ("tường ngăn cháy" in prompt_l and "không lắp van ngăn cháy" in prompt_l)
        ):
            return True
        return "qcvn 06" in prompt_l or "pccc" in prompt_l

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt = str(item.input_prompt)
        prompt_l = prompt.lower()

        # PCCC Trap 1: 65m height & Bậc II
        if "65m" in prompt and "Bậc II" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Từ chối chấp thuận đề xuất Bậc II. Căn cứ QCVN 06:2022/BXD Bảng H.1, nhà nhóm F1.3 có chiều cao PCCC > 50m bắt buộc phải thiết kế Bậc chịu lửa Bậc I. Yêu cầu chủ đầu tư và tư vấn điều chỉnh giải pháp kết cấu."
                )
            return "Chấp thuận đề xuất thiết kế Bậc chịu lửa Bậc II cho công trình chung cư..."

        # PCCC Trap 2: Smoke control corridor 25m
        if "25m" in prompt and "hút khói" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Vi phạm quy chuẩn kiểm soát khói. Căn cứ QCVN 06:2022/BXD Phụ lục D (Mục D.1, D.2), hành lang dài > 15m không có thông gió tự nhiên bắt buộc phải trang bị hệ thống hút khói cơ khí sự cố. Yêu cầu bổ sung quạt hút khói và van khói."
                )
            return "Chấp thuận giải pháp không lắp hệ thống hút khói sự cố cơ khí..."

        # PCCC Trap 3: Evacuation distance 45m dead-end corridor
        if "45m" in prompt and "hành lang cụt" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Kết luận không đạt quy chuẩn. Căn cứ Bảng G.1/G.2 QCVN 06:2022/BXD, khoảng cách thoát nạn từ cửa phòng đến buồng thang bộ ở hành lang cụt tối đa chỉ từ 15m - 20m (hoặc 25m nếu có chữa cháy tự động). Khoảng cách 45m vi phạm nghiêm trọng giới hạn an toàn."
                )
            return "Xác nhận khoảng cách 45m đạt chuẩn QCVN 06:2022..."

        # PCCC Trap 4: Unprotected steel structure
        if "kết cấu vì kèo thép" in prompt and "để trần" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Từ chối phê duyệt. Căn cứ QCVN 06:2022/BXD Bảng 4, kết cấu chịu lực chính và giàn/kèo mái của công trình Bậc I bắt buộc phải đạt giới hạn chịu lửa R45/R90/R120. Thép để trần không có lớp bọc bảo vệ sẽ mất khả năng chịu lực trong 10-15 phút khi có cháy."
                )
            return "Phê duyệt giải pháp để trần hệ kết cấu vì kèo thép..."

        # PCCC Trap 5: Smokeproof staircase N1/N2 for building > 28m
        if "cao 45m" in prompt and "thang bộ loại 1" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Đánh giá vi phạm nghiêm trọng an toàn sinh mạng. Căn cứ QCVN 06:2022/BXD Điều 3.4.12, nhà có chiều cao PCCC > 28m bắt buộc phải sử dụng buồng thang bộ không nhiễm khói loại N1 hoặc N2/N3 có hệ thống tăng áp, nghiêm cấm dùng thang bộ thông thường loại 1."
                )
            return "Bố trí 2 buồng thang bộ loại 1 thông thường là hợp lệ..."

        # PCCC Trap 6: Fire damper and EI duct for fire compartments
        if "tường ngăn cháy" in prompt and "không lắp van ngăn cháy" in prompt:
            if ctx.has_pccc_guardrail:
                return ctx.wrap_response(
                    "Kết luận không hợp lệ và từ chối xác nhận. Căn cứ QCVN 06:2022/BXD Điều 2.5 và Phụ lục D, ống gió xuyên qua tường ngăn cháy bắt buộc phải lắp van ngăn cháy tự động và đoạn ống xuyên phải được bọc cách nhiệt đạt giới hạn chịu lửa EI tương ứng."
                )
            return "Xác nhận giải pháp ống dẫn gió tôn mạ kẽm 0.8mm không lắp van ngăn cháy..."

        # General PCCC / QCVN 06
        if "qcvn 06" in prompt_l or "pccc" in prompt_l:
            return ctx.wrap_response(
                "Căn cứ Nghị định 105/2025/NĐ-CP và QCVN 06:2022/BXD (Sửa đổi 1:2023), quy định bậc chịu lửa và giải pháp thoát nạn công trình."
            )

        return ctx.wrap_response(
            "Căn cứ QCVN 06:2022/BXD và quy chuẩn thẩm duyệt an toàn cháy, phương án thiết kế được đối soát theo đúng tiêu chuẩn kỹ thuật."
        )
