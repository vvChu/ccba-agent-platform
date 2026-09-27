"""orchestration.py - Multi-Agent Orchestration & Teamwork Domain Simulator.

Simulates responses for multi-agent coordination skills (e.g. ccba-teamwork, ccba-platform-loader),
including Single-Writer Pattern, Constitution preservation, handoff.md, verdict CLEAN, and send_message protocol.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class OrchestrationDomainSimulator(BaseDomainSimulator):
    """Simulator for multi-agent coordination, handoffs, and platform orchestration."""

    archetype_name = "orchestration"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return any(
            k in prompt_l
            for k in [
                "auditor",
                "worker",
                "orchestrat",
                "teamwork",
                "handoff",
                "forensic integrity",
                "single-writer",
                "working directory",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_orchestration = (
            "Single-Writer" in content
            or "orchestrat" in content.lower()
            or "handoff" in content.lower()
            or "progressive disclosure" in content.lower()
            or "hiến pháp" in content.lower()
            or "constitution" in content.lower()
        )
        if has_orchestration or "teamwork" in content.lower() or "ccba" in content.lower():
            return ctx.wrap_response(
                "Thực thi quy trình điều phối đa tác tử (Multi-Agent Orchestration):\n"
                "- Tuân thủ Single-Writer Pattern Invariant và cách ly thư mục làm việc riêng biệt (isolated sandbox working directory).\n"
                "- Bảo vệ Hiến pháp (Constitution Invariant) và toàn vẹn liên kết Markdown AST Link Integrity theo chuẩn Progressive Disclosure [references/](references/).\n"
                "- Lập báo cáo bàn giao handoff.md, đưa ra kết luận kiểm định verdict CLEAN, và gửi thông điệp send_message tới parent orchestrator."
            )
        return ctx.wrap_response("Xử lý tác vụ điều phối tự do không theo chuẩn single-writer...")
