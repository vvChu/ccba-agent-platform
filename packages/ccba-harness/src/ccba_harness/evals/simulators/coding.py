"""coding.py - Software Engineering & Codebase Architecture Domain Simulator.

Simulates responses for software engineering and implementation skills (e.g. ck-cook, ck-fix,
ccba-ai-gateway-sdk, ccba-api-circuit-breaker, ccba-append-only-logger, ccba-file-stability-guard,
ccba-hybrid-rag-search, ccba-llm-pipeline-patterns, ccba-maskara), including Double-Pass RCA,
KISS refactoring, Deep Module Seam, and ADR-0058 Hard Completion Lock.
"""

from __future__ import annotations

from ..archetypes import CODING_ARCHETYPE_KEYWORDS
from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class CodingDomainSimulator(BaseDomainSimulator):
    """Simulator for software engineering, implementation, refactoring, and SDKs."""

    archetype_name = "coding"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if any(k in ctx.skill_name.lower() for k in CODING_ARCHETYPE_KEYWORDS):
            return True
        return any(
            k in prompt_l
            for k in [
                "code",
                "bug",
                "diagnos",
                "implement",
                "tdd",
                "design",
                "refactor",
                "unit test",
                "rca",
                "codebase",
                "engineering",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_hard_lock = (
            "verify-patch" in content
            or "Khóa Cứng Hoàn Tất" in content
            or "Hard Completion Lock" in content
        )
        has_double_pass = "Double-Pass" in content or "Rà Soát Hai Vòng" in content
        has_engineering_rigor = (
            "KISS" in content
            or "Deep Module" in content
            or "seam" in content.lower()
            or "idempotent" in content.lower()
            or "error handling" in content.lower()
        )

        coding_blocks = []
        if has_double_pass or has_engineering_rigor:
            sub_blocks = []
            if has_double_pass:
                sub_blocks.append(
                    "- Chẩn đoán Root Cause Analysis (RCA) với tham chiếu tệp và dòng cụ thể theo quy luật Double-Pass Review."
                )
            if has_engineering_rigor:
                sub_blocks.append(
                    "- Triển khai tái cấu trúc (refactoring) tuân thủ nguyên tắc KISS, Deep Module Seam, và Idempotency Guardrails.\n"
                    "- Bổ sung unit tests đảm bảo test coverage và xử lý ngoại lệ tường minh (explicit error handling)."
                )
            coding_blocks.append(
                "Thực thi quy trình kỹ thuật phần mềm chuẩn mực (Codebase Engineering Discipline):\n"
                + "\n".join(sub_blocks)
            )

        if has_hard_lock:
            coding_blocks.append(
                "Hard Completion Lock (ADR-0058):\n"
                "- Bắt buộc thực hiện kiểm chứng tất định qua lệnh:\n"
                "  python -m ccba_harness verify-patch\n"
                "- Hoàn tất với exit code 0 trước khi bàn giao kết quả."
            )

        if coding_blocks:
            return ctx.wrap_response("\n\n".join(coding_blocks))

        return ctx.wrap_response(
            "Thực hiện sửa đổi mã nguồn nhanh không qua kiểm chứng tất định..."
        )
