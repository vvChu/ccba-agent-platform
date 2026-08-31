# Copyright (c) 2026 CCBA. All rights reserved.
"""Hierarchy State Machine & Paragraph Indentation Guardrails (OKF v2.4)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto

from ccba_legal.converters.standard.models import HierarchyState
from ccba_legal.converters.technical_formulas import GREEK_MAP


class LineActionType(Enum):
    EMIT_DIRECT = auto()
    EMIT_IN_TRONG_DO = auto()
    EMIT_LETTERED = auto()
    EMIT_LETTERED_CHILD = auto()
    EMIT_BULLET = auto()
    SUPPRESS = auto()


@dataclass
class LineFormattingAction:
    action_type: LineActionType
    content: str
    letter: str = ""


class HierarchyStateManager:
    """State-driven processor for hierarchical lists, variable explanations, and paragraphs."""

    def __init__(self) -> None:
        self.state: HierarchyState = HierarchyState.BODY_TEXT
        self.in_lettered_parent: bool = False
        self.in_bullet_category: bool = False

    def reset(self) -> None:
        """Reset state machine to plain body text."""
        self.state = HierarchyState.BODY_TEXT
        self.in_lettered_parent = False
        self.in_bullet_category = False

    def process_paragraph(
        self,
        raw_text: str,
        rendered_text: str,
    ) -> LineFormattingAction:
        """Evaluate paragraph and return appropriate formatting action."""
        text = raw_text.strip()
        rendered_p = rendered_text.strip()

        # 1. State Invariant: Exit triggers on structural breaks
        if re.match(r"^[0-9]+\.[0-9]+", text) or re.match(r"^(?:Bảng|Hình|PHỤ LỤC|Phụ lục)", text):
            self.reset()
            return LineFormattingAction(action_type=LineActionType.EMIT_DIRECT, content=rendered_p)

        # 2. State: IN_TRONG_DO (Variable explanation list)
        if self.state == HierarchyState.IN_TRONG_DO:
            # Bulleted item under 'trong đó:'
            if rendered_p.startswith(("- ", "– ", "— ", "+ ", "• ")):
                clean_b = re.sub(r"^[-–—+•]\s*", "", rendered_p).strip()
                return LineFormattingAction(action_type=LineActionType.EMIT_IN_TRONG_DO, content=clean_b)

            # Auto-exit triggers: Lead-in phrases, conditional statements, non-variable definitions
            if not text.startswith(("-", "–", "—", "+", "•")) and any(rendered_p.startswith(w) for w in [
                "Cho phép", "Đối với", "Trường hợp", "Khi", "Nếu", "Các mô men", "Các đại lượng", "Giá trị", "Chiều cao",
                "Tính toán", "Trong các", "Tại các", "Theo đó", "Với các", "Cần tiến hành", "Cốt thép", "Bê tông", "Quy tắc"
            ]):
                self.reset()
                return LineFormattingAction(action_type=LineActionType.EMIT_DIRECT, content=rendered_p)

            # Unbulleted item defining a variable
            if len(rendered_p) > 1 and not rendered_p.startswith(("#", "<a id=")):
                clean_b = rendered_p
                for g_c, g_l in GREEK_MAP.items():
                    if clean_b.startswith(g_c + " ") or clean_b.startswith(g_c + "\t"):
                        clean_b = f"${g_l}$ " + clean_b[len(g_c):].strip()
                        break
                return LineFormattingAction(action_type=LineActionType.EMIT_IN_TRONG_DO, content=clean_b)

            self.reset()

        # 3. Trigger: Start of 'trong đó:' block
        if text.lower().startswith(("trong đó:", "với:", "ở đây:")):
            self.state = HierarchyState.IN_TRONG_DO
            self.in_lettered_parent = False
            self.in_bullet_category = False
            return LineFormattingAction(action_type=LineActionType.EMIT_DIRECT, content=rendered_p)

        # 4. Lettered Clause (a), b), c)...)
        m_let = re.match(r"^([a-z])\)\s*(.+)$", text)
        if m_let:
            self.state = HierarchyState.IN_LETTERED_LIST
            self.in_bullet_category = False
            m_let_r = re.match(r"^([a-z])\)\s*(.+)$", rendered_p)
            if m_let_r:
                letter = m_let_r.group(1)
                content = m_let_r.group(2).lstrip("-–— ").strip()
                self.in_lettered_parent = content.endswith(":")
                return LineFormattingAction(
                    action_type=LineActionType.EMIT_LETTERED,
                    content=content,
                    letter=letter
                )

        # 5. Sub-item under lettered clause
        if self.state == HierarchyState.IN_LETTERED_LIST and self.in_lettered_parent:
            if text.startswith(("-", "–", "—", "+", "•")):
                clean_child = re.sub(r"^[-–—•+]\s*", "", rendered_p).strip()
                return LineFormattingAction(action_type=LineActionType.EMIT_LETTERED_CHILD, content=clean_child)

        # 6. Top-level bullet list
        if text.startswith(("- ", "– ", "— ", "• ", "-")):
            self.state = HierarchyState.IN_BULLET_LIST
            self.in_lettered_parent = False
            clean_b = re.sub(r"^[-–—•]\s*", "", rendered_p).strip()
            self.in_bullet_category = clean_b.endswith(":")
            return LineFormattingAction(action_type=LineActionType.EMIT_BULLET, content=clean_b)

        # 7. Sub-bullet under bullet category
        if self.state == HierarchyState.IN_BULLET_LIST and self.in_bullet_category:
            if text.startswith(("+", "–", "—", "-")):
                clean_child = re.sub(r"^[-–—+•]\s*", "", rendered_p).strip()
                return LineFormattingAction(action_type=LineActionType.EMIT_IN_TRONG_DO, content=clean_child)
            self.in_bullet_category = False

        # 8. Plain body text
        self.reset()
        return LineFormattingAction(action_type=LineActionType.EMIT_DIRECT, content=rendered_p)
