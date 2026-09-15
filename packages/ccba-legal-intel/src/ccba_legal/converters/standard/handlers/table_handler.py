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
        content = m.group(1)
        content = re.sub(r"(?<!\\)\|", r"\\vert ", content)
        return f"${content}$"

    res = re.sub(r"\$([^$]+)\$", _rep_math, text)
    res = re.sub(r"(?<!\\)\|", r"\|", res)
    return res


def build_composite_headers(header_rows: list[list[str]]) -> list[str]:
    """Combine multi-row table headers (2 to 4 tiers) into single composite headers."""
    if not header_rows:
        return []
    cols_count = len(header_rows[0])
    composite: list[str] = []
    for c in range(cols_count):
        tokens: list[str] = []
        for r in range(len(header_rows)):
            val = re.sub(r"<[^>]+>", " ", header_rows[r][c]).strip()
            val = re.sub(r"\s+", " ", val).strip()
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

    max_h = min(5, len(grid))
    header_rows_count = 1

    for r_idx in range(1, max_h):
        prev_row = grid[r_idx - 1]
        curr_row = grid[r_idx]

        # Stop if Col 0 is an enumerated data item like (a), (b), (1), etc.
        if (
            re.match(r"^\(?[a-zđ0-9]+\)?$", curr_row[0].strip(), re.IGNORECASE)
            and curr_row[0].strip() != prev_row[0].strip()
        ):
            break

        # Check if Col 0 is a continuation of the header stub label
        c0_same = bool(curr_row[0].strip() and curr_row[0].strip() == prev_row[0].strip())

        has_subheaders = False
        for c in range(len(prev_row)):
            if (
                c > 0
                and prev_row[c]
                and prev_row[c] == prev_row[c - 1]
                and curr_row[c] != curr_row[c - 1]
            ):
                has_subheaders = True
                break

        non_empty = [c.strip() for c in curr_row if c.strip()]
        is_category_partition = len(set(non_empty)) == 1 and len(non_empty) > 1

        if (has_subheaders or c0_same) and not is_category_partition:
            if not c0_same and re.match(r"^[0-9\.,\-\+±%]+$", curr_row[0].strip().replace(" ", "")):
                break
            header_rows_count = r_idx + 1
        else:
            break

    if header_rows_count > 1:
        header_rows = grid[:header_rows_count]
        combined_header = build_composite_headers(header_rows)
        return [combined_header] + grid[header_rows_count:]

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
        admin_keywords = [
            "cộng hòa xã hội chủ nghĩa",
            "độc lập - tự do",
            "độc lập tự do",
            "nơi nhận:",
            "ký, ghi rõ họ tên",
            "ký, đóng dấu",
            "thủ trưởng đơn vị",
        ]
        if any(k in lower_t for k in admin_keywords):
            return "BORDERLESS_LAYOUT"
    if not is_captioned and any(
        k in lower_t
        for k in ["[ ]", "☐", "biên bản", "phiếu kiểm tra", "mẫu số", "chức vụ của người ký"]
    ):
        return "ADMIN_FORM"
    if has_images or "<img" in lower_t:
        return "IN_CELL_MULTIMODAL"
    if header_rows_count > 1:
        return "HIERARCHICAL_GRID"
    if has_footnotes or "chú thích" in lower_t:
        return "FOOTNOTE_RICH"
    return "FLAT_MATRIX"


def render_table_markdown(
    table: Any, rid_to_katex: dict[str, str] | None = None
) -> tuple[str, list[str], list[list[str]]]:
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
                        p_r = "&nbsp;&nbsp;\\- " + p_r.lstrip("-–—• ")
                    elif p_r.startswith(("+ ", "+")):
                        p_r = "&nbsp;&nbsp;&nbsp;&nbsp;\\+ " + p_r.lstrip("+ ")
                    cell_p_rendered.append(p_r)
            clean_cell = "<br>".join(cell_p_rendered)
            clean_cell = re.sub(r"[\r\n]+", "<br>", clean_cell).strip()
            clean_cell = escape_table_pipes(clean_cell)
            clean_cell = re.sub(r"(?<!\$)\$\$(?!\$)", "$ $", clean_cell)
            row_rendered.append(clean_cell)

        if not row_rendered or not any(row_rendered):
            continue

        # Extract squashed footnotes from any cell in this row (ADR 0030 / ADR 0041)
        for c_idx, cell_str in enumerate(row_rendered):
            if re.search(r"<br>\s*(?:\*\*)?(?:CHÚ\s+THÍCH|CHÚ\s+DẪN)", cell_str, re.IGNORECASE):
                parts = re.split(
                    r"<br>\s*(?=(?:\*\*)?(?:CHÚ\s+THÍCH|CHÚ\s+DẪN))", cell_str, flags=re.IGNORECASE
                )
                row_rendered[c_idx] = parts[0].strip()
                for note_p in parts[1:]:
                    note_clean = re.sub(r"^<br\s*/?>", "", note_p).strip()
                    note_lines = [
                        line_part.strip()
                        for line_part in re.split(r"<br\s*/?>", note_clean)
                        if line_part.strip()
                    ]
                    for nl in note_lines:
                        footnotes.append(nl)

        first_cell = row_rendered[0].strip()
        first_cell_clean = re.sub(r"^(?:<!--.*?-->|<[^>]+>|\s)+", "", first_cell)
        if re.match(
            r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)",
            first_cell_clean,
            re.IGNORECASE,
        ):
            # Deduplicate identical merged cells across columns (gridSpan)
            unique_cells: list[str] = []
            for c in row_rendered:
                c_str = c.strip()
                if c_str and c_str not in unique_cells:
                    unique_cells.append(c_str)
            combined_fn = "<br>".join(unique_cells)
            raw_parts = [p.strip() for p in re.split(r"<br\s*/?>", combined_fn) if p.strip()]
            fn_parts: list[str] = []
            seen_clean: set[str] = set()
            for p in raw_parts:
                p_clean = re.sub(
                    r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[\.:–-]\s*(?:\*\*)?\s*",
                    "",
                    p,
                    flags=re.IGNORECASE,
                ).strip()
                p_clean = re.sub(r"^\*\*\s*", "", p_clean).strip()
                if not p_clean:
                    continue

                # Normalize 40$^{0}$ C -> 40 °C
                p_clean = re.sub(r"(\d+)\$\^\{0\}\$\s*C\b", r"\1 °C", p_clean)

                is_bullet = bool(
                    re.match(r"^(?:[-–—•\+]|\*+|\(\*+\)|\([0-9a-zA-Z]+\)|[0-9]+[)\.])\s*", p_clean)
                )
                if fn_parts and not is_bullet:
                    last_txt = fn_parts[-1].strip()
                    if last_txt.endswith(
                        ("≤", "≥", "=", "<", ">", ",", ":", "-", "–", "—", "với", "là")
                    ) or re.match(r"^[0-9\.,]+", p_clean):
                        fn_parts[-1] = f"{last_txt} {p_clean}"
                        continue

                if p_clean and p_clean not in seen_clean:
                    seen_clean.add(p_clean)
                    fn_parts.append(p_clean)
            has_explicit_numbered = any(
                re.search(
                    r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*[1-9]",
                    p,
                    re.IGNORECASE,
                )
                or re.match(r"^[0-9]+[)\.]\s+", p)
                for p in fn_parts
            )

            if has_explicit_numbered:
                bullet_lines: list[str] = []
                numbered_lines: list[str] = []
                for _idx, fn_p in enumerate(fn_parts):
                    fn_clean = re.sub(
                        r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[\.:–-]\s*(?:\*\*)?\s*",
                        "",
                        fn_p,
                        flags=re.IGNORECASE,
                    ).strip()
                    fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
                    if not fn_clean:
                        continue

                    m_num = re.search(
                        r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích|CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)",
                        fn_p,
                        flags=re.IGNORECASE,
                    )
                    if not m_num:
                        m_num = re.match(r"^([0-9]+)[)\.]\s*", fn_p)

                    is_star_bullet = bool(
                        re.match(r"^\*+\s*", fn_clean) or re.match(r"^\*+\s*", fn_p)
                    )

                    if is_star_bullet and not m_num:
                        bullet_lines.append(fn_clean)
                    elif m_num and m_num.group(1):
                        fn_clean = re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()
                        pfx = f"**CHÚ THÍCH {m_num.group(1)}:**"
                        numbered_lines.append(f"{pfx} {fn_clean}")
                    else:
                        fn_clean = re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()
                        curr_num = len(numbered_lines) + 1
                        pfx = f"**CHÚ THÍCH {curr_num}:**"
                        numbered_lines.append(f"{pfx} {fn_clean}")

                if bullet_lines:
                    fn_block: list[str] = ["**CHÚ THÍCH:**"]
                    for bl in bullet_lines:
                        b_txt = bl.lstrip("*–—•- ").strip()
                        fn_block.append(f"&nbsp;&nbsp;\\- {b_txt}")
                    footnotes.append("\n".join(fn_block))

                for nl in numbered_lines:
                    footnotes.append(nl)
            else:
                if len(fn_parts) == 1:
                    fn_clean = re.sub(
                        r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*[:–-]\s*(?:\*\*)?\s*",
                        "",
                        fn_parts[0],
                        flags=re.IGNORECASE,
                    ).strip()
                    fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
                    footnotes.append(f"**CHÚ THÍCH:** {fn_clean}")
                else:
                    block_lines: list[str] = ["**CHÚ THÍCH:**"]
                    for fn_p in fn_parts:
                        fn_clean = re.sub(
                            r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*[:–-]\s*(?:\*\*)?\s*",
                            "",
                            fn_p,
                            flags=re.IGNORECASE,
                        ).strip()
                        fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
                        if not fn_clean:
                            continue
                        if fn_clean.startswith(
                            ("- ", "– ", "— ", "• ", "* ")
                        ) or fn_clean.startswith("&nbsp;&nbsp;\\- "):
                            b_txt = fn_clean.replace("&nbsp;&nbsp;\\- ", "").lstrip("-–—•* ")
                            block_lines.append(f"&nbsp;&nbsp;\\- {b_txt}")
                        elif fn_clean.startswith("$$") or (
                            fn_clean.startswith("$")
                            and fn_clean.endswith("$")
                            and len(fn_clean) > 10
                        ):
                            f_txt = fn_clean.strip()
                            if (
                                f_txt.startswith("$")
                                and not f_txt.startswith("$$")
                                and f_txt.endswith("$")
                                and not f_txt.endswith("$$")
                            ):
                                f_txt = f"$${f_txt[1:-1]}$$"
                            block_lines.append(f_txt)
                        else:
                            b_txt = fn_clean.lstrip("-–—•* ")
                            block_lines.append(f"&nbsp;&nbsp;\\- {b_txt}")
                    footnotes.append("\n\n".join(block_lines))
            continue

        grid.append(row_rendered)

    if not grid:
        return ("", footnotes, [])

    # Resolve hierarchical 2-tier headers without dropping columns
    grid = resolve_hierarchical_headers(grid)

    # Deduplicate full-width category/subheader rows spanning all columns
    cleaned_grid: list[list[str]] = []
    for r_idx, r in enumerate(grid):
        non_empty = [c.strip() for c in r if c.strip()]
        if (
            r_idx > 0
            and len(r) > 1
            and non_empty
            and len(set(non_empty)) == 1
            and len(r) == len(non_empty)
        ):
            first_c = non_empty[0]
            cat_text = f"**{first_c}**" if not first_c.startswith("**") else first_c
            cleaned_grid.append([cat_text] + [""] * (len(r) - 1))
        else:
            cleaned_grid.append(r)
    grid = cleaned_grid

    max_cols = max(len(r) for r in grid)
    normalized_grid: list[list[str]] = [
        [re.sub(r"[\r\n]+", "<br>", c).strip() for c in r] + [""] * (max_cols - len(r))
        for r in grid
    ]

    alignments: list[str] = []
    for c_idx in range(max_cols):
        vals = [r[c_idx] for r in normalized_grid[1:] if r[c_idx].strip()]
        is_num = (
            all(re.match(r"^[0-9\.,\-\+\s%±]+$", v.replace("<br>", " ")) for v in vals)
            if vals
            else False
        )
        alignments.append(":---:" if is_num else ":---")

    lines: list[str] = [
        "| " + " | ".join(normalized_grid[0]) + " |",
        "| " + " | ".join(alignments) + " |",
    ]
    for r in normalized_grid[1:]:
        lines.append("| " + " | ".join(r) + " |")

    return ("\n".join(lines) + "\n\n", footnotes, normalized_grid)


def clean_formula_latex(raw_f: str) -> str:
    """Sanitize formula expressions by stripping unescaped inner dollars and standardizing operators."""
    f = raw_f.replace("$$", "").replace("$", " ").strip()

    def _rep_eq_frac(m: re.Match[str]) -> str:
        num = m.group(1).strip()
        den = m.group(2).strip()
        if re.match(r"^[A-Z][a-z0-9]$", num):
            num = f"{num[0]}_{num[1]}"
        if re.match(r"^[A-Z][a-z0-9]$", den):
            den = f"{den[0]}_{den[1]}"
        for g_char, g_latex in GREEK_MAP.items():

            def _rep_g_tbl(_m: re.Match[str], gl: str = g_latex) -> str:
                return f"{gl} "

            num = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", _rep_g_tbl, num)
            num = num.replace(g_char, g_latex)
            den = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", _rep_g_tbl, den)
            den = den.replace(g_char, g_latex)
        return f"\\frac{{{num}}}{{{den}}}"

    def _rep_root(m: re.Match[str]) -> str:
        content = m.group(1).strip()
        if "," in content:
            parts = [p.strip() for p in content.split(",", 1)]
            if not parts[0]:
                return f"\\sqrt{{{parts[1]}}}"
            return f"\\sqrt[{parts[0]}]{{{parts[1]}}}"
        return f"\\sqrt{{{content}}}"

    for _ in range(5):
        prev = f
        f = re.sub(r"\\r\(([^()]+)\)", _rep_root, f, flags=re.IGNORECASE)
        f = re.sub(r"(?:eq|EQ)?\s*\\f\(([^(),]+),([^(),]+)\)", _rep_eq_frac, f)
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
    # Restore any broken left/right/le/ge
    f = re.sub(r"\\le\s+ft\b", r"\\left", f)
    f = re.sub(r"\\le\s+q\b", r"\\le", f)
    f = re.sub(r"\\ge\s+q\b", r"\\ge", f)
    f = re.sub(r"\\ge\s+t\b", r"\\ge", f)
    return re.sub(r"\s+", " ", f).strip()


def handle_table_block(ctx: Any, tbl: Any, i: int, blocks: list[Any] | None = None) -> None:
    """Parse a docx table block, checking for formula frames and exporting tables to CSV/JSON."""
    # 1. Formula Frame Check
    all_row_formulas: list[tuple[str, Any]] = []
    for r in tbl.rows:
        r_texts = [c.text.strip() for c in r.cells]
        f_tag = next(
            (m.group(1) for t in r_texts if (m := re.match(r"^\(([0-9A-Za-zĐđ\.]+)\)$", t))), None
        )
        if f_tag:
            all_row_formulas.append((f_tag, r))

    if all_row_formulas and len(all_row_formulas) == len(tbl.rows):
        for f_tag, r in all_row_formulas:
            f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_")
            cell_rids: list[str] = []
            for c in r.cells:
                cell_rids.extend(re.findall(r'r:(?:id|embed)="([^"]+)"', c._element.xml))

            if f_tag in ctx.formula_overrides:
                val = ctx.formula_overrides[f_tag]
                if isinstance(val, tuple):
                    fid, f_latex = val[0], val[1]
                elif isinstance(val, dict):
                    fid = val.get(
                        "formula_id", f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                    )
                    f_latex = val.get("latex", "")
                else:
                    fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                    f_latex = str(val)
            elif any(rid in ctx.formula_overrides for rid in cell_rids):
                matched_rid = next(rid for rid in cell_rids if rid in ctx.formula_overrides)
                val = ctx.formula_overrides[matched_rid]
                if isinstance(val, tuple):
                    fid, f_latex = val[0], val[1]
                elif isinstance(val, dict):
                    fid = val.get(
                        "formula_id", f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                    )
                    f_latex = val.get("latex", "")
                else:
                    fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                    f_latex = str(val)
            else:
                fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                raw_f = next(
                    (
                        render_paragraph_with_runs(c.paragraphs[0], rid_to_katex=ctx.rid_to_katex)
                        if c.paragraphs
                        else c.text.strip()
                        for c in r.cells
                        if c.text.strip() and not re.match(r"^\([0-9A-Za-z\.]+\)$", c.text.strip())
                    ),
                    None,
                )
                if not raw_f:
                    for rid in cell_rids:
                        if ctx.rid_to_katex and rid in ctx.rid_to_katex:
                            raw_f = ctx.rid_to_katex[rid]
                            break
                f_latex = clean_formula_latex(raw_f) if raw_f else f"\\text{{Formula }} ({f_tag})"

            f_latex = f_latex.strip()
            if f_latex.startswith("$$") and f_latex.endswith("$$"):
                f_latex = f_latex[2:-2].strip()
            f_latex = re.sub(r"\\tag\{[^}]+\}", "", f_latex).strip()
            f_latex = re.sub(r"\\qquad\s*\([^)]+\)", "", f_latex).strip()
            ctx.emit(
                f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \\qquad ({f_tag})$$\n<!-- formula_id: "{fid}" -->\n\n'
            )
        if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
            ctx.state_mgr.reset()
        return

    # 2. Normative or Layout Table
    is_captioned = bool(ctx.last_table_caption)
    if is_captioned:
        t_num = ctx.last_table_caption_num or ""
        t_cap = ctx.last_table_caption or ""
        ctx.last_table_caption = None
        ctx.last_table_caption_num = None
        ctx.state_mgr.reset()
        t_slug = (
            f"bang_{int(t_num):02d}"
            if t_num.isdigit()
            else f"bang_{t_num.lower().replace('.', '_').replace('-', '_')}"
        )
        tbl_anchor = f"bang-{t_slug.replace('_', '-')}"
        ctx.emit(f'\n<a id="{tbl_anchor}"></a>\n### {t_cap}\n\n')
    elif not is_captioned and blocks and i > 0 and blocks[i - 1][0] == "p":
        prev_p_text = blocks[i - 1][1].text.strip()
        m_tbl_ref = re.search(
            r"(?:theo|ở|tại)\s+(?:bảng|Bảng|BẢNG)\s+([0-9A-Za-zĐđ]+(?:\.[0-9A-Za-zĐđ]+)*)\b",
            prev_p_text,
        )
        if m_tbl_ref:
            t_num = m_tbl_ref.group(1)
            t_cap = f"Bảng {t_num}"
            is_captioned = True
            t_slug = (
                f"bang_{int(t_num):02d}"
                if t_num.isdigit()
                else f"bang_{t_num.lower().replace('.', '_').replace('-', '_')}"
            )
            tbl_anchor = f"bang-{t_slug.replace('_', '-')}"
            ctx.emit(f'\n<a id="{tbl_anchor}"></a>\n### {t_cap}\n\n')
        elif ctx.current_target != "main":
            annex_tbl_count = getattr(ctx, "_annex_tbl_count", {})
            count = annex_tbl_count.get(ctx.current_target, 0) + 1
            annex_tbl_count[ctx.current_target] = count
            ctx._annex_tbl_count = annex_tbl_count
            suffix = f"_{count}" if count > 1 else ""
            t_num = f"PL{ctx.current_target}{suffix}"
            t_cap = f"Bảng Phụ lục {ctx.current_target}" + (f" (Phần {count})" if count > 1 else "")
            t_slug = f"bang_phu_luc_{ctx.current_target.lower()}{suffix}"
            tbl_anchor = f"bang-{t_slug.replace('_', '-')}"
            ctx.emit(f'\n<a id="{tbl_anchor}"></a>\n### {t_cap}\n\n')
            is_captioned = True
        else:
            t_num, t_cap = "", ""
            t_slug = f"layout_tbl_{i:03d}"
    elif ctx.current_target != "main":
        annex_tbl_count = getattr(ctx, "_annex_tbl_count", {})
        count = annex_tbl_count.get(ctx.current_target, 0) + 1
        annex_tbl_count[ctx.current_target] = count
        ctx._annex_tbl_count = annex_tbl_count
        suffix = f"_{count}" if count > 1 else ""
        t_num = f"PL{ctx.current_target}{suffix}"
        t_cap = f"Bảng Phụ lục {ctx.current_target}" + (f" (Phần {count})" if count > 1 else "")
        t_slug = f"bang_phu_luc_{ctx.current_target.lower()}{suffix}"
        tbl_anchor = f"bang-{t_slug.replace('_', '-')}"
        ctx.emit(f'\n<a id="{tbl_anchor}"></a>\n### {t_cap}\n\n')
        is_captioned = True
    else:
        t_num, t_cap = "", ""
        t_slug = f"layout_tbl_{i:03d}"

    md_tbl_str, tbl_footnotes, raw_grid = render_table_markdown(tbl, rid_to_katex=ctx.rid_to_katex)

    if not is_captioned and len(raw_grid[0] if raw_grid else []) <= 1:
        seen_cell_ids: set[int] = set()
        for row in tbl.rows:
            for cell in row.cells:
                cell_id = id(cell._tc)
                if cell_id in seen_cell_ids:
                    continue
                seen_cell_ids.add(cell_id)
                for p in cell.paragraphs:
                    p_r = render_paragraph_with_runs(p, rid_to_katex=ctx.rid_to_katex)
                    if p_r:
                        if p_r.startswith(("- ", "– ", "— ", "• ")):
                            p_r = "&nbsp;&nbsp;\\- " + p_r.lstrip("-–—• ")
                        elif p_r.startswith(("+ ", "+")):
                            p_r = "&nbsp;&nbsp;&nbsp;&nbsp;\\+ " + p_r.lstrip("+ ")
                        elif re.match(
                            r"^(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*",
                            p_r,
                            re.IGNORECASE,
                        ):
                            p_r = re.sub(
                                r"^(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*",
                                lambda m: f"**CHÚ THÍCH {m.group(1)}:** "
                                if m.group(1)
                                else "**CHÚ THÍCH:** ",
                                p_r,
                                flags=re.IGNORECASE,
                            )
                        elif re.match(
                            r"^(?:CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[:–-]\s*", p_r, re.IGNORECASE
                        ):
                            p_r = re.sub(
                                r"^(?:CHÚ\s+DẪN|Chú\s+dẫn)\s*([0-9]+)?\s*[:–-]\s*",
                                lambda m: f"**CHÚ DẪN {m.group(1)}:** "
                                if m.group(1)
                                else "**CHÚ DẪN:** ",
                                p_r,
                                flags=re.IGNORECASE,
                            )
                        ctx.emit(f"{p_r}\n\n")
        ctx.state_mgr.reset()
        return

    ctx.emit(md_tbl_str)
    if tbl_footnotes:
        bq_blocks: list[str] = []
        for fn in tbl_footnotes:
            lines = [f"> {line}" if line.strip() else ">" for line in fn.splitlines()]
            bq_blocks.append("\n".join(lines))
        ctx.emit("\n>\n".join(bq_blocks) + "\n\n")
    ctx.state_mgr.reset()

    # 3. Export CSV / JSON for captioned tables
    if is_captioned and raw_grid:
        tables_dir = ctx.bundle_dir / "tables"
        csv_dir = tables_dir / "csv"
        json_dir = tables_dir / "json"
        csv_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)

        table_text = " ".join(c.text.lower() for row in tbl.rows for c in row.cells)
        has_images = any("<img" in c or "figures/" in c for row in raw_grid for c in row)
        archetype = detect_table_archetype(
            rows_count=len(tbl.rows),
            cols_count=len(raw_grid[0]) if raw_grid else 1,
            text=f"{t_cap} {table_text}",
            is_captioned=is_captioned,
            has_images=has_images,
            has_footnotes=bool(tbl_footnotes),
        )

        with open(csv_dir / f"{t_slug}.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(raw_grid)

        headers = [re.sub(r"<[^>]+>", "", h).strip() for h in raw_grid[0]]
        json_rows: list[dict[str, Any]] = []
        for r_idx, row in enumerate(raw_grid[1:], 1):
            row_dict: dict[str, Any] = {"_row_id": r_idx}
            for c_idx, val in enumerate(row):
                key = (
                    headers[c_idx]
                    if c_idx < len(headers) and headers[c_idx]
                    else f"col_{c_idx + 1}"
                )
                clean_val = re.sub(r"<br\s*/?>", "\n", val)
                clean_val = re.sub(r"<[^>]+>", "", clean_val).strip()
                row_dict[key] = clean_val
            json_rows.append(row_dict)

        parsed_footnotes: dict[str, str] = {}
        for fn in tbl_footnotes:
            m_sym = re.search(r"(\([0-9\*\+a-zA-Z]+\)|\[[0-9\*\+a-zA-Z]+\])", fn)
            if m_sym:
                parsed_footnotes[m_sym.group(1)] = fn.strip()
            else:
                parsed_footnotes[f"fn_{len(parsed_footnotes) + 1}"] = fn.strip()

        with open(json_dir / f"{t_slug}.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "table_id": t_slug,
                    "table_number": t_num,
                    "table_title": t_cap,
                    "archetype": archetype,
                    "headers": headers,
                    "rows": json_rows,
                    "footnotes": parsed_footnotes or tbl_footnotes,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        ctx.tables_extracted.append(
            {
                "table_id": t_slug,
                "table_number": t_num,
                "title": t_cap,
                "archetype": archetype,
                "csv_file": f"tables/csv/{t_slug}.csv",
                "json_file": f"tables/json/{t_slug}.json",
            }
        )
