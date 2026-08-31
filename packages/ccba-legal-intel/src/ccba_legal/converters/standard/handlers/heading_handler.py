# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Heading & Annotation Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def slugify_vietnamese(text: str) -> str:
    """Convert Vietnamese unicode string into clean semantic ASCII slug."""
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = text.replace("đ", "d").replace("Đ", "D")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:45].rstrip("_")


def handle_structural_heading(
    ctx: Any,
    blocks: list[tuple[str, Any]],
    i: int,
    text: str,
    rendered_p: str,
    obj: Any,
) -> int | None:
    """Handle structural headings (Table, Annex, Section, Clause, Notes, Guides).

    Returns:
        Next block index if handled, or None to continue downstream processing.
    """
    from ccba_legal.converters.standard.strategy import render_paragraph_with_runs

    # 1. Table Caption
    m_tbl = re.match(r"^(?:Bảng|BẢNG)\s+([0-9A-Za-z\.\-]+)\s*[-–—:]\s*(.+)$", text)
    if m_tbl:
        ctx.last_table_caption_num = m_tbl.group(1)
        cap_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        clean_cap = re.sub(r"^(?:Bảng|BẢNG)\s+[0-9A-Za-z\.\-]+\s*[-–—:]\s*", "", cap_rendered).strip()
        ctx.last_table_caption = f"Bảng {ctx.last_table_caption_num} - {clean_cap}"
        ctx.state_mgr.reset()
        return i + 1

    # 2. Annex Heading
    m_annex = re.match(r"^(?:Phụ\s+lục|PHỤ\s+LỤC)\s+([A-Z])(?:\s*\(([^)]+)\))?(?:\s*[-–—:]\s*(.+))?$", text, re.IGNORECASE)
    if m_annex:
        a_letter = m_annex.group(1).upper()
        a_type = (m_annex.group(2) or "").strip()
        a_title = (m_annex.group(3) or "").strip()
        if not a_type and i + 1 < len(blocks) and blocks[i + 1][0] == "p":
            ntxt = blocks[i + 1][1].text.strip()
            if ntxt.startswith("(") and ntxt.endswith(")"):
                a_type = ntxt.strip("() ").capitalize()
                i += 1
        if not a_title and i + 1 < len(blocks) and blocks[i + 1][0] == "p":
            ntxt2 = blocks[i + 1][1].text.strip()
            if not re.match(r"^[0-9A-Z]+\.", ntxt2) and not ntxt2.startswith(("Bảng", "Hình", "Phụ lục", "PHỤ LỤC")):
                a_title = ntxt2
                i += 1

        clean_title_slug = slugify_vietnamese(a_title)
        slug = f"phu_luc_{a_letter.lower()}_{clean_title_slug}" if clean_title_slug else f"phu_luc_{a_letter.lower()}"
        ctx.current_target = a_letter
        anchor = f"phu-luc-{a_letter.lower()}"
        hdr = f"## PHỤ LỤC {a_letter}" + (f"  ({a_type})" if a_type else "") + (f"  {a_title.upper()}" if a_title else "")
        ctx.annex_buffers[a_letter] = {
            "slug": slug, "title": a_title, "type": a_type or "Quy định",
            "anchor": anchor, "parts": [f'\n<a id="{anchor}"></a>\n{hdr}\n\n']
        }
        ctx.state_mgr.reset()
        return i + 1

    # 3. Section Heading (1 to 99)
    m_sec = re.match(r"^([1-9][0-9]?)\s+([^\n]+)", text)
    if m_sec and not m_sec.group(2).startswith(("-", "–", "—", ":")) and len(m_sec.group(2)) < 120 and not m_sec.group(2).lower().startswith(("đối với", "khi", "lấy", "tính", "theo", "như")):
        sec_num = m_sec.group(1)
        sec_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        sec_title = re.sub(rf"^{re.escape(sec_num)}\s+", "", sec_rendered).strip()
        ctx.emit(f'\n<a id="muc-{sec_num}"></a>\n## {sec_num}  {sec_title.upper()}\n\n')
        ctx.state_mgr.reset()
        return i + 1

    # 4. Clause Heading (e.g. 1.1, 10.2.1, F.1, G.2.1)
    m_clause = re.match(r"^([A-Z]|[1-9][0-9]?)\.([0-9]+(?:\.[0-9]+)*)\s+([^\n]+)", text)
    if m_clause:
        cl_num = f"{m_clause.group(1)}.{m_clause.group(2)}"
        cl_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        cl_title = re.sub(rf"^{re.escape(cl_num)}\s+", "", cl_rendered).strip()
        anchor = f"muc-{cl_num.lower().replace('.', '-')}"
        ctx.emit(f'\n<a id="{anchor}"></a>\n### {cl_num}  {cl_title}\n\n')
        ctx.state_mgr.reset()
        return i + 1

    # 5. Technical Notes (CHÚ THÍCH)
    if re.match(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)", text, re.IGNORECASE):
        m_num = re.search(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)", text, re.IGNORECASE)
        prefix = f"**CHÚ THÍCH {m_num.group(1)}:**" if m_num and m_num.group(1) else "**CHÚ THÍCH:**"
        rendered_note = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        rendered_note_clean = re.sub(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*", "", rendered_note, flags=re.IGNORECASE).strip()
        ctx.emit(f"{prefix} {rendered_note_clean}\n\n")
        ctx.state_mgr.reset()
        return i + 1

    # 6. Diagram Guides (CHÚ DẪN)
    if re.match(r"^(?:CHÚ\s+DẪN|Chú\s+dẫn)", text, re.IGNORECASE):
        ctx.state_mgr.reset()
        clean_cd = text.strip()
        ctx.emit(f"**{clean_cd}**\n\n")
        return i + 1

    # 7. Numbered guide list (e.g. 1 - Cốt thép dọc; 2 - Dầm phụ)
    if re.match(r"^[0-9]+\s*[-–—]\s*", text) and not re.match(r"^[0-9]+\.[0-9]+", text):
        ctx.state_mgr.reset()
        ctx.emit(f"{rendered_p}\n\n")
        return i + 1

    # 8. Unit Note right before/after table
    if re.match(r"^(?:\t|\s)*(?:Đơn vị tính(?:\s+bằng)?|ĐƠN VỊ TÍNH)\s*(.+)$", text, re.IGNORECASE):
        unit_txt = re.sub(r"^(?:Đơn vị tính(?:\s+bằng)?|ĐƠN VỊ TÍNH)\s*", "", text.strip(), flags=re.IGNORECASE).strip()
        ctx.last_table_unit = f"Đơn vị tính bằng {unit_txt}"
        ctx.state_mgr.reset()
        return i + 1

    return None
