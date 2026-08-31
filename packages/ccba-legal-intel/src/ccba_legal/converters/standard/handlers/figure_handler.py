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
        img_path = f"figures/images/hinh_{fig_slug}.png"

        # Extract preceding CHÚ DẪN / CHÚ THÍCH blocks to place them below the image
        chudan_parts: list[str] = []
        parts_buf = getattr(ctx, "active_parts", getattr(ctx, "body_md_parts", []))
        while parts_buf:
            last = parts_buf[-1].strip()
            if not last or last.startswith("<!--"):
                parts_buf.pop()
                continue
            if (
                "CHÚ DẪN" in last
                or "CHÚ THÍCH" in last
                or re.match(r"^[0-9A-Za-z\.'\-]+\s*[-–—:]", last)
                or last.startswith("&nbsp;&nbsp;\\-")
            ):
                chudan_parts.insert(0, parts_buf.pop())
            else:
                break

        full_chudan = "".join(chudan_parts)
        if "CHÚ DẪN" not in full_chudan and "CHÚ THÍCH" not in full_chudan:
            for p in chudan_parts:
                parts_buf.append(p)
            chudan_parts = []

        ctx.emit(f'\n<a id="{anchor}"></a>\n\n<p align="center">\n\n![Hình {fig_num}]({img_path})\n\n</p>\n\n')

        if chudan_parts:
            for p in chudan_parts:
                ctx.emit(p)
            if not full_chudan.endswith("\n\n"):
                ctx.emit("\n\n")

        ctx.emit(f'<p align="center"><strong>Hình {fig_num} — {fig_title}</strong></p>\n\n')
        ctx.state_mgr.reset()
        return i + 1

    return None
