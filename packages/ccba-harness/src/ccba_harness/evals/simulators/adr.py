"""adr.py - Architecture Decision Record (ADR) Lifecycle Domain Simulator.

Simulates responses for ADR governance skills (e.g. ccba-adr-lifecycle),
including Scaffolding, Status Cascading, Living Traceability Matrix, and CI Parity Gate.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class AdrLifecycleDomainSimulator(BaseDomainSimulator):
    """Simulator for Architecture Decision Record lifecycle governance."""

    archetype_name = "adr"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if "adr" in ctx.skill_name.lower():
            return True
        return any(
            k in prompt_l
            for k in [
                "adr",
                "architecture decision",
                "traceability_matrix",
                "scaffolding",
                "status cascading",
                "ci parity",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_adr_grounding = (
            "ccba-adr-lifecycle" in content
            or "Quản Trị Vòng Đời Quyết Định Kiến Trúc" in content
            or "docs/adr/" in content
            or "HUB-ADR" in content
        )
        if has_adr_grounding or "adr" in content.lower():
            return ctx.wrap_response(
                "Quản trị Vòng đời Quyết định Kiến trúc (ADR Lifecycle Governance):\n"
                "- Scaffolding: Khởi tạo tệp docs/adr/00XX-<slug>.md với đầy đủ YAML Frontmatter (id: HUB-ADR-00XX hoặc SPOKE-ADR-00XX, status: ACCEPTED, pillar) cùng các mục Context, Decision, Consequences, Invariants.\n"
                "- Status Cascading: Cập nhật status SUPERSEDED cho ADR cũ và bổ sung liên kết hai chiều superseded_by / supersedes.\n"
                "- Matrix Sync: Quét và cập nhật Living Traceability Matrix docs/adr/TRACEABILITY_MATRIX.md cùng bảng mục lục README.md.\n"
                "- CI Parity Gate: Kiểm tra tính toàn vẹn và chống lệch pha tài liệu qua python scripts/validate_adr_traceability.py."
            )
        return ctx.wrap_response("Tạo file markdown ghi chép kiến trúc thông thường...")
