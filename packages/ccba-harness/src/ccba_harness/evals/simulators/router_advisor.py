"""router_advisor.py - Read-Only Advisory & Routing Skill Domain Simulator.

Offline deterministic simulator for unit-test plumbing of the router_advisor
archetype (e.g. ccba-ask). Never used for production NightlyTunerDaemon runs.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext

_ROUTER_ADVISOR_SKILLS: frozenset[str] = frozenset({"ccba-ask", "router_advisor", "router-advisor"})

_ROUTER_PROMPT_KEYWORDS: tuple[str, ...] = (
    "/ccba-ask",
    "built-in /plan",
    "tiếp theo nên làm gì",
    "/ccba-wayfinder",
)


class RouterAdvisorDomainSimulator(BaseDomainSimulator):
    """Offline plumbing simulator for read-only routing and consultation skills."""

    archetype_name = "router_advisor"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in _ROUTER_ADVISOR_SKILLS:
            return True
        return any(k in prompt_l for k in _ROUTER_PROMPT_KEYWORDS)

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt_l = str(item.input_prompt).lower()
        if "youtube" in prompt_l or "brainstorm" in prompt_l:
            return ctx.wrap_response(
                "CHẾ ĐỘ TƯ VẤN CHỈ ĐỌC (READ-ONLY — KHÔNG GHI TỆP, MENTION != INVOKE):\n\n"
                "1. Khuyến nghị chính (Mode B — Reframe & Hybrid Rhythm):\n"
                "- Áp dụng kỹ thuật Reframe lật ngược giả định; với nguồn YouTube, trích xuất qua `/ccba-youtube-learn` trước khi hội tụ.\n"
                "- Đích bàn giao trung lập: `/ccba-wayfinder`, `/ccba-grilling` hoặc `/ccba-to-spec`.\n\n"
                "2. Trạng thái phiên: Tiếp tục thảo luận ngắn tại đây hoặc mở phiên mới trước khi triển khai.\n\n"
                "3. Lệnh gợi ý copy-paste:\n"
                "```text\n/ccba-grilling\n```\n"
                "Tham chiếu: [references/brainstorm_techniques.md](references/brainstorm_techniques.md)."
            )

        return ctx.wrap_response(
            "CHẾ ĐỘ TƯ VẤN CHỈ ĐỌC (READ-ONLY — KHÔNG GHI TỆP, MENTION != INVOKE):\n\n"
            "1. Khuyến nghị chính (State-Aware Routing & Built-in vs CCBA):\n"
            "- Phân định rõ `/plan`, `/grill-me`, `/learn` (built-in) với `/ccba-new-feature`, `/ccba-grilling`, `/ccba-release-feature`, `/ccba-update-spoke`, `/ccba-session-retrospective`, `/ccba-wayfinder`.\n"
            "- Giữ nguyên tắc chỉ đọc (read-only), tuyệt đối không thực thi hay ghi tệp khi người dùng chỉ hỏi so sánh.\n\n"
            "2. Trạng thái phiên (Phase Boundary): Tiếp tục tại đây cho hỏi đáp ngắn, hoặc mở phiên mới (Clear Context) trước khi sang pha triển khai mới.\n\n"
            "3. Lệnh copy-paste 1-click:\n"
            "```text\n/ccba-new-feature\n```\n"
            "Tham chiếu: [references/builtin_vs_ccba.md](references/builtin_vs_ccba.md) và [references/phase_boundaries.md](references/phase_boundaries.md)."
        )
