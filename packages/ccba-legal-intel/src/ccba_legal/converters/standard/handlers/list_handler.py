# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized List Hierarchy & Paragraph Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.converters.standard.state_manager import LineActionType


def handle_list_and_paragraph(
    ctx: Any,
    blocks: list[tuple[str, Any]],
    i: int,
    text: str,
    rendered_p: str,
    obj: Any,
) -> int:
    """Handle lettered items, bullet lists, variable glossary, and regular paragraphs via State Manager."""
    # 1. Check if this is a sub-figure caption immediately preceding a Figure card (e.g. a) Lực dọc N... before Hình 8)
    m_let = re.match(r"^([a-z])\)\s*(.+)$", text)
    if m_let and i + 4 < len(blocks):
        is_subfig_caption = False
        for next_idx in range(i + 1, min(i + 5, len(blocks))):
            next_b_type, next_obj = blocks[next_idx]
            if next_b_type == "p" and hasattr(next_obj, "text") and re.match(r"^(?:Hình|HÌNH)\s+[0-9A-Za-z\.\-]+", next_obj.text.strip()):
                is_subfig_caption = True
                break
        if is_subfig_caption:
            return i + 1

    # 2. Process via Hierarchy State Manager
    action = ctx.state_mgr.process_paragraph(text, rendered_p)

    if action.action_type == LineActionType.EMIT_LETTERED:
        ctx.emit(f"{action.letter}) \\- {action.content}\n\n")
    elif action.action_type == LineActionType.EMIT_LETTERED_CHILD:
        ctx.emit(f"&nbsp;&nbsp;&nbsp;&nbsp;\\- {action.content}\n\n")
    elif action.action_type == LineActionType.EMIT_BULLET:
        ctx.emit(f"&nbsp;&nbsp;\\- {action.content}\n\n")
    elif action.action_type == LineActionType.EMIT_IN_TRONG_DO:
        ctx.emit(f"&nbsp;&nbsp;&nbsp;&nbsp;\\- {action.content}\n\n")
    elif action.action_type == LineActionType.EMIT_DIRECT:
        ctx.emit(f"{action.content}\n\n")

    return i + 1
