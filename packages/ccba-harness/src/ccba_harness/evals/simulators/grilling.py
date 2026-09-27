"""grilling.py - Socrates Grilling & Requirements Stress-Testing Domain Simulator.

Simulates responses for grilling and requirements stress-testing skills (e.g. ccba-grilling),
including One-by-One frontier questions, codebase fact-finding, AGENTS.md invariant checks,
Visual Prototype multi-variants in single HTML, and Solution How-Tree escalations.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class GrillingDomainSimulator(BaseDomainSimulator):
    """Simulator for Socrates Grilling and frontier interviewing."""

    archetype_name = "grilling"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if "grill" in ctx.skill_name.lower():
            return True
        return any(
            k in prompt_l
            for k in [
                "grill",
                "stress-test",
                "phỏng vấn",
                "chất vấn",
                "redis",
                "adc",
                "gcloud_auth_verification",
                "visual prototype",
                "milvus",
                "pgvector",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_grilling = (
            "ccba-grilling" in content
            or "Phỏng Vấn Dồn Dập" in content
            or "Grilling Loop" in content
            or "stress-test" in content.lower()
        )
        has_one_by_one = "từng câu một" in content or "one-by-one" in content

        if has_grilling or has_one_by_one:
            return ctx.wrap_response(
                "Thực thi quy trình Grilling Socrates (Phỏng vấn dồn dập & Đối chiếu quy chuẩn):\n"
                "- Quy tắc câu hỏi: Chỉ đặt đúng một câu hỏi duy nhất (one-by-one) ở Frontier, kèm phương án đề xuất (recommended answer) của Agent trước.\n"
                "- Nguyên tắc tra cứu: Tự tra cứu dữ kiện thực tế (facts vs decisions) từ codebase, tuyệt đối không hỏi người dùng các thông tin có thể tự đọc được.\n"
                "- Đối chiếu quy chuẩn: Đối chiếu trực tiếp với AGENTS.md, chỉ ra vi phạm bất biến cốt lõi (ADR-0058 Hard Completion Lock) nếu có.\n"
                "- Visual Prototype Grilling: Tạo 3-5 variants trong 1 file HTML duy nhất với floating picker, ghi Decision Log vào NOTES.md.\n"
                "- Escalation Checkpoint: Triệu hồi /ccba-issue-tree (Solution How-Tree) để lượng hóa và xếp hạng các phương án đối đầu qua ma trận Giá trị × Độ phức tạp × Rủi ro × KISS."
            )
        return ctx.wrap_response("Hỏi một danh sách nhiều câu hỏi dồn dập...")
