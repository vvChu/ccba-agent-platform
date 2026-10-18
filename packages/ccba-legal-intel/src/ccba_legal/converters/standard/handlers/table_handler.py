# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Table Handler & 2D Matrix Exporter for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import csv
import json
import re
from typing import Any

from ccba_legal.converters.standard.models import HierarchyState
from ccba_legal.converters.standard.sanitizers import render_paragraph_with_runs
from ccba_legal.converters.technical_formulas import GREEK_MAP


def escape_table_pipes(text: str) -> str:
    """Escape pipe '|' symbols in cell text to prevent breaking Markdown table columns."""
    if "|" not in text:
        return text

    def _rep_math(m: re.Match[str]) -> str:
        content = re.sub(r"(?<!\\)\|", r"\\vert ", m.group(1))
        return f"${content}$"

    res = re.sub(r"\$([^$]+)\$", _rep_math, text)
    return re.sub(r"(?<!\\)\|", r"\|", res)


def build_composite_headers(header_rows: list[list[str]]) -> list[str]:
    """Combine multi-row table headers (2 to 4 tiers) into single composite headers."""
    if not header_rows:
        return []
    cols_count = len(header_rows[0])
    composite: list[str] = []
    for c in range(cols_count):
        tokens: list[str] = []
        for r in range(len(header_rows)):
            val = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", header_rows[r][c]).strip()).strip()
            if not val or val in ("—", "-"):
                continue
            if not tokens or tokens[-1] != val:
                tokens.append(val)
        composite.append(" — ".join(tokens) if tokens else f"col_{c + 1}")
    return composite


def resolve_hierarchical_headers(grid: list[list[str]]) -> list[list[str]]:
    """Combine multi-row table headers (e.g. category spans) into structured single-row headers."""
    if len(grid) < 2:
        return grid
    header_rows_count = 1
    for r_idx in range(1, min(5, len(grid))):
        prev_row, curr_row = grid[r_idx - 1], grid[r_idx]
        c0_curr, c0_prev = curr_row[0].strip(), prev_row[0].strip()
        if re.match(r"^\(?[a-zđ0-9]+\)?$", c0_curr, re.IGNORECASE) and c0_curr != c0_prev:
            break
        c0_same = bool(c0_curr and c0_curr == c0_prev)
        has_subheaders = any(
            c > 0
            and prev_row[c]
            and prev_row[c] == prev_row[c - 1]
            and curr_row[c] != curr_row[c - 1]
            for c in range(len(prev_row))
        )
        non_empty = [c.strip() for c in curr_row if c.strip()]
        is_category_partition = len(set(non_empty)) == 1 and len(non_empty) > 1
        if (has_subheaders or c0_same) and not is_category_partition:
            if not c0_same and re.match(r"^[0-9\.,\-\+±%]+$", c0_curr.replace(" ", "")):
                break
            header_rows_count = r_idx + 1
        else:
            break
    if header_rows_count > 1:
        return [build_composite_headers(grid[:header_rows_count])] + grid[header_rows_count:]
    return grid


def detect_table_archetype(
    rows_count: int,
    cols_count: int,
    text: str = "",
    is_formula_frame: bool = False,
    is_captioned: bool = False,
    header_rows_count: int = 1,
    has_images: bool = False,
    has_footnotes: bool = False,
) -> str:
    """Classify table into 1 of 6 Table Archetypes according to ADR 0041."""
    lower_t = text.lower()
    if is_formula_frame:
        return "BORDERLESS_LAYOUT"
    if rows_count <= 3 and cols_count <= 2 and not is_captioned:
        admin_keywords = (
            "cộng hòa xã hội chủ nghĩa",
            "độc lập - tự do",
            "độc lập tự do",
            "nơi nhận:",
            "ký, ghi rõ họ tên",
            "ký, đóng dấu",
            "thủ trưởng đơn vị",
        )
        if any(k in lower_t for k in admin_keywords):
            return "BORDERLESS_LAYOUT"
    if not is_captioned and any(
        k in lower_t
        for k in ("[ ]", "☐", "biên bản", "phiếu kiểm tra", "mẫu số", "chức vụ của người ký")
    ):
        return "ADMIN_FORM"
    if has_images or "<img" in lower_t:
        return "IN_CELL_MULTIMODAL"
    if header_rows_count > 1:
        return "HIERARCHICAL_GRID"
    if has_footnotes or "chú thích" in lower_t:
        return "FOOTNOTE_RICH"
    return "FLAT_MATRIX"


def is_table_footnote_row(row_rendered: list[str]) -> bool:
    """Detect whether a table row is an administrative/normative footnote row rather than a data row."""
    non_empty = [c.strip() for c in row_rendered if c.strip()]
    if not non_empty or len(set(non_empty)) > 1:
        return False
    first_cell = non_empty[0]
    first_cell_stripped = re.sub(r"^(?:<!--.*?-->|[\s\*_])+", "", first_cell)
    if re.match(
        r"^(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn|GHI\s+CHÚ|Ghi\s+chú)",
        first_cell_stripped,
        re.IGNORECASE,
    ):
        return True
    if re.match(
        r"^<sup\b[^>]*>(?:\([0-9a-zA-Z\*\+]+\)|[0-9a-zA-Z\*\+]+\)?|\*+)</sup>",
        first_cell_stripped,
        re.IGNORECASE,
    ):
        return True
    if re.match(r"^(?:\([0-9a-zA-Z\*\+]+\)|\[[0-9a-zA-Z\*\+]+\])\s+", first_cell_stripped):
        return True
    return bool(
        "<br>" in first_cell and re.search(r"<br\s*/?>\s*(?:<sup\b[^>]*>)?\s*[1-9]\)", first_cell)
    )


def _render_table_row_cells(
    row: Any, rid_to_katex: dict[str, str] | None, footnotes: list[str]
) -> list[str]:
    """Render paragraphs in each cell of a table row and extract inline squashed footnotes."""
    row_rendered: list[str] = []
    for cell in row.cells:
        cell_p_rendered: list[str] = []
        for p in cell.paragraphs:
            p_r = render_paragraph_with_runs(p, rid_to_katex=rid_to_katex)
            if p_r:
                if p_r.startswith(("- ", "– ", "— ", "• ")):
                    p_r = "&nbsp;&nbsp;\\- " + p_r.lstrip("-–—• ")
                elif p_r.startswith(("+ ", "+")):
                    p_r = "&nbsp;&nbsp;&nbsp;&nbsp;\\+ " + p_r.lstrip("+ ")
                cell_p_rendered.append(p_r)
        clean_cell = re.sub(r"[\r\n]+", "<br>", "<br>".join(cell_p_rendered)).strip()
        clean_cell = re.sub(r"(?<!\$)\$\$(?!\$)", "$ $", escape_table_pipes(clean_cell))
        row_rendered.append(clean_cell)

    for c_idx, cell_str in enumerate(row_rendered):
        if re.search(r"<br>\s*(?:\*\*)?(?:CHÚ\s+THÍCH|CHÚ\s+DẪN)", cell_str, re.IGNORECASE):
            parts = re.split(
                r"<br>\s*(?=(?:\*\*)?(?:CHÚ\s+THÍCH|CHÚ\s+DẪN))", cell_str, flags=re.IGNORECASE
            )
            row_rendered[c_idx] = parts[0].strip()
            for note_p in parts[1:]:
                note_clean = re.sub(r"^<br\s*/?>", "", note_p).strip()
                for nl in (lp.strip() for lp in re.split(r"<br\s*/?>", note_clean) if lp.strip()):
                    if nl not in footnotes:
                        footnotes.append(nl)
    return row_rendered


def _parse_footnote_row_parts(row_rendered: list[str]) -> list[str]:
    """Deduplicate merged cells in a footnote row and split into normalized footnote parts."""
    unique_cells: list[str] = []
    for c in row_rendered:
        if (c_str := c.strip()) and c_str not in unique_cells:
            unique_cells.append(c_str)
    raw_parts = [p.strip() for p in re.split(r"<br\s*/?>", "<br>".join(unique_cells)) if p.strip()]
    fn_parts: list[str] = []
    seen_clean: set[str] = set()
    prefix_pat = r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[\.:–-]\s*(?:\*\*)?\s*"
    bullet_pat = r"^(?:[-–—•\+]|\*+|\(\*+\)|\([0-9a-zA-Z]+\)|[0-9]+[)\.]|<sup\b[^>]*>[0-9a-zA-Z\*\+\)]+</sup>)\s*"
    for p in raw_parts:
        p_clean = re.sub(prefix_pat, "", p, flags=re.IGNORECASE).strip()
        p_clean = re.sub(r"\s*\*\*$", "", re.sub(r"^\*\*\s*", "", p_clean).strip()).strip()
        if not p_clean:
            continue
        p_clean = re.sub(r"(\d+)\$\^\{0\}\$\s*C\b", r"\1 °C", p_clean)
        if fn_parts and not re.match(bullet_pat, p_clean):
            last_txt = fn_parts[-1].strip()
            if last_txt.endswith(
                ("≤", "≥", "=", "<", ">", ",", ":", "-", "–", "—", "với", "là")
            ) or re.match(r"^[0-9\.,]+", p_clean):
                fn_parts[-1] = f"{last_txt} {p_clean}"
                continue
        if p_clean not in seen_clean:
            seen_clean.add(p_clean)
            fn_parts.append(p_clean)
    return fn_parts


def _format_numbered_footnotes(fn_parts: list[str]) -> list[str]:
    """Format explicitly numbered footnote parts into bullet and numbered blocks."""
    bullet_lines: list[str] = []
    numbered_lines: list[str] = []
    prefix_pat = r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[\.:–-]\s*(?:\*\*)?\s*"
    for fn_p in fn_parts:
        fn_clean = re.sub(prefix_pat, "", fn_p, flags=re.IGNORECASE).strip()
        fn_clean = re.sub(r"\s*\*\*$", "", re.sub(r"^\*\*\s*", "", fn_clean).strip()).strip()
        if not fn_clean:
            continue
        m_num = (
            re.search(
                r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)",
                fn_p,
                flags=re.IGNORECASE,
            )
            or re.search(r"<sup\b[^>]*>([0-9]+)\)?</sup>", fn_p)
            or re.match(r"^(?:\*\*)?\(?([0-9]+)\)[\.\s]*", fn_p)
            or re.match(r"^([0-9]+)[)\.]\s*", fn_p)
        )
        if (re.match(r"^\*+\s*", fn_clean) or re.match(r"^\*+\s*", fn_p)) and not m_num:
            bullet_lines.append(fn_clean)
        elif m_num and m_num.group(1):
            num_str = m_num.group(1)
            fn_clean = re.sub(rf"^<sup\b[^>]*>{num_str}\)?</sup>\s*", "", fn_clean).strip()
            fn_clean = re.sub(rf"^\(?{num_str}\)[\.\s]*", "", fn_clean).strip()
            fn_clean = re.sub(rf"^{num_str}[)\.]\s*", "", fn_clean).strip()
            fn_clean = re.sub(r"\s*\*\*$", "", re.sub(r"^\*\*\s*", "", fn_clean).strip()).strip()
            numbered_lines.append(f"**CHÚ THÍCH {num_str}:** {fn_clean}")
        else:
            fn_clean = re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()
            numbered_lines.append(f"**CHÚ THÍCH {len(numbered_lines) + 1}:** {fn_clean}")

    out: list[str] = []
    if bullet_lines:
        fn_block = ["**CHÚ THÍCH:**"] + [
            f"&nbsp;&nbsp;\\- {bl.lstrip('*–—•- ').strip()}" for bl in bullet_lines
        ]
        out.append("\n".join(fn_block))
    out.extend(numbered_lines)
    return out


def _format_unnumbered_footnotes(fn_parts: list[str]) -> str:
    """Format unnumbered footnote parts into a single-line or bulleted footnote block."""
    prefix_pat = r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*[:–-]\s*(?:\*\*)?\s*"
    if len(fn_parts) == 1:
        fn_clean = re.sub(prefix_pat, "", fn_parts[0], flags=re.IGNORECASE).strip()
        fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
        return f"**CHÚ THÍCH:** {fn_clean}"

    block_lines: list[str] = ["**CHÚ THÍCH:**"]
    for fn_p in fn_parts:
        fn_clean = re.sub(prefix_pat, "", fn_p, flags=re.IGNORECASE).strip()
        fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
        if not fn_clean:
            continue
        if fn_clean.startswith(("- ", "– ", "— ", "• ", "* ", "&nbsp;&nbsp;\\- ")):
            b_txt = fn_clean.replace("&nbsp;&nbsp;\\- ", "").lstrip("-–—•* ")
            block_lines.append(f"&nbsp;&nbsp;\\- {b_txt}")
        elif fn_clean.startswith("$$") or (
            fn_clean.startswith("$") and fn_clean.endswith("$") and len(fn_clean) > 10
        ):
            f_txt = fn_clean.strip()
            if f_txt.startswith("$") and not f_txt.startswith("$$") and not f_txt.endswith("$$"):
                f_txt = f"$${f_txt[1:-1]}$$"
            block_lines.append(f_txt)
        else:
            block_lines.append(f"&nbsp;&nbsp;\\- {fn_clean.lstrip('-–—•* ')}")
    return "\n\n".join(block_lines)


def _extract_footnote_row(row_rendered: list[str], footnotes: list[str]) -> None:
    """Parse a footnote table row and append formatted blocks to footnotes list."""
    fn_parts = _parse_footnote_row_parts(row_rendered)
    if not fn_parts:
        return
    has_explicit_numbered = any(
        re.search(
            r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*[1-9]",
            p,
            re.IGNORECASE,
        )
        or re.match(r"^[0-9]+[)\.]\s+", p)
        or re.search(r"<sup\b[^>]*>([0-9]+)\)?</sup>", p)
        or re.search(r"^\(?([0-9]+)\)\s+", p)
        for p in fn_parts
    )
    if has_explicit_numbered:
        footnotes.extend(_format_numbered_footnotes(fn_parts))
    else:
        footnotes.append(_format_unnumbered_footnotes(fn_parts))


def _normalize_and_format_grid(grid: list[list[str]]) -> tuple[str, list[list[str]]]:
    """Normalize header hierarchy, category spans, column widths, and render GFM table string."""
    grid = resolve_hierarchical_headers(grid)
    cleaned_grid: list[list[str]] = []
    for r_idx, r in enumerate(grid):
        non_empty = [c.strip() for c in r if c.strip()]
        is_numeric = bool(non_empty and re.match(r"^[0-9\.,\-\+±%\s]+$", non_empty[0]))
        if (
            r_idx > 0
            and len(r) > 1
            and non_empty
            and not is_numeric
            and len(set(non_empty)) == 1
            and len(r) == len(non_empty)
        ):
            first_c = non_empty[0]
            cat_text = f"**{first_c}**" if not first_c.startswith("**") else first_c
            cleaned_grid.append([cat_text] + [""] * (len(r) - 1))
        else:
            cleaned_grid.append(r)

    max_cols = max(len(r) for r in cleaned_grid)
    normalized_grid: list[list[str]] = [
        [re.sub(r"[\r\n]+", "<br>", c).strip() for c in r] + [""] * (max_cols - len(r))
        for r in cleaned_grid
    ]
    alignments: list[str] = []
    for c_idx in range(max_cols):
        vals = [r[c_idx] for r in normalized_grid[1:] if r[c_idx].strip()]
        is_num = bool(
            vals and all(re.match(r"^[0-9\.,\-\+\s%±]+$", v.replace("<br>", " ")) for v in vals)
        )
        alignments.append(":---:" if is_num else ":---")

    lines = [
        "| " + " | ".join(normalized_grid[0]) + " |",
        "| " + " | ".join(alignments) + " |",
    ] + ["| " + " | ".join(r) + " |" for r in normalized_grid[1:]]
    return ("\n".join(lines) + "\n\n", normalized_grid)


def render_table_markdown(
    table: Any, rid_to_katex: dict[str, str] | None = None
) -> tuple[str, list[str], list[list[str]]]:
    """Render a docx Table object as a GitHub Flavored Markdown table with smart column alignment and footnote extraction."""
    grid: list[list[str]] = []
    footnotes: list[str] = []
    for row in table.rows:
        row_rendered = _render_table_row_cells(row, rid_to_katex, footnotes)
        if not row_rendered or not any(row_rendered):
            continue
        if is_table_footnote_row(row_rendered):
            _extract_footnote_row(row_rendered, footnotes)
            continue
        grid.append(row_rendered)
    if not grid:
        return ("", footnotes, [])
    md_str, normalized_grid = _normalize_and_format_grid(grid)
    return (md_str, footnotes, normalized_grid)


def _replace_eq_frac(m: re.Match[str]) -> str:
    """Convert Word EQ \\f(num,den) field into LaTeX \\frac{num}{den}."""
    num, den = m.group(1).strip(), m.group(2).strip()
    if re.match(r"^[A-Z][a-z0-9]$", num):
        num = f"{num[0]}_{num[1]}"
    if re.match(r"^[A-Z][a-z0-9]$", den):
        den = f"{den[0]}_{den[1]}"
    for g_char, g_latex in GREEK_MAP.items():
        num = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", lambda _m, gl=g_latex: f"{gl} ", num)
        num = num.replace(g_char, g_latex)
        den = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", lambda _m, gl=g_latex: f"{gl} ", den)
        den = den.replace(g_char, g_latex)
    return f"\\frac{{{num}}}{{{den}}}"


def _replace_eq_root(m: re.Match[str]) -> str:
    """Convert Word EQ \\r(n,x) field into LaTeX \\sqrt[n]{x}."""
    content = m.group(1).strip()
    if "," in content:
        parts = [p.strip() for p in content.split(",", 1)]
        return f"\\sqrt{{{parts[1]}}}" if not parts[0] else f"\\sqrt[{parts[0]}]{{{parts[1]}}}"
    return f"\\sqrt{{{content}}}"


def clean_formula_latex(raw_f: str) -> str:
    """Sanitize formula expressions by stripping unescaped inner dollars and standardizing operators."""
    f = raw_f.replace("$$", "").replace("$", " ").strip()
    for _ in range(5):
        prev = f
        f = re.sub(r"\\r\(([^()]+)\)", _replace_eq_root, f, flags=re.IGNORECASE)
        f = re.sub(r"(?:eq|EQ)?\s*\\f\(([^(),]+),([^(),]+)\)", _replace_eq_frac, f)
        if f == prev:
            break
    f = re.sub(r"^(?:eq|EQ)\s+", "", f).strip()
    ops = {
        "≤": r" \le ",
        "≥": r" \ge ",
        "<=": r" \le ",
        ">=": r" \ge ",
        "≠": r" \ne ",
        "≈": r" \approx ",
        "±": r" \pm ",
        "∓": r" \mp ",
        "×": r" \times ",
        "·": r" \cdot ",
        "÷": r" \div ",
        "…": r" \dots ",
    }
    for op, repl in ops.items():
        f = f.replace(op, repl)
    greek_cmds = r"\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|eta|theta|lambda|mu|nu|xi|pi|rho|sigma|tau|varphi|psi|omega|Delta|Sigma|Omega)"
    f = re.sub(rf"({greek_cmds})([0-9])", r"\1 \2", f)
    f = re.sub(r"\\le\s+ft\b", r"\\left", f)
    f = re.sub(r"\\le\s+q\b", r"\\le", f)
    f = re.sub(r"\\ge\s+[qt]\b", r"\\ge", f)
    return re.sub(r"\s+", " ", f).strip()


def _unpack_formula_override(val: Any, default_fid: str) -> tuple[str, str]:
    """Unpack formula override entry from tuple, dict, or raw string."""
    if isinstance(val, tuple):
        return val[0], val[1]
    if isinstance(val, dict):
        return val.get("formula_id", default_fid), val.get("latex", "")
    return default_fid, str(val)


def _emit_formula_frame_row(ctx: Any, f_tag: str, r: Any) -> None:
    """Resolve and emit a single formula row from a borderless formula frame table."""
    f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_")
    default_fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
    cell_rids = [
        rid for c in r.cells for rid in re.findall(r'r:(?:id|embed)="([^"]+)"', c._element.xml)
    ]
    if f_tag in ctx.formula_overrides:
        fid, f_latex = _unpack_formula_override(ctx.formula_overrides[f_tag], default_fid)
    elif matched_rid := next((rid for rid in cell_rids if rid in ctx.formula_overrides), None):
        fid, f_latex = _unpack_formula_override(ctx.formula_overrides[matched_rid], default_fid)
    else:
        fid = default_fid
        raw_f = next(
            (
                render_paragraph_with_runs(c.paragraphs[0], rid_to_katex=ctx.rid_to_katex)
                if c.paragraphs
                else c.text.strip()
                for c in r.cells
                if c.text.strip() and not re.match(r"^\([0-9A-Za-z\.]+\)$", c.text.strip())
            ),
            None,
        ) or next(
            (
                ctx.rid_to_katex[rid]
                for rid in cell_rids
                if ctx.rid_to_katex and rid in ctx.rid_to_katex
            ),
            None,
        )
        f_latex = clean_formula_latex(raw_f) if raw_f else f"\\text{{Formula }} ({f_tag})"

    f_latex = f_latex.strip()
    if f_latex.startswith("$$") and f_latex.endswith("$$"):
        f_latex = f_latex[2:-2].strip()
    f_latex = re.sub(r"\\qquad\s*\([^)]+\)", "", re.sub(r"\\tag\{[^}]+\}", "", f_latex)).strip()
    ctx.emit(
        f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \\qquad ({f_tag})$$\n<!-- formula_id: "{fid}" -->\n\n'
    )


def _handle_formula_frame_table(ctx: Any, tbl: Any) -> bool:
    """Detect and emit borderless formula frame tables; return True if handled."""
    all_row_formulas: list[tuple[str, Any]] = []
    for r in tbl.rows:
        f_tag = next(
            (
                m.group(1)
                for c in r.cells
                if (m := re.match(r"^\(([0-9A-Za-zĐđ\.]+)\)$", c.text.strip()))
            ),
            None,
        )
        if f_tag:
            all_row_formulas.append((f_tag, r))
    if not all_row_formulas or len(all_row_formulas) != len(tbl.rows):
        return False
    for f_tag, r in all_row_formulas:
        _emit_formula_frame_row(ctx, f_tag, r)
    if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
        ctx.state_mgr.reset()
    return True


def _build_table_slug(current_part: str | None, t_num: str) -> str:
    """Build normalized table slug from part identifier and table number."""
    norm_num = (
        f"{int(t_num):02d}"
        if t_num.isdigit()
        else t_num.lower().replace(".", "_").replace("-", "_")
    )
    return f"bang_{current_part}_{norm_num}" if current_part else f"bang_{norm_num}"


def _emit_annex_table_caption(ctx: Any) -> tuple[bool, str, str, str]:
    """Generate and emit synthetic table caption for uncaptioned annex tables."""
    annex_tbl_count = getattr(ctx, "_annex_tbl_count", {})
    count = annex_tbl_count.get(ctx.current_target, 0) + 1
    annex_tbl_count[ctx.current_target] = count
    ctx._annex_tbl_count = annex_tbl_count
    suffix = f"_{count}" if count > 1 else ""
    t_num = f"PL{ctx.current_target}{suffix}"
    t_cap = f"Bảng Phụ lục {ctx.current_target}" + (f" (Phần {count})" if count > 1 else "")
    t_slug = f"bang_phu_luc_{ctx.current_target.lower()}{suffix}"
    ctx.emit(f'\n<a id="bang-{t_slug.replace("_", "-")}"></a>\n### {t_cap}\n\n')
    return True, t_num, t_cap, t_slug


def _resolve_table_caption_and_slug(
    ctx: Any, i: int, blocks: list[Any] | None
) -> tuple[bool, str, str, str]:
    """Resolve table caption, number, and slug, emitting heading anchor if captioned."""
    if ctx.last_table_caption:
        t_num, t_cap = ctx.last_table_caption_num or "", ctx.last_table_caption or ""
        ctx.last_table_caption, ctx.last_table_caption_num = None, None
        ctx.state_mgr.reset()
        t_slug = _build_table_slug(ctx.current_part, t_num)
        ctx.emit(f'\n<a id="bang-{t_slug.replace("_", "-")}"></a>\n### {t_cap}\n\n')
        return True, t_num, t_cap, t_slug

    if blocks and i > 0 and blocks[i - 1][0] == "p":
        prev_p_text = blocks[i - 1][1].text.strip()
        if m_tbl_ref := re.search(
            r"(?:theo|ở|tại)\s+(?:bảng|Bảng|BẢNG)\s+([0-9A-Za-zĐđ]+(?:\.[0-9A-Za-zĐđ]+)*)\b",
            prev_p_text,
        ):
            t_num = m_tbl_ref.group(1)
            t_cap = f"Bảng {t_num}"
            t_slug = _build_table_slug(ctx.current_part, t_num)
            ctx.emit(f'\n<a id="bang-{t_slug.replace("_", "-")}"></a>\n### {t_cap}\n\n')
            return True, t_num, t_cap, t_slug

    if ctx.current_target != "main":
        return _emit_annex_table_caption(ctx)
    return False, "", "", f"layout_tbl_{i:03d}"


def _emit_single_column_layout_table(ctx: Any, tbl: Any) -> None:
    """Emit paragraphs from an uncaptioned single-column layout table directly into prose."""
    seen_cell_ids: set[int] = set()
    for row in tbl.rows:
        for cell in row.cells:
            if (cell_id := id(cell._tc)) in seen_cell_ids:
                continue
            seen_cell_ids.add(cell_id)
            for p in cell.paragraphs:
                p_r = render_paragraph_with_runs(p, rid_to_katex=ctx.rid_to_katex)
                if not p_r:
                    continue
                if p_r.startswith(("- ", "– ", "— ", "• ")):
                    p_r = "&nbsp;&nbsp;\\- " + p_r.lstrip("-–—• ")
                elif p_r.startswith(("+ ", "+")):
                    p_r = "&nbsp;&nbsp;&nbsp;&nbsp;\\+ " + p_r.lstrip("+ ")
                elif re.match(
                    r"^(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*", p_r, re.IGNORECASE
                ):
                    p_r = re.sub(
                        r"^(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*",
                        lambda m: (
                            f"**CHÚ THÍCH {m.group(1)}:** " if m.group(1) else "**CHÚ THÍCH:** "
                        ),
                        p_r,
                        flags=re.IGNORECASE,
                    )
                elif re.match(
                    r"^(?:CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[:–-]\s*", p_r, re.IGNORECASE
                ):
                    p_r = re.sub(
                        r"^(?:CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[:–-]\s*",
                        lambda m: f"**CHÚ DẪN {m.group(1)}:** " if m.group(1) else "**CHÚ DẪN:** ",
                        p_r,
                        flags=re.IGNORECASE,
                    )
                ctx.emit(f"{p_r}\n\n")
    ctx.state_mgr.reset()


def _parse_structured_footnotes(tbl_footnotes: list[str]) -> dict[str, str]:
    """Parse footnote list into symbol-keyed dictionary for JSON export."""
    parsed_footnotes: dict[str, str] = {}
    sym_pat = r"(\([0-9\*\+a-zA-Z]+\)|\[[0-9\*\+a-zA-Z]+\]|<sup\b[^>]*>[0-9\*\+a-zA-Z\)]+</sup>)"
    for fn in tbl_footnotes:
        if m_sym := re.search(sym_pat, fn):
            parsed_footnotes[m_sym.group(1)] = fn.strip()
        elif m_ct := re.search(r"\*\*CHÚ\s+THÍCH\s+([0-9]+):\*\*", fn):
            parsed_footnotes[f"{m_ct.group(1)})"] = fn.strip()
        else:
            parsed_footnotes[f"fn_{len(parsed_footnotes) + 1}"] = fn.strip()
    return parsed_footnotes


def _build_table_json_rows(
    raw_grid: list[list[str]], tbl_footnotes: list[str]
) -> tuple[list[list[str]], list[str], list[dict[str, Any]]]:
    """Decouple trailing footnote rows and extract stripped headers and row dictionaries."""
    cleaned_raw_grid: list[list[str]] = []
    for r in raw_grid:
        if is_table_footnote_row(r):
            if (fn_txt := "\n".join(c.strip() for c in r if c.strip())) not in tbl_footnotes:
                tbl_footnotes.append(fn_txt)
            continue
        cleaned_raw_grid.append(r)
    headers = [re.sub(r"<[^>]+>", "", h).strip() for h in cleaned_raw_grid[0]]
    json_rows = [
        {
            "_row_id": r_idx,
            **{
                (
                    headers[c_idx]
                    if c_idx < len(headers) and headers[c_idx]
                    else f"col_{c_idx + 1}"
                ): re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", val)).strip()
                for c_idx, val in enumerate(row)
            },
        }
        for r_idx, row in enumerate(cleaned_raw_grid[1:], 1)
    ]
    return cleaned_raw_grid, headers, json_rows


def _export_captioned_table_artifacts(
    ctx: Any,
    tbl: Any,
    t_num: str,
    t_cap: str,
    t_slug: str,
    raw_grid: list[list[str]],
    tbl_footnotes: list[str],
) -> None:
    """Export captioned table data to CSV and JSON files and record in ctx.tables_extracted."""
    csv_dir, json_dir = ctx.bundle_dir / "tables" / "csv", ctx.bundle_dir / "tables" / "json"
    csv_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    table_text = " ".join(c.text.lower() for row in tbl.rows for c in row.cells)
    archetype = detect_table_archetype(
        rows_count=len(tbl.rows),
        cols_count=len(raw_grid[0]) if raw_grid else 1,
        text=f"{t_cap} {table_text}",
        is_captioned=True,
        has_images=any("<img" in c or "figures/" in c for row in raw_grid for c in row),
        has_footnotes=bool(tbl_footnotes),
    )
    cleaned_raw_grid, headers, json_rows = _build_table_json_rows(raw_grid, tbl_footnotes)
    with open(csv_dir / f"{t_slug}.csv", "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(cleaned_raw_grid)

    table_json_dict: dict[str, Any] = {
        "table_id": t_slug,
        "table_number": t_num,
        "table_title": t_cap,
        "archetype": archetype,
        "headers": headers,
        "rows": json_rows,
        "footnotes": _parse_structured_footnotes(tbl_footnotes) or tbl_footnotes,
    }
    table_extracted_entry: dict[str, Any] = {
        "table_id": t_slug,
        "table_number": t_num,
        "title": t_cap,
        "archetype": archetype,
        "csv_file": f"tables/csv/{t_slug}.csv",
        "json_file": f"tables/json/{t_slug}.json",
    }
    if ctx.current_part:
        table_json_dict["part_id"] = table_extracted_entry["part_id"] = ctx.current_part
    with open(json_dir / f"{t_slug}.json", "w", encoding="utf-8") as f:
        json.dump(table_json_dict, f, ensure_ascii=False, indent=2)
    ctx.tables_extracted.append(table_extracted_entry)


def handle_table_block(ctx: Any, tbl: Any, i: int, blocks: list[Any] | None = None) -> None:
    """Parse a docx table block, checking for formula frames and exporting tables to CSV/JSON."""
    if _handle_formula_frame_table(ctx, tbl):
        return
    is_captioned, t_num, t_cap, t_slug = _resolve_table_caption_and_slug(ctx, i, blocks)
    md_tbl_str, tbl_footnotes, raw_grid = render_table_markdown(tbl, rid_to_katex=ctx.rid_to_katex)
    if not is_captioned and len(raw_grid[0] if raw_grid else []) <= 1:
        _emit_single_column_layout_table(ctx, tbl)
        return
    ctx.emit(md_tbl_str)
    if tbl_footnotes:
        bq_blocks = [
            "\n".join(f"> {line}" if line.strip() else ">" for line in fn.splitlines())
            for fn in tbl_footnotes
        ]
        ctx.emit("\n>\n".join(bq_blocks) + "\n\n")
    ctx.state_mgr.reset()
    if is_captioned and raw_grid:
        _export_captioned_table_artifacts(ctx, tbl, t_num, t_cap, t_slug, raw_grid, tbl_footnotes)
