# Copyright (c) 2026 CCBA. All rights reserved.
"""Document block extraction, header location, and preamble processing for Technical Standards."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from docx.table import Table
from docx.text.paragraph import Paragraph

from ccba_legal.converters.standard.sanitizers import render_paragraph_with_runs

if TYPE_CHECKING:
    from ccba_legal.converters.standard.strategy import StandardConversionContext

__all__ = [
    "ROMAN_TO_INT",
    "extract_document_blocks",
    "find_normative_start_index",
    "find_standard_header_start_index",
    "parse_part_number",
    "process_preamble_blocks",
]

ROMAN_TO_INT: dict[str, int] = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
}


def parse_part_number(raw: str) -> int | None:
    """Parse part number from Arabic digit or Roman numeral string."""
    if raw.isdigit():
        return int(raw)
    return ROMAN_TO_INT.get(raw.upper())


def extract_document_blocks(doc: Any) -> list[tuple[str, Any]]:
    """Traverse DOCX body elements in exact XML document order."""
    blocks: list[tuple[str, Any]] = []
    for child in doc.element.body:
        if child.tag.endswith("p"):
            blocks.append(("p", Paragraph(child, doc)))
        elif child.tag.endswith("tbl"):
            blocks.append(("tbl", Table(child, doc)))
    return blocks


def find_standard_header_start_index(blocks: list[tuple[str, Any]]) -> int:
    """Find index where actual Standard begins, skipping circular administrative wrapper."""
    first_few_texts: list[str] = []
    for b_type, obj in blocks[:15]:
        if b_type == "p":
            first_few_texts.append(obj.text.strip())
        elif b_type == "tbl":
            first_few_texts.append(" ".join(cell.text for cell in obj.rows[0].cells))
    combined_header = " ".join(first_few_texts).upper()
    has_circular_wrapper = any(
        k in combined_header
        for k in [
            "THÔNG TƯ",
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
            "BAN HÀNH KÈM THEO THÔNG TƯ",
            "CĂN CỨ NGHỊ ĐỊNH",
        ]
    )
    if not has_circular_wrapper:
        return 0

    for idx, (b_type, obj) in enumerate(blocks):
        if idx == 0:
            continue
        if b_type == "p":
            t = obj.text.strip().upper()
            if (
                re.match(r"^(?:QCVN|TCVN)\s+[0-9]+", t)
                or t in ("TIÊU CHUẨN QUỐC GIA", "QUY CHUẨN KỸ THUẬT QUỐC GIA")
                or t.startswith("QUY CHUẨN KỸ THUẬT QUỐC GIA")
            ):
                return idx
    return 0


def find_normative_start_index(blocks: list[tuple[str, Any]], start_from: int = 0) -> int:
    """Locate exact start index of normative body (Section 1), skipping Table of Contents."""
    in_toc = False
    for idx in range(start_from, len(blocks)):
        b_type, obj = blocks[idx]
        if b_type == "p":
            txt = obj.text.strip()
            txt_u = txt.upper()
            if txt_u in ("MỤC LỤC", "## MỤC LỤC", "TABLE OF CONTENTS") or txt_u.startswith(
                "MỤC LỤC"
            ):
                in_toc = True
                continue
            if in_toc:
                is_end = False
                if txt.lower().startswith(("lời nói đầu", "lời giới thiệu")):
                    for nxt_idx in range(idx + 1, min(idx + 5, len(blocks))):
                        if blocks[nxt_idx][0] == "p" and blocks[nxt_idx][1].text.strip():
                            nxt_t = blocks[nxt_idx][1].text.strip()
                            if not re.match(
                                r"^(?:Lời giới thiệu|\d+[\.\s]|Phụ lục|Thư mục)",
                                nxt_t,
                                re.IGNORECASE,
                            ):
                                is_end = True
                            break
                elif txt_u in ("TIÊU CHUẨN QUỐC GIA", "QUY CHUẨN KỸ THUẬT QUỐC GIA"):
                    is_end = True
                if is_end:
                    in_toc = False

            if not in_toc and re.match(
                r"^1[\.\s]+(?:QUY ĐỊNH CHUNG|PHẠM VI ÁP DỤNG|YÊU CẦU CHUNG|[A-ZÀ-Ỹ])\b",
                txt,
                re.IGNORECASE,
            ):
                has_substantive = False
                for nxt_idx in range(idx + 1, min(idx + 15, len(blocks))):
                    if blocks[nxt_idx][0] == "p" and blocks[nxt_idx][1].text.strip():
                        nxt_t = blocks[nxt_idx][1].text.strip()
                        if (
                            re.match(r"^(?:\(\d+\)|\d+\)|[\-\+•]|(?:[a-z]\)))", nxt_t)
                            or len(nxt_t.split()) > 15
                        ):
                            has_substantive = True
                            break
                if has_substantive:
                    return idx
    return start_from


def process_preamble_blocks(
    ctx: StandardConversionContext,
    blocks: list[tuple[str, Any]],
    std_start_idx: int,
    start_idx: int,
) -> None:
    """Process front matter and preamble blocks (headers, Lời nói đầu, Mục lục) preceding Section 1."""
    if start_idx <= std_start_idx:
        return

    preamble_parts: list[str] = []
    in_preamble_toc = False
    for p_idx in range(std_start_idx, start_idx):
        b_type, obj = blocks[p_idx]
        if b_type != "p":
            continue
        t = obj.text.strip()
        if not t:
            continue
        t_u = t.upper()
        if t_u in ("MỤC LỤC", "## MỤC LỤC", "TABLE OF CONTENTS"):
            in_preamble_toc = True
            continue
        if in_preamble_toc:
            is_end = False
            if t.lower().startswith("lời nói đầu"):
                for nxt_idx in range(p_idx + 1, min(p_idx + 5, len(blocks))):
                    if blocks[nxt_idx][0] == "p" and blocks[nxt_idx][1].text.strip():
                        nxt_t = blocks[nxt_idx][1].text.strip()
                        if not re.match(
                            r"^(?:Lời giới thiệu|\d+[\.\s]|Phụ lục|Thư mục)", nxt_t, re.IGNORECASE
                        ):
                            is_end = True
                        break
            elif t_u in ("TIÊU CHUẨN QUỐC GIA", "QUY CHUẨN KỸ THUẬT QUỐC GIA"):
                is_end = True
            if is_end:
                in_preamble_toc = False
            else:
                continue

        m_p_q = re.match(r"^(?:QCVN|TCVN)\s+[0-9]+-(\d+):[0-9]+(?:\/[A-Z0-9]+)?$", t, re.IGNORECASE)
        m_p_p = re.match(r"^(?:PHẦN|Phần)\s+([0-9]+|[IVXLCDM]+)\b", t, re.IGNORECASE)
        if m_p_q:
            ctx.current_part = f"p{int(m_p_q.group(1)):02d}"
        elif m_p_p:
            p_val = parse_part_number(m_p_p.group(1))
            if p_val is not None:
                ctx.current_part = f"p{p_val:02d}"

        rendered_t = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        if t.upper() in ("TIÊU CHUẨN QUỐC GIA", "QUY CHUẨN KỸ THUẬT QUỐC GIA"):
            preamble_parts.append(f"# {rendered_t}\n\n")
        elif re.match(r"^(?:TCVN|QCVN)", t, re.IGNORECASE):
            preamble_parts.append(f"**{rendered_t}**\n\n")
        elif t.lower().startswith("lời nói đầu"):
            preamble_parts.append(f"## {rendered_t}\n\n")
        elif t.lower().startswith("mục lục"):
            preamble_parts.append(f"## {rendered_t}\n\n")
        else:
            preamble_parts.append(f"{rendered_t}\n\n")

    if preamble_parts:
        ctx.body_md_parts.append("".join(preamble_parts) + "\n---\n\n")
