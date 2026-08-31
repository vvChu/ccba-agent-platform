# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Figure Card & Diagram Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.figure_extractor import render_markdown_figure_card


def handle_figure_card(
    ctx: Any,
    text: str,
    i: int,
) -> int | None:
    """Handle Figure Card triggers (e.g. Hình 1 - ...)."""
    m_fig = re.match(r"^(?:Hình|HÌNH)\s+([0-9A-Za-z\.\-]+)\s*[-–—:]\s*(.+)$", text)
    if m_fig:
        fig_num = m_fig.group(1)
        fig_title = m_fig.group(2).strip()
        fig_slug = fig_num.lower().replace(".", "_")
        anchor = f"hinh-{fig_slug}"
        fig_entry = {
            "tag": fig_num,
            "title": fig_title,
            "anchor": anchor,
            "image_relpath": f"figures/images/hinh_{fig_slug}.png",
            "geometry_rules": {},
        }

        ctx.emit(render_markdown_figure_card(fig_entry))
        ctx.state_mgr.reset()
        return i + 1

    return None
