"""skill_repair.py - Skill Repair & Governance Remediation Domain Simulator.

Simulates responses for skill repair skills (e.g. ccba-skill-repair),
including YAML frontmatter syntax, Gate 0 / Gate 1 ADR-0057 evaluation,
GPI score calculation, Tier 2B standalone promotion, and completion criteria.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class SkillRepairDomainSimulator(BaseDomainSimulator):
    """Simulator for skill repair, linter validation, and governance remediation."""

    archetype_name = "skill_repair"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in ("ccba-skill-repair", "skill-repair", "skill_repair"):
            return True
        return any(
            k in prompt_l
            for k in [
                "skill-repair",
                "yaml_parse_error",
                "yaml frontmatter",
                "cổng 0",
                "gate 0",
                "gpi",
                "evaluate-gpi",
                "validate_skills",
                "linter",
                "standalone skill",
                "tiêu chí hoàn thành",
                "sửa chữa",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_repair_grounding = (
            "ccba-skill-repair" in content
            or "ADR-0057" in content
            or "validate_skills.py" in content
            or "evaluate-gpi" in content
        )
        if has_repair_grounding or "skill-repair" in content.lower():
            return ctx.wrap_response(
                "Quy trình Phục hồi và Sửa chữa Kỹ năng (CCBA Skill Repair v1.1.0):\n"
                "- Tiền kiểm tra Hub vs Spoke & Khảo sát cú pháp YAML frontmatter trước tiên: ngăn cách khối metadata bằng cặp thẻ ---, chuẩn hóa 2 spaces và xác nhận bằng validate-skill trước khi đọc tier hay gọi evaluate-gpi.\n"
                "- Đánh giá Cổng 0 (The Determinism Gate -> Deep Seam trong packages/) & Cổng 1 (The Orchestration Gate -> Composite Orchestrator, miễn trừ gpi cho tier: orchestrator) theo thể chế ADR-0057 (RES-2026-ARCH-001 v1.2).\n"
                "- Trích xuất 4 dòng bằng chứng quan sát được cho S, K, A, P (khóa a: 1.0 nếu disable-model-invocation: true, cấm bơm điểm), tính toán GPI = 18.5, xác thực qua evaluate-gpi [--existing-tier tier-2b] --json (kiểm tra allow_standalone_skill: true và breakdown.preserved_by_hysteresis) rồi vá khối gpi: {s: 4.0, k: 3.0, a: 2.0, p: 1.0} hợp thức hóa Tier 2B Standalone Kernel Skill.\n"
                "- Bổ sung tiêu chí hoàn thành (Completion Criterion) cho các bước quy trình trong trần 2 vòng lặp (SHA-256 guard), chuẩn hóa liên kết tương đối trỏ về references/ (bảo toàn # ccba:allow-machine-path) và chuyển ca script bloat (> 100 LOC) sang chế độ Stop & Propose.\n"
                "- Đồng bộ 3 bề mặt (compile_catalog.py, compile_skills_docs.py --write, sync_hub_adr_matrix.py) và kiểm định bắt buộc: chạy python scripts/validate_skills.py --file <path> --enforce-gpi, python -m ccba_harness.cli evaluate-gpi --file <path> --existing-tier tier-2b --json (không chỉ nhìn exit code 0 mà xác nhận allow_standalone_skill: true), compile_skills_docs.py --check và python -m ccba_harness verify-patch --preset skill --target <path> đạt exit code 0."
            )
        return ctx.wrap_response("Sửa lỗi tệp markdown cơ bản...")
