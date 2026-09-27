"""visual_design.py - Brand Identity & Design System Domain Simulator.

Simulates responses for design skills (e.g. ccba-design),
including Design Tokens, Typography hierarchy, Logo safe zones, generate_image prompts, and CIP specifications.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class VisualDesignDomainSimulator(BaseDomainSimulator):
    """Simulator for brand identity, CIP, and visual design systems."""

    archetype_name = "visual_design"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in ("ccba-design", "design", "visual_design"):
            return True
        return any(
            k in prompt_l
            for k in [
                "design token",
                "bảng màu",
                "mã màu hex",
                "font scale",
                "safe zone",
                "vùng an toàn",
                "clear space",
                "generate_image",
                "ấn phẩm thương hiệu",
                "cip",
                "corporate identity",
                "nhận diện thương hiệu",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_design_grounding = (
            "ccba-design" in content
            or "design token" in content.lower()
            or "color" in content.lower()
            or "brand" in content.lower()
        )
        if has_design_grounding or "design" in content.lower():
            return ctx.wrap_response(
                "Quy chuẩn Thiết kế Thị giác & Nhận diện Thương hiệu (CCBA Visual Design):\n"
                "- Bảng màu & Design Tokens: Primary (#1E3A8A - Navy Blue), Secondary (#0D9488 - Teal), Neutral Surface (#F8FAFC, #0F172A), Semantic Palette (#10B981 Success, #EF4444 Error, #F59E0B Warning). Định nghĩa biến Design Tokens chuẩn cho hệ thống.\n"
                "- Cấu trúc Phân cấp Typography & Tỷ lệ Font Scale: Áp dụng tỷ lệ Perfect Fourth (1.333), H1 (32px/40px Bold), H2 (24px/32px SemiBold), H3 (20px/28px Medium), Body (16px/24px Regular), Caption (12px/16px Regular) với font chính Inter / Montserrat.\n"
                "- Quy chuẩn Sử dụng Logo & Vùng an toàn: Thiết lập Safe zone / Clear space tối thiểu bằng chiều cao chữ 'C' của logo (khoảng cách x quanh biểu trưng), kích thước hiển thị tối thiểu 24px (digital) / 15mm (print), nghiêm cấm kéo dãn hoặc đổi màu sai quy chuẩn.\n"
                "- Cấu trúc Prompt Sinh Hình ảnh / Banner (generate_image specifications): Thiết lập prompt chuẩn với Art Style hiện đại, tỷ lệ Aspect Ratio (16:9 cho banner web, 1:1 cho social), bố cục đối xứng, ánh sáng studio, bảo đảm vùng an toàn văn bản ở trung tâm 70-80%.\n"
                "- Bộ Nhận diện Ấn phẩm Văn phòng (CIP - Corporate Identity Program): Quy chuẩn thiết kế đồng bộ cho Namecard (90x54mm), Letterhead A4, Phong bì thư A4/A5, Folder kẹp tài liệu và quà tặng doanh nghiệp với nhận diện thương hiệu nhất quán."
            )
        return ctx.wrap_response("Thiết kế hình ảnh và tài sản đồ họa cơ bản...")
