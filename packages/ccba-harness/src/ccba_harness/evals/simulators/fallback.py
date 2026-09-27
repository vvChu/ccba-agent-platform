"""fallback.py - Generic Fallback & Golden Answer Domain Simulator.

Provides fallback simulation when no specific domain simulator matches,
supporting item golden answers and lean structural architecture responses.
"""

from __future__ import annotations

import json
import re

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class FallbackDomainSimulator(BaseDomainSimulator):
    """Fallback simulator returning golden answers or lean structural scaffolding."""

    archetype_name = "general"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        return True

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        if item.golden_answer is not None:
            return (
                item.golden_answer
                if isinstance(item.golden_answer, str)
                else json.dumps(item.golden_answer, ensure_ascii=False)
            )

        content = ctx.content
        has_links = bool(
            re.search(
                r"\[([^\]]+)\]\(([^)]+)\)|progressive disclosure|references/|tham chiếu",
                content,
                re.IGNORECASE,
            )
        )
        if has_links:
            body = (
                "Thực thi quy trình có cấu trúc (Lean Structural Architecture):\n"
                "- Bộc lộ dần (Progressive Disclosure): Tham chiếu chi tiết tại [Tài liệu hướng dẫn](references/guide.md).\n"
                "- Cấu trúc tinh gọn và loại bỏ hoàn toàn rác dữ liệu (Anti-Debris Invariant)."
            )
        else:
            body = "Thực thi quy trình chuẩn mực: tham chiếu tài liệu chi tiết tại [Tài liệu hướng dẫn](references/guide.md)."

        return ctx.wrap_response(body)
