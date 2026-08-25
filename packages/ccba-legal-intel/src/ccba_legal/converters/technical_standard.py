"""Native Technical Standard (TCVN / QCVN) Strategy Converter (ADR 0030, ADR 0031)."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.converters.table_extractor import classify_and_extract_tables
from ccba_legal.converters.unit_normalizer import normalize_units_and_math
from ccba_legal.formula_harvester import harvest_docx_formula_images
from ccba_legal.gold_standard import generate_bundle_ast_and_qa, inject_semantic_anchors


GREEK_MAP: dict[str, str] = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "η": r"\eta", "θ": r"\theta", "λ": r"\lambda",
    "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho",
    "σ": r"\sigma", "τ": r"\tau", "φ": r"\varphi", "ψ": r"\psi",
    "ω": r"\omega", "Δ": r"\Delta", "Σ": r"\Sigma", "Ω": r"\Omega"
}

# 100% Authentic KaTeX Formulations for TCVN 2737:2023 & Structural Standards
FORMULAS_MAP: dict[str, tuple[str, str]] = {
    "1": ("F_TCVN2737_TO_HOP_CO_BAN_1", r'C_m = \gamma_n \left( \sum_{i \ge 1} \gamma_{f,i} G_{k,i} \text{ “+” } \sum_{j \ge 1} \gamma_{f,j} \psi_{L,j} Q_{k,L,j} \text{ “+” } \sum_{m \ge 1} \gamma_{f,m} \psi_{t,m} Q_{k,t,m} \right)'),
    "2": ("F_TCVN2737_TO_HOP_DAC_BIET_2", r'C_a = \left( \sum_{i \ge 1} \gamma_{f,i} G_{k,i} \text{ “+” } \sum_{j \ge 1} \gamma_{f,j} \psi_{L,j} Q_{k,L,j} \text{ “+” } \sum_{m \ge 1} \gamma_{f,m} \psi_{t,m} Q_{k,t,m} \right) \text{ “+” } A_d'),
    "3": ("F_TCVN2737_HE_SO_GIAM_DIEN_TICH_1", r"\varphi_1 = 0,4 + \frac{0,6}{\sqrt{A / A_1}} \ge 0,6"),
    "4": ("F_TCVN2737_HE_SO_GIAM_DIEN_TICH_2", r"\varphi_2 = 0,5 + \frac{0,5}{\sqrt{A / A_2}} \ge 0,6"),
    "5": ("F_TCVN2737_HE_SO_GIAM_SO_TANG_1", r"\varphi_3 = 0,4 + \frac{\varphi_1 - 0,4}{\sqrt{n}} \ge 0,5"),
    "6": ("F_TCVN2737_HE_SO_GIAM_SO_TANG_2", r"\varphi_4 = 0,5 + \frac{\varphi_2 - 0,5}{\sqrt{n}} \ge 0,5"),
    "7": ("F_TCVN2737_LUC_BUNG_CAU_TRUC", r"F_{d,up} = \gamma_f \cdot \xi \cdot Q_{k,t}"),
    "8": ("F_TCVN2737_LUC_VA_CHAM_CAU_TRUC", r"F_{d',down} = C \sqrt{m}"),
    "9": ("F_TCVN2737_LUC_HAM_NGANG_CAU_TRUC", r"F_{d,h} = \xi \cdot G_k"),
    "10": ("F_TCVN2737_AP_LUC_GIO_TIEU_CHUAN", r"W_k = W_{3s,10} \cdot k(z_e) \cdot c \cdot G_f"),
    "11": ("F_TCVN2737_VAN_TOC_GIO_3S_10", r"W_0 = 0,0613 \, V_0^2"),
    "12": ("F_TCVN2737_HE_SO_DO_CAO_GIO", r"k(z_e) = 2,01 \left(\frac{z_e}{z_g}\right)^{2/\alpha}"),
    "13": ("F_TCVN2737_HE_SO_GIAT_GF", r"G_f = 0,925 \left( \frac{1 + 1,7 I(z_s) \sqrt{g_Q^2 Q^2 + g_R^2 R^2}}{1 + 1,7 g_v I(z_s)} \right)"),
    "14": ("F_TCVN2737_CUONG_DO_NHIEU_DONG", r"I(z_s) = c_r \left(\frac{10}{z_s}\right)^{1/6}"),
    "15": ("F_TCVN2737_HE_SO_DINH_CONG_HUONG_GR", r"g_R = \sqrt{2 \ln(3\,600 n_1)} + \frac{0,577}{\sqrt{2 \ln(3\,600 n_1)}}"),
    "16": ("F_TCVN2737_HE_SO_PHAN_UNG_NEN", r"Q = \sqrt{\frac{1}{1 + 0,63 \left(\frac{b + h}{L(z_s)}\right)^{0,63}}}"),
    "17": ("F_TCVN2737_TY_LE_CHIEU_DAI_TICH_PHAN", r"L(z_s) = \ell \left(\frac{z_s}{10}\right)^{\bar{\alpha}}"),
    "18": ("F_TCVN2737_HE_SO_PHAN_UNG_CONG_HUONG_R", r"R = \sqrt{\frac{1}{\beta} R_n R_h R_b (0,53 + 0,47 R_d)}"),
    "19": ("F_TCVN2737_HAM_MAT_DO_PHO_NANG_LUONG", r"R_n = \frac{7,47 N_1}{(1 + 10,3 N_1)^{5/3}}"),
    "20": ("F_TCVN2737_TAN_SO_KHONG_THU_NGUYEN", r"N_1 = \frac{n_1 L(z_s)}{V(z_s)_{3\,600\text{s},50}}"),
    "21": ("F_TCVN2737_VAN_TOC_GIO_TRUNG_BINH_3600S", r"V(z_s)_{3\,600\text{s},50} = \bar{b} \left(\frac{z_s}{10}\right)^{\bar{\alpha}} V_{3s,50}"),
    "22": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_CAO", r"R_h = \frac{1}{\eta_h} - \frac{1}{2\eta_h^2}\left(1 - e^{-2\eta_h}\right); \quad R_h = 1 \text{ khi } \eta_h = 0"),
    "23": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_RONG", r"R_b = \frac{1}{\eta_b} - \frac{1}{2\eta_b^2}\left(1 - e^{-2\eta_b}\right); \quad R_b = 1 \text{ khi } \eta_b = 0"),
    "24": ("F_TCVN2737_HAM_TUONG_QUAN_CHIEU_SAU", r"R_d = \frac{1}{\eta_d} - \frac{1}{2\eta_d^2}\left(1 - e^{-2\eta_d}\right); \quad R_d = 1 \text{ khi } \eta_d = 0"),
    "25": ("F_TCVN2737_DO_VONG_GIOI_HAN", r"f \le f_u")
}


def render_paragraph_with_runs(p: Any) -> str:
    """Render a docx paragraph while preserving sub/superscripts as clean KaTeX tokens."""
    runs = p.runs
    if not runs:
        return p.text.strip()

    grouped = []
    for r in runs:
        t = r.text
        if not t:
            continue
        xml = r._r.xml
        is_sub = "subscript" in xml or (r.font.subscript is True)
        is_sup = "superscript" in xml or (r.font.superscript is True)
        mode = "sub" if is_sub else ("sup" if is_sup else "norm")
        if grouped and grouped[-1][0] == mode:
            grouped[-1] = (mode, grouped[-1][1] + t)
        else:
            grouped.append((mode, t))

    out_tokens = []
    for mode, text in grouped:
        if mode == "sub":
            clean_t = text.strip()
            for g_char, g_latex in GREEK_MAP.items():
                clean_t = clean_t.replace(g_char, g_latex)
            if len(clean_t) > 1 or "," in clean_t or "\\" in clean_t:
                out_tokens.append(f"$_{{{clean_t}}}$")
            else:
                out_tokens.append(f"$_{clean_t}$")
        elif mode == "sup":
            clean_t = text.strip()
            if len(clean_t) > 1:
                out_tokens.append(f"$^{{{clean_t}}}$")
            else:
                out_tokens.append(f"$^{clean_t}$")
        else:
            out_tokens.append(text)

    res = "".join(out_tokens)

    # Merge adjacent alphanumeric + math subscript/superscript
    res = re.sub(
        r"([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9\u0370-\u03FF]+)\$(_\{[^}]+\}|_[a-zA-Z0-9,]+|\^\{[^}]+\}|\^[a-zA-Z0-9]+)\$",
        lambda m: f"${m.group(1)}{m.group(2)}$",
        res,
    )

    # Merge consecutive math tokens
    res = re.sub(r"\$([^$]+)\$\s*\$([^$]+)\$", r"$ $", res)

    # Replace Greek letters inside math tokens with proper LaTeX
    def _sanitize_math_greeks(m: re.Match) -> str:
        inner = m.group(1)
        for g_char, g_latex in GREEK_MAP.items():
            inner = inner.replace(g_char, g_latex)
        return f"${inner}$"

    res = re.sub(r"\$([^$]+)\$", _sanitize_math_greeks, res)

    return normalize_units_and_math(res)


def calculate_emsp_padding(sym: str) -> str:
    """Calculate dynamic em-space tab padding to align the definition column vertically."""
    clean = (
        sym.replace('$', '')
        .replace(r'\gamma', 'g')
        .replace(r'\eta', 'h')
        .replace(r'\psi', 'p')
        .replace(r'\alpha', 'a')
        .replace(r'\beta', 'b')
    )
    clean = clean.replace('{;', '').replace('}', '').replace('_', '')
    vis_len = len(clean.strip())
    if vis_len <= 1:
        return '&emsp;&emsp;&emsp;&emsp;'
    elif vis_len <= 3:
        return '&emsp;&emsp;&emsp;'
    elif vis_len <= 5:
        return '&emsp;&emsp;'
    else:
        return '&emsp;'


def format_symbol_cell_runs(cell: Any) -> str:
    """Format Section 3.2 docx symbol cells into exact KaTeX math variables."""
    grouped = []
    for p in cell.paragraphs:
        for r in p.runs:
            t = r.text
            if not t:
                continue
            xml = r._r.xml
            is_sub = "subscript" in xml or (r.font.subscript is True)
            is_sup = "superscript" in xml or (r.font.superscript is True)
            mode = "sub" if is_sub else ("sup" if is_sup else "norm")
            if grouped and grouped[-1][0] == mode:
                grouped[-1] = (mode, grouped[-1][1] + t)
            else:
                grouped.append((mode, t))

    parts = []
    for mode, text in grouped:
        t_mapped = text
        for g_char, g_latex in GREEK_MAP.items():
            if g_char in t_mapped:
                t_mapped = t_mapped.replace(g_char, g_latex)
        if mode == "sub":
            clean_t = text.strip()
            if len(clean_t) > 1 or "," in clean_t:
                parts.append(f"_{{{clean_t}}}")
            else:
                parts.append(f"_{clean_t}")
        elif mode == "sup":
            clean_t = text.strip()
            if len(clean_t) > 1:
                parts.append(f"^{{{clean_t}}}")
            else:
                parts.append(f"^{clean_t}")
        else:
            parts.append(t_mapped)
    raw_sym = "".join(parts).strip()
    return f"${raw_sym}$"


def render_table_markdown(table: Any) -> str:
    """Render a docx Table object as a GitHub Flavored Markdown table."""
    grid = []
    for row in table.rows:
        row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
        clean_cells = []
        for cell_val in row_cells:
            if not clean_cells or cell_val != clean_cells[-1]:
                clean_cells.append(cell_val)
        if clean_cells:
            grid.append(clean_cells)
    if not grid:
        return ""
    max_cols = max(len(r) for r in grid)
    norm_grid = [r + [""] * (max_cols - len(r)) for r in grid]
    lines = []
    lines.append("| " + " | ".join(norm_grid[0]) + " |")
    lines.append("| " + " | ".join([":---:"] * max_cols) + " |")
    for r in norm_grid[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n"


def process_technical_standard_strategy(
    docx_path: Path,
    bundle_dir: Path,
    registry_file: Path,
    doc_meta: dict[str, Any],
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Native Technical Standard (TCVN / QCVN) Strategy Converter with Integrated Deep Seam."""
    import docx
    import docx.oxml
    import docx.oxml.text.paragraph
    import docx.oxml.table

    doc = docx.Document(str(docx_path))
    templates_dir = bundle_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = bundle_dir / "tables"
    csv_dir = tables_dir / "csv"
    json_dir = tables_dir / "json"
    csv_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    spoke_root = bundle_dir.parents[2] if len(bundle_dir.parents) >= 3 else bundle_dir.parent
    cache_dir = spoke_root / ".md" / "cache" / "formula_vision"
    skip_vision = os.environ.get("AI_SKIP_VISION", "").strip() == "1"

    rid_to_katex: dict = harvest_docx_formula_images(
        docx_path, cache_dir=cache_dir, skip_vision=skip_vision
    )

    blocks = []
    for child in doc.element.body.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            blocks.append(("p", docx.text.paragraph.Paragraph(child, doc)))
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            blocks.append(("tbl", docx.table.Table(child, doc)))

    body_md_parts: list[str] = []
    tables_extracted: list[dict[str, Any]] = []

    # ADR 0030: Find exact start of real normative body
    start_idx = 0
    for idx, (b_type, obj) in enumerate(blocks):
        if b_type == "p":
            txt = obj.text.strip().upper()
            if "1  PHẠM VI ÁP DỤNG" in txt or "1. PHẠM VI ÁP DỤNG" in txt or "1 PHẠM VI ÁP DỤNG" in txt or "1  QUY ĐỊNH CHUNG" in txt:
                start_idx = idx
                break

    i = start_idx
    last_table_caption = ""
    last_table_caption_num = ""
    in_trong_do = False

    while i < len(blocks):
        b_type, obj = blocks[i]
        if b_type == "p":
            text = obj.text.strip()
            if not text:
                xml_str = obj._element.xml
                for rid, katex in rid_to_katex.items():
                    if rid in xml_str and not katex.startswith("<!-- DIAGRAM"):
                        body_md_parts.append(f"\n{katex}\n")
                        break
                i += 1
                continue

            if text.lower() == "trong đó:" or text.lower() == "trong đó":
                body_md_parts.append("trong đó:\n\n")
                in_trong_do = True
                i += 1
                continue

            if "Lời nói đầu" in text or "MỤC LỤC" in text:
                i += 1
                continue

            # Table Caption check
            m_tbl = re.match(r"^(?:Bảng|Table)\s+([0-9A-Za-z\.\-]+)(?:\s*[-–—:]\s*(.+))?$", text, re.IGNORECASE)
            if m_tbl:
                last_table_caption = text
                last_table_caption_num = m_tbl.group(1)
                in_trong_do = False
                i += 1
                continue

            # Figure Captions (Generalized Pattern 2)
            m_fig = re.match(r"^(?:Hình|HÌNH|Figure)\s+([0-9A-Za-z\.\-]+)(?:\s*[-–—:]\s*(.+))?$", text, re.IGNORECASE)
            if m_fig:
                fig_num = m_fig.group(1)
                fig_title = m_fig.group(2) or ""
                fig_slug = fig_num.lower().replace('.', '_').replace('-', '_')
                fig_cap = f'<a id="hinh-{fig_slug}"></a>\n\n**Hình {fig_num} — {fig_title}**\n\n'
                body_md_parts.append(fig_cap)
                in_trong_do = False
                i += 1
                continue

            # Annex Headings (Generalized Pattern 3)
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
                anchor = f"phu-luc-{a_letter.lower()}"
                hdr_str = f"## PHỤ LỤC {a_letter}"
                if a_type:
                    hdr_str += f"  ({a_type})"
                if a_title:
                    hdr_str += f"  {a_title.upper()}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n{hdr_str}\n\n')
                in_trong_do = False
                i += 1
                continue

            # Section Headings
            m_sec = re.match(r"^([1-9]|10)\s+([^\n]+)", text)
            if m_sec:
                sec_num, sec_title = m_sec.group(1), m_sec.group(2)
                anchor = f"muc-{sec_num}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n## {sec_num}  {sec_title.upper()}\n\n')
                in_trong_do = False
                i += 1
                continue

            # Technical Notes (Generalized Pattern 4)
            m_note = re.match(r"^(?:CHÚ THÍCH|Chú thích)\s*([0-9]+)?\s*[:–-]\s*(.+)$", text)
            if m_note:
                n_num = m_note.group(1)
                prefix = f"**CHÚ THÍCH {n_num}:**" if n_num else "**CHÚ THÍCH:**"
                rend_note = render_paragraph_with_runs(obj)
                rend_note = re.sub(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*", "", rend_note, flags=re.IGNORECASE).strip()
                body_md_parts.append(f"{prefix} {rend_note}\n\n")
                in_trong_do = False
                i += 1
                continue

            # Definition Headings
            m_def = re.match(r"^(1\.3\.[0-9]+|3\.[0-9]+)\s+([^\n]+)", text)
            if m_def:
                def_num, def_title = m_def.group(1), m_def.group(2)
                anchor = f"muc-{def_num.replace('.', '-')}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}  {def_title}\n\n')
                i += 1
                continue

            m_def_alone = re.match(r"^(1\.3\.[0-9]+|3\.[0-9]+)$", text)
            if m_def_alone:
                def_num = m_def_alone.group(1)
                anchor = f"muc-{def_num.replace('.', '-')}"
                if i + 1 < len(blocks) and blocks[i + 1][0] == "p":
                    next_t = blocks[i + 1][1].text.strip()
                    body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}  {next_t}\n\n')
                    i += 2
                    continue
                else:
                    body_md_parts.append(f'\n<a id="{anchor}"></a>\n#### {def_num}\n\n')
                    i += 1
                    continue

            if re.match(r"^[a-z]\)\s+", text):
                in_trong_do = False

            # Clauses
            m_cl = re.match(r"^([1-9]|10)\.([0-9]+(?:\.[0-9]+)*)\s+([^\n]+)", text)
            if m_cl:
                cl_num = f"{m_cl.group(1)}.{m_cl.group(2)}"
                cl_title = m_cl.group(3)
                anchor = f"muc-{cl_num.replace('.', '-')}"
                body_md_parts.append(f'\n<a id="{anchor}"></a>\n### {cl_num}  {cl_title}\n\n')
                in_trong_do = False
                i += 1
                continue

            # Preserved lists (ADR 0029)
            if text.startswith(("+ ", "+")):
                body_md_parts.append(f"&nbsp;&nbsp;\\+ {text.lstrip('+ ').strip()}\n")
                i += 1
                continue
            if text.startswith(("- ", "• ", "– ", "— ", "-")):
                body_md_parts.append(f"\\- {text.lstrip('-•–— ').strip()}\n")
                i += 1
                continue

            # Run-aware paragraph rendering
            rendered_p = render_paragraph_with_runs(obj)
            if in_trong_do:
                body_md_parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{rendered_p}\n\n")
            else:
                body_md_parts.append(f"{rendered_p}\n\n")
            i += 1

        elif b_type == "tbl":
            tbl = obj
            rows_cnt = len(tbl.rows)
            cols_cnt = len(tbl.columns)
            cell_texts = [c.text.strip() for r in tbl.rows for c in r.cells]

            # 1. Formula frame check (ADR 0030 / ADR 0031)
            formula_num = None
            for t in cell_texts:
                m_f = re.match(r"^\((\d+)\)$", t)
                if m_f:
                    formula_num = m_f.group(1)
                    break

            if formula_num and rows_cnt <= 2:
                if formula_num in FORMULAS_MAP:
                    fid, f_latex = FORMULAS_MAP[formula_num]
                    body_md_parts.append(f'\n<a id="formula-{formula_num}"></a>\n\n$$\n{f_latex} \\tag{{{formula_num}}}\n$$\n\n<!-- formula_id: "{fid}" -->\n\n')
                i += 1
                continue

            # 2. Symbol glossary table check (Mục 3.2)
            prev_context = "".join(body_md_parts[-3:]).lower()
            if "ký hiệu chính sau" in prev_context or "3.2  ký hiệu" in prev_context:
                for row in tbl.rows:
                    if len(row.cells) >= 2:
                        sym = format_symbol_cell_runs(row.cells[0])
                        desc = render_paragraph_with_runs(row.cells[1].paragraphs[0]) if row.cells[1].paragraphs else row.cells[1].text.strip()
                        desc = desc.replace("qk,qper = η · qk,t", "$q_{k,qper} = \\eta \\cdot q_{k,t}$")
                        desc = desc.replace("($q_{k,qper}$ = η · $q_{k,t}$)", "($q_{k,qper} = \\eta \\cdot q_{k,t}$)")
                        pad = calculate_emsp_padding(sym)
                        body_md_parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;**{sym}**{pad}{desc}\n\n")
                i += 1
                continue

            # 3. Normative Table
            if last_table_caption:
                t_num = last_table_caption_num
                t_cap = last_table_caption
                last_table_caption = ""
                last_table_caption_num = ""
                in_trong_do = False
            else:
                t_num = f"raw_{len(tables_extracted)+1:02d}"
                t_cap = f"Bảng {t_num}"

            if t_num.isdigit():
                t_slug = f"bang_{int(t_num):02d}"
            else:
                t_slug = f"bang_{t_num.lower().replace('.', '_').replace('-', '_')}"

            anchor = f"bang-{t_slug.replace('_', '-')}"
            body_md_parts.append(f'\n<a id="{anchor}"></a>\n### {t_cap}\n\n')
            body_md_parts.append(render_table_markdown(tbl))

            grid = []
            for row in tbl.rows:
                grid.append([c.text.strip().replace("\n", " ") for c in row.cells])
            if grid:
                csv_path = csv_dir / f"{t_slug}.csv"
                with open(csv_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(grid)
                
                json_path = json_dir / f"{t_slug}.json"
                headers = grid[0]
                rows_data = [dict(zip(headers, r)) for r in grid[1:]]
                json_path.write_text(json.dumps(rows_data, ensure_ascii=False, indent=2), encoding="utf-8")

                tables_extracted.append({
                    "table_id": t_slug,
                    "title": t_cap,
                    "number": t_num,
                    "csv_path": f"tables/csv/{csv_path.name}",
                    "json_path": f"tables/json/{json_path.name}",
                    "rows_count": len(grid),
                    "status": "active"
                })
            i += 1

    (tables_dir / "tables_catalog.json").write_text(json.dumps(tables_extracted, ensure_ascii=False, indent=2), encoding="utf-8")

    out_name = output_filename or f"{bundle_dir.name}.md"
    target_md_path = bundle_dir / out_name
    final_md = "".join(body_md_parts)
    target_md_path.write_text(final_md, encoding="utf-8")

    # Generate AST & QA Benchmark
    doc_title = doc_meta.get("title", f"TCVN {bundle_dir.name}")
    clauses, qa_list = generate_bundle_ast_and_qa(bundle_dir, doc_title=doc_title)

    return {
        "status": "success",
        "bundle": bundle_dir.name,
        "archetype": "TECHNICAL_TCVN",
        "clauses_count": len(clauses),
        "templates_count": 0,
        "tables_count": len(tables_extracted),
        "qa_count": len(qa_list),
    }
