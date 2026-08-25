"""Native Technical Standard (TCVN / QCVN) Strategy Converter (ADR 0030, ADR 0031)."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.converters.table_extractor import classify_and_extract_tables
from ccba_legal.converters.technical_formulas import FORMULAS_MAP, GREEK_MAP, INLINE_SYMBOLS_MAP
from ccba_legal.converters.unit_normalizer import normalize_units_and_math
from ccba_legal.figure_extractor import (
    AERODYNAMIC_FIGURES_GEOMETRY,
    extract_docx_figures,
    render_markdown_figure_card,
)
from ccba_legal.formula_harvester import harvest_docx_formula_images
from ccba_legal.gold_standard import generate_bundle_ast_and_qa, inject_semantic_anchors


def slugify_vietnamese(text: str) -> str:
    """Convert Vietnamese unicode string into clean semantic ASCII slug."""
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = text.replace("đ", "d").replace("Đ", "D")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:45].rstrip("_")


def sanitize_prose_greeks_and_variables(text: str) -> str:
    """Convert unformatted Greek symbols, macrons, and standard variables into KaTeX math mode."""
    nfd = unicodedata.normalize("NFD", text)

    def _macron_repl(m: re.Match) -> str:
        base = m.group(1)
        base_latex = GREEK_MAP.get(base, base)
        return f"$\\bar{{{base_latex}}}$"

    res = re.sub(r"([a-zA-Z\u0370-\u03ff])[\u0304\u0305]", _macron_repl, nfd)
    text = unicodedata.normalize("NFC", res).replace("ℓ", r"$\ell$")

    for g_char, g_latex in GREEK_MAP.items():
        pattern = r"(?<!\$)\b" + g_char + r"([a-zA-Z0-9]+)\b(?!\$)"
        text = re.sub(pattern, lambda m, gl=g_latex: f"${gl}_{{{m.group(1)}}}$", text)
        pattern_alone = r"(?<![\$\w])" + g_char + r"(?![\$\w])"
        text = re.sub(pattern_alone, lambda m, gl=g_latex: f"${gl}$", text)

    for var in ["qk,t", "Qk,t", "qk,qper", "Wk", "W0", "Gk", "Qk", "QL", "Qt", "Ad", "ze", "zs", "Gf"]:
        k_var = var.replace(",", "_{").replace("0", "_0")
        if "_" in k_var and not k_var.endswith("}"):
            k_var += "}"
        elif len(var) > 1 and not "_" in k_var:
            k_var = f"{var[0]}_{{{var[1:]}}}"
        text = re.sub(rf"(?<!\$)\b{var}\b(?!\$)", f"${k_var}$", text)

    return text


def render_paragraph_with_runs(p: Any, rid_to_katex: dict[str, str] | None = None) -> str:
    """Render a docx paragraph while preserving sub/superscripts and resolving inline image symbols as clean KaTeX tokens."""
    runs = p.runs
    if not runs:
        return p.text.strip()

    grouped: list[tuple[str, str]] = []
    for r in runs:
        xml = r._r.xml
        m_rid = re.search(r'r:(?:id|embed)="([^"]+)"', xml)
        if m_rid:
            rid = m_rid.group(1)
            if rid in INLINE_SYMBOLS_MAP:
                grouped.append(("norm", f"${INLINE_SYMBOLS_MAP[rid]}$"))
                continue
            if rid_to_katex and rid in rid_to_katex:
                k_sym = rid_to_katex[rid]
                if not k_sym.startswith("<!-- DIAGRAM"):
                    grouped.append(("norm", f"${k_sym.strip('$ ')}$"))
                    continue
        t = r.text
        if not t:
            continue
        is_sub = "subscript" in xml or (r.font.subscript is True)
        is_sup = "superscript" in xml or (r.font.superscript is True)
        mode = "sub" if is_sub else ("sup" if is_sup else "norm")
        if grouped and grouped[-1][0] == mode:
            grouped[-1] = (mode, grouped[-1][1] + t)
        else:
            grouped.append((mode, t))

    out_tokens: list[str] = []
    for mode, text in grouped:
        if mode in ("sub", "sup"):
            clean_t = text.strip()
            if not clean_t:
                out_tokens.append(text)
                continue
            trailing_comma = ", " if clean_t.endswith(",") else ""
            clean_t = clean_t.rstrip(",").strip()
            for g_char, g_latex in GREEK_MAP.items():
                clean_t = clean_t.replace(g_char, g_latex)
            wrap = f"_{{{clean_t}}}" if mode == "sub" else f"^{{{clean_t}}}"
            out_tokens.append(f"${wrap}${trailing_comma}")
        else:
            out_tokens.append(text)

    res = "".join(out_tokens)
    res = re.sub(r"([a-zA-ZÀ-ɏẠ-ỹͰ-Ͽ]+)\$(_\{[^}]+\}|_[a-zA-Z0-9,]+|\^\{[^}]+\}|\^[a-zA-Z0-9]+)\$", r"$\1\2$", res)
    res = re.sub(r"\$([^$]+)\$", lambda m: f"${''.join(GREEK_MAP.get(c, c) for c in m.group(1))}$", res)
    res = res.replace("$$", "").replace("$_$", "").replace("$^$", "")
    res = re.sub(r"\$([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9\u0370-\u03FF_,\{\}\^\\0-9]+)\$([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])", r"$\1$ \2", res)
    return res.strip()


def calculate_emsp_padding(vis_len: int) -> str:
    """Calculate accurate typography &emsp; padding based on symbol visual width."""
    if vis_len <= 1:
        return '&emsp;&emsp;&emsp;&emsp;&emsp;'
    elif vis_len <= 2:
        return '&emsp;&emsp;&emsp;&emsp;'
    elif vis_len <= 3:
        return '&emsp;&emsp;&emsp;'
    elif vis_len <= 5:
        return '&emsp;&emsp;'
    return '&emsp;'


def format_symbol_cell_runs(cell: Any) -> str:
    """Format Section 3.2 docx symbol cells into exact KaTeX math variables."""
    grouped: list[tuple[str, str]] = []
    for p in cell.paragraphs:
        for r in p.runs:
            t = r.text
            if not t:
                continue
            is_sub = "subscript" in r._r.xml or (r.font.subscript is True)
            is_sup = "superscript" in r._r.xml or (r.font.superscript is True)
            mode = "sub" if is_sub else ("sup" if is_sup else "norm")
            if grouped and grouped[-1][0] == mode:
                grouped[-1] = (mode, grouped[-1][1] + t)
            else:
                grouped.append((mode, t))

    parts: list[str] = []
    for mode, text in grouped:
        t_mapped = text
        for g_char, g_latex in GREEK_MAP.items():
            t_mapped = t_mapped.replace(g_char, g_latex)
        clean_t = text.strip()
        if mode == "sub":
            parts.append(f"_{{{clean_t}}}")
        elif mode == "sup":
            parts.append(f"^{{{clean_t}}}")
        else:
            parts.append(t_mapped)
    return f"${''.join(parts).strip()}$"


def render_table_markdown(table: Any, rid_to_katex: dict[str, str] | None = None) -> tuple[str, list[str], list[list[str]]]:
    """Render a docx Table object as a GitHub Flavored Markdown table with smart column alignment and footnote extraction."""
    grid: list[list[str]] = []
    footnotes: list[str] = []

    for row in table.rows:
        row_rendered: list[str] = []
        for cell in row.cells:
            cell_p_rendered: list[str] = []
            for p in cell.paragraphs:
                p_r = render_paragraph_with_runs(p, rid_to_katex=rid_to_katex)
                if p_r:
                    if p_r.startswith(("- ", "– ", "— ", "• ")):
                        p_r = "&nbsp;&nbsp;\- " + p_r.lstrip("-–—• ")
                    elif p_r.startswith(("+ ", "+")):
                        p_r = "&nbsp;&nbsp;&nbsp;&nbsp;\+ " + p_r.lstrip("+ ")
                    cell_p_rendered.append(p_r)
            row_rendered.append("<br>".join(cell_p_rendered))

        clean_row: list[str] = []
        for val in row_rendered:
            if not clean_row or val != clean_row[-1]:
                clean_row.append(val)

        if not clean_row or not any(clean_row):
            continue

        first_cell = clean_row[0].strip()
        if re.match(r"^(?:<br>)*\s*(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)", first_cell, re.IGNORECASE):
            fn_text = "<br>".join([c for c in clean_row if c.strip()])
            fn_clean = re.sub(r"^(?:<br>)*\s*(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*", "", fn_text, flags=re.IGNORECASE).strip()
            footnotes.append(f"**CHÚ THÍCH:** {fn_clean}")
            continue

        grid.append(clean_row)

    if not grid:
        return ("", footnotes, [])

    max_cols = max(len(r) for r in grid)
    normalized_grid: list[list[str]] = [r + [""] * (max_cols - len(r)) for r in grid]

    alignments: list[str] = []
    for c_idx in range(max_cols):
        vals = [r[c_idx] for r in normalized_grid[1:] if r[c_idx].strip()]
        is_num = all(re.match(r"^[0-9\.,\-\+\s%±]+$", v.replace("<br>", " ")) for v in vals) if vals else False
        alignments.append(":---:" if is_num else ":---")

    lines: list[str] = ["| " + " | ".join(normalized_grid[0]) + " |", "| " + " | ".join(alignments) + " |"]
    for r in normalized_grid[1:]:
        lines.append("| " + " | ".join(r) + " |")

    return ("\n".join(lines) + "\n\n", footnotes, normalized_grid)


@dataclass
class StandardConversionContext:
    """State machine container for technical standard conversions."""
    bundle_dir: Path
    output_filename: str | None
    rid_to_katex: dict[str, str] = field(default_factory=dict)
    body_md_parts: list[str] = field(default_factory=list)
    annex_buffers: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_target: str = "main"
    last_table_caption: str = ""
    last_table_caption_num: str = ""
    in_trong_do: bool = False
    tables_extracted: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, chunk: str) -> None:
        """Emit a markdown chunk to either the main body buffer or the active modular annex buffer."""
        if self.current_target == "main":
            self.body_md_parts.append(chunk)
        else:
            self.annex_buffers[self.current_target]["parts"].append(chunk)


def _extract_document_blocks(doc: Any) -> list[tuple[str, Any]]:
    """Traverse DOCX body elements in exact XML document order."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    blocks: list[tuple[str, Any]] = []
    for child in doc.element.body:
        if child.tag.endswith("p"):
            blocks.append(("p", Paragraph(child, doc)))
        elif child.tag.endswith("tbl"):
            blocks.append(("tbl", Table(child, doc)))
    return blocks


def _find_normative_start_index(blocks: list[tuple[str, Any]]) -> int:
    """Locate the exact start index of the normative body."""
    for idx, (b_type, obj) in enumerate(blocks):
        if b_type == "p":
            txt = obj.text.strip().upper()
            if any(k in txt for k in ["1  PHẠM VI ÁP DỤNG", "1. PHẠM VI ÁP DỤNG", "1 PHẠM VI ÁP DỤNG", "1  QUY ĐỊNH CHUNG"]):
                return idx
    return 0


def _process_paragraph_block(ctx: StandardConversionContext, blocks: list[tuple[str, Any]], i: int) -> int:
    """Parse a single paragraph block and emit corresponding markdown structure."""
    obj = blocks[i][1]
    text = obj.text.strip()
    if not text:
        return i + 1

    # 1. Table Caption
    m_tbl = re.match(r"^(?:Bảng|BẢNG)\s+([0-9A-Za-z\.\-]+)\s*[-–—:]\s*(.+)$", text)
    if m_tbl:
        ctx.last_table_caption_num = m_tbl.group(1)
        cap_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        clean_cap = re.sub(r"^(?:Bảng|BẢNG)\s+[0-9A-Za-z\.\-]+\s*[-–—:]\s*", "", cap_rendered).strip()
        ctx.last_table_caption = f"Bảng {ctx.last_table_caption_num} - {clean_cap}"
        ctx.in_trong_do = False
        return i + 1

    # 2. Formula Heading
    m_f_head = re.match(r"^\(([0-9A-Za-z\.]+)\)$", text)
    if m_f_head:
        f_tag = m_f_head.group(1)
        f_slug = f_tag.lower().replace(".", "_")
        fid, f_latex = FORMULAS_MAP.get(f_tag, (f"F_TCVN2737_FORMULA_{f_slug.upper()}", f"\text{{Formula }} ({f_tag})"))
        ctx.emit(f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \tag{{{f_tag}}}$$\n<!-- formula_id: "{fid}" -->\n\n')
        ctx.in_trong_do = False
        return i + 1

    # 3. Figure Card
    m_fig = re.match(r"^(?:Hình|HÌNH)\s+([0-9A-Za-z\.\-]+)\s*[-–—:]\s*(.+)$", text)
    if m_fig:
        fig_num = m_fig.group(1)
        fig_title = m_fig.group(2).strip()
        fig_slug = fig_num.lower().replace(".", "_")
        anchor = f"hinh-{fig_slug}"
        fig_entry = {
            "tag": fig_num, "title": fig_title, "anchor": anchor,
            "image_relpath": f"figures/images/hinh_{fig_slug}.png",
            "geometry_rules": AERODYNAMIC_FIGURES_GEOMETRY.get(fig_num, {})
        }
        ctx.emit(render_markdown_figure_card(fig_entry))
        ctx.in_trong_do = False
        return i + 1

    # 4. Annex Heading
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
        ctx.in_trong_do = False
        return i + 1

    # 5. Section Heading (1 to 99)
    m_sec = re.match(r"^([1-9][0-9]?)\s+([^\n]+)", text)
    if m_sec and not m_sec.group(2).startswith(("-", "–", "—", ":")) and len(m_sec.group(2)) < 120 and not m_sec.group(2).lower().startswith(("đối với", "khi", "lấy", "tính", "theo", "như")):
        sec_num = m_sec.group(1)
        sec_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        sec_title = re.sub(rf"^{re.escape(sec_num)}\s+", "", sec_rendered).strip()
        ctx.emit(f'\n<a id="muc-{sec_num}"></a>\n## {sec_num}  {sec_title.upper()}\n\n')
        ctx.in_trong_do = False
        return i + 1

    # 6. Clause Heading (e.g. 1.1, 10.2.1, F.1, G.2.1)
    m_clause = re.match(r"^([A-Z]|[1-9][0-9]?)\.([0-9]+(?:\.[0-9]+)*)\s+([^\n]+)", text)
    if m_clause:
        cl_num = f"{m_clause.group(1)}.{m_clause.group(2)}"
        cl_rendered = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        cl_title = re.sub(rf"^{re.escape(cl_num)}\s+", "", cl_rendered).strip()
        anchor = f"muc-{cl_num.lower().replace('.', '-')}"
        ctx.emit(f'\n<a id="{anchor}"></a>\n### {cl_num}  {cl_title}\n\n')
        ctx.in_trong_do = False
        return i + 1

    # 7. Technical Notes
    if re.match(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)", text, re.IGNORECASE):
        note_clean = re.sub(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*", "", text, flags=re.IGNORECASE).strip()
        m_num = re.search(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)", text, re.IGNORECASE)
        prefix = f"**CHÚ THÍCH {m_num.group(1)}:**" if m_num and m_num.group(1) else "**CHÚ THÍCH:**"
        rendered_note = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
        rendered_note_clean = re.sub(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*", "", rendered_note, flags=re.IGNORECASE).strip()
        ctx.emit(f"{prefix} {rendered_note_clean}\n\n")
        ctx.in_trong_do = False
        return i + 1

    # 8. Variable Glossary / Prose
    rendered_p = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)
    if rendered_p.startswith(("trong đó:", "Trong đó:", "trong đó", "Trong đó")):
        ctx.in_trong_do = True
        ctx.emit(f"{rendered_p}\n\n")
    elif ctx.in_trong_do:
        if rendered_p.startswith(("- ", "– ", "— ", "+ ", "• ")):
            ctx.emit(f"&nbsp;&nbsp;&nbsp;&nbsp;{rendered_p}\n\n")
        elif re.match(r"^[a-zA-Z0-9\$]", rendered_p) and len(rendered_p) > 2:
            ctx.emit(f"&nbsp;&nbsp;&nbsp;&nbsp;\- {rendered_p}\n\n")
        else:
            ctx.in_trong_do = False
            ctx.emit(f"{rendered_p}\n\n")
    else:
        ctx.emit(f"{rendered_p}\n\n")

    return i + 1


def _process_table_block(ctx: StandardConversionContext, tbl: Any, i: int) -> None:
    """Parse a docx table block, checking for formula frames and exporting tables to CSV/JSON."""
    # 1. Formula Frame Check
    all_row_formulas: list[tuple[str, Any]] = []
    for r in tbl.rows:
        r_texts = [c.text.strip() for c in r.cells]
        f_tag = next((m.group(1) for t in r_texts if (m := re.match(r"^\(([0-9A-Za-z\.]+)\)$", t))), None)
        if f_tag:
            all_row_formulas.append((f_tag, r))

    if all_row_formulas and len(all_row_formulas) == len(tbl.rows):
        for f_tag, r in all_row_formulas:
            f_slug = f_tag.lower().replace(".", "_")
            if f_tag in FORMULAS_MAP:
                fid, f_latex = FORMULAS_MAP[f_tag]
            else:
                fid = f"F_TCVN2737_FORMULA_{f_slug.upper()}"
                raw_f = next((render_paragraph_with_runs(c.paragraphs[0], rid_to_katex=ctx.rid_to_katex) if c.paragraphs else c.text.strip() for c in r.cells if c.text.strip() and not re.match(r"^\([0-9A-Za-z\.]+\)$", c.text.strip())), f"\text{{Formula }} ({f_tag})")
                f_latex = raw_f.strip("$ ")
            ctx.emit(f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \tag{{{f_tag}}}$$\n<!-- formula_id: "{fid}" -->\n\n')
        ctx.in_trong_do = False
        return

    # 2. Normative or Layout Table
    is_captioned = bool(ctx.last_table_caption)
    if is_captioned:
        t_num = ctx.last_table_caption_num
        t_cap = ctx.last_table_caption
        ctx.last_table_caption = ""
        ctx.last_table_caption_num = ""
        ctx.in_trong_do = False
        t_slug = f"bang_{int(t_num):02d}" if t_num.isdigit() else f"bang_{t_num.lower().replace('.', '_').replace('-', '_')}"
        tbl_anchor = f"bang-{t_slug.replace('_', '-')}"
        ctx.emit(f'\n<a id="{tbl_anchor}"></a>\n### {t_cap}\n\n')
    else:
        t_num, t_cap = "", ""
        t_slug = f"layout_tbl_{i:03d}"

    md_tbl_str, tbl_footnotes, raw_grid = render_table_markdown(tbl, rid_to_katex=ctx.rid_to_katex)
    ctx.emit(md_tbl_str)
    for fn in tbl_footnotes:
        ctx.emit(f"{fn}\n\n")

    # 3. Export CSV / JSON for captioned tables
    if is_captioned and raw_grid:
        tables_dir = ctx.bundle_dir / "tables"
        csv_dir = tables_dir / "csv"
        json_dir = tables_dir / "json"
        csv_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)

        with open(csv_dir / f"{t_slug}.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(raw_grid)

        headers = [re.sub(r"<[^>]+>", "", h).strip() for h in raw_grid[0]]
        json_rows: list[dict[str, Any]] = []
        for r_idx, row in enumerate(raw_grid[1:], 1):
            row_dict: dict[str, Any] = {"_row_id": r_idx}
            for c_idx, val in enumerate(row):
                key = headers[c_idx] if c_idx < len(headers) and headers[c_idx] else f"col_{c_idx+1}"
                row_dict[key] = re.sub(r"<[^>]+>", "", val).strip()
            json_rows.append(row_dict)

        with open(json_dir / f"{t_slug}.json", "w", encoding="utf-8") as f:
            json.dump({"table_id": t_slug, "table_number": t_num, "table_title": t_cap, "rows": json_rows}, f, ensure_ascii=False, indent=2)

        ctx.tables_extracted.append({"table_id": t_slug, "table_number": t_num, "title": t_cap, "csv_file": f"tables/csv/{t_slug}.csv", "json_file": f"tables/json/{t_slug}.json"})


def _export_modular_annexes_and_moc(ctx: StandardConversionContext) -> Path:
    """Export modular annex files, 2D navigation matrix, tables catalog, and AST index."""
    # 1. Export Annexes
    if ctx.annex_buffers:
        annexes_dir = ctx.bundle_dir / "annexes"
        annexes_dir.mkdir(parents=True, exist_ok=True)
        nav_rows: list[str] = []
        for a_letter, a_info in ctx.annex_buffers.items():
            annex_slug, annex_title, annex_type, annex_anchor = a_info["slug"], a_info["title"], a_info["type"], a_info["anchor"]
            annex_md = "".join(a_info["parts"]).replace("figures/images/", "../figures/images/").replace("tables/", "../tables/")
            (annexes_dir / f"{annex_slug}.md").write_text(annex_md, encoding="utf-8")
            nav_rows.append(f"| **Phụ lục {a_letter}** | {annex_title} | {annex_type} | [📑 **Xem Phụ lục**](annexes/{annex_slug}.md#{annex_anchor}) |")

        nav_matrix = [
            "\n---\n",
            f"## 📑 DANH MỤC PHỤ LỤC KỸ THUẬT CHUYÊN ĐỀ (MODULAR ANNEXES)\n\nToàn bộ {len(ctx.annex_buffers)} Phụ lục kỹ thuật chuyên đề đã được module hóa thành các tệp độc lập nhằm tối ưu hóa tra cứu và thẩm tra thiết kế (ADR 0021 & ADR 0030):\n",
            "| Ký hiệu | Tên Phụ Lục | Tính chất | Liên kết Tập tin |",
            "| :---: | :--- | :---: | :---: |"
        ]
        nav_matrix.extend(nav_rows)
        nav_matrix.append(f"\n---\n\n## 📊 HỆ THỐNG TRA CỨU BẢNG & SƠ ĐỒ KỸ THUẬT\n\n- **Tra cứu {len(ctx.tables_extracted)} Bảng Số Liệu:** Tra cứu chi tiết dạng CSV/JSON tại [Thư mục Bảng Số Liệu](tables/README.md).\n- **Tra cứu Sơ Đồ Hình Vẽ:** Tra cứu ảnh nét cao và đặc tả phân vùng tại [Danh Mục Sơ Đồ Khí Động](figures/figures_catalog.yaml).\n\n")
        ctx.body_md_parts.append("\n".join(nav_matrix))

    # 2. Write Primary Markdown
    out_name = ctx.output_filename or f"{ctx.bundle_dir.name}.md"
    target_md_path = ctx.bundle_dir / out_name
    target_md_path.write_text("".join(ctx.body_md_parts), encoding="utf-8")

    # 3. Export Tables Catalog & README
    if ctx.tables_extracted:
        tables_dir = ctx.bundle_dir / "tables"
        with open(tables_dir / "tables_catalog.json", "w", encoding="utf-8") as f:
            json.dump({"total_tables": len(ctx.tables_extracted), "tables": ctx.tables_extracted}, f, ensure_ascii=False, indent=2)

        tbl_readme = ["# DANH MỤC BẢNG TRA CỨU KỸ THUẬT 2D (OKF v2.2)\n", "| Mã bảng | Tên bảng | CSV | JSON |", "| :--- | :--- | :---: | :---: |"]
        for t in ctx.tables_extracted:
            tbl_readme.append(f"| {t['table_id']} | {t['title']} | [CSV]({t['csv_file']}) | [JSON]({t['json_file']}) |")
        (tables_dir / "README.md").write_text("\n".join(tbl_readme) + "\n", encoding="utf-8")

    # 4. Generate AST and QA Benchmarks
    clauses, qa_list = generate_bundle_ast_and_qa(ctx.bundle_dir)
    return {
        "status": "success",
        "bundle": ctx.bundle_dir.name,
        "archetype": "TECHNICAL_TCVN",
        "clauses_count": len(clauses),
        "templates_count": 0,
        "tables_count": len(ctx.tables_extracted),
        "qa_count": len(qa_list),
    }


def process_technical_standard_strategy(
    docx_path: Path | str,
    bundle_dir: Path | str,
    output_filename: str | None = None,
    rid_to_katex: dict[str, str] | None = None,
    registry_file: Path | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Process a Technical Standard (TCVN / QCVN) DOCX file with 100% Visual Parity & Modular Annex Split."""
    from docx import Document

    docx_p = Path(docx_path)
    bundle_p = Path(bundle_dir)
    bundle_p.mkdir(parents=True, exist_ok=True)

    # 1. Harvest formulas and extract figures
    cache_dir = bundle_p.parents[2] / ".md" / "cache" / "formula_vision" if len(bundle_p.parents) >= 3 else bundle_p / ".cache"
    skip_vis = os.environ.get("AI_SKIP_VISION") == "1"
    docx_rid_to_katex = rid_to_katex or harvest_docx_formula_images(docx_p, cache_dir=cache_dir, skip_vision=skip_vis)
    extract_docx_figures(docx_p, bundle_p)

    # 2. Extract and locate normative start
    doc = Document(docx_p)
    blocks = _extract_document_blocks(doc)
    start_idx = _find_normative_start_index(blocks)

    # 3. Process blocks with conversion context
    ctx = StandardConversionContext(
        bundle_dir=bundle_p,
        output_filename=output_filename,
        rid_to_katex=docx_rid_to_katex,
    )

    i = start_idx
    while i < len(blocks):
        b_type, obj = blocks[i]
        if b_type == "p":
            i = _process_paragraph_block(ctx, blocks, i)
        elif b_type == "tbl":
            _process_table_block(ctx, obj, i)
            i += 1

    # 4. Export modular bundle
    return _export_modular_annexes_and_moc(ctx)
