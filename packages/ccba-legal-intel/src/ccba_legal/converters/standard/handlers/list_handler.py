# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized List Hierarchy & Paragraph Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

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
    # Process via Hierarchy State Manager
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
