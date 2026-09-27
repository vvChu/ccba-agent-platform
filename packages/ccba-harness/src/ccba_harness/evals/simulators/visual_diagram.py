"""visual_diagram.py - Visual Architecture & Diagramming Domain Simulator.

Simulates responses for diagramming skills (e.g. ccba-mermaid-diagram),
including Mermaid flowchart, sequence diagrams, Excalidraw, and Academic Grayscale styling.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class VisualDiagramDomainSimulator(BaseDomainSimulator):
    """Simulator for Mermaid and architectural diagram generation."""

    archetype_name = "visual"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return any(
            k in prompt_l
            for k in [
                "mermaid",
                "excalidraw",
                "diagram",
                "sơ đồ",
                "flowchart",
                "sequence",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_diagram = (
            "mermaid" in content.lower()
            or "excalidraw" in content.lower()
            or "diagram" in content.lower()
            or "sơ đồ" in content.lower()
        )
        if has_diagram or "ccba" in content.lower():
            return ctx.wrap_response(
                "Khởi tạo sơ đồ trực quan kiến trúc (Visual Diagram):\n"
                "```mermaid\n"
                "flowchart TD\n"
                "    A[Khởi đầu] --> B[Xử lý trung tâm]\n"
                "    B --> C{Kiểm tra điều kiện}\n"
                "    C -->|Hợp lệ| D[Hoàn tất]\n"
                "    C -->|Không hợp lệ| E[Xử lý lỗi]\n"
                "    style A fill:#f9f9f9,stroke:#333\n"
                "    style D fill:#e6ffe6,stroke:#333\n"
                "```\n"
                "Sơ đồ tuân thủ quy chuẩn Academic Grayscale và định danh theo [references/](references/)."
            )
        return ctx.wrap_response("Tạo biểu đồ thông thường...")
