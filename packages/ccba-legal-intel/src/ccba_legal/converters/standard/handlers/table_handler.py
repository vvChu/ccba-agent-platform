# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Table Handler & 2D Matrix Exporter for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import csv
import json
import re
from typing import Any

from ccba_legal.converters.standard.models import HierarchyState


def resolve_hierarchical_headers(grid: list[list[str]]) -> list[list[str]]:
    """Combine multi-row table headers (e.g. category spans) into structured single-row headers."""
    if len(grid) < 2:
        return grid

    row0 = grid[0]
    row1 = grid[1]

    # Check if row0 has merged spans where row1 has distinct sub-values
    has_subheaders = False
    for c in range(len(row0)):
        if c > 0 and row0[c] == row0[c - 1] and row1[c] != row1[c - 1]:
            has_subheaders = True
            break

    if has_subheaders:
        combined_header = []
        for c in range(len(row0)):
            h0 = row0[c].strip()
            h1 = row1[c].strip()
            if h0 and h1 and h0 != h1 and h1 not in ("—", "-", ""):
                combined_header.append(f"{h0} — {h1}")
            else:
                combined_header.append(h0 or h1)
        return [combined_header] + grid[2:]
    return grid


def render_table_markdown(
    table: Any, rid_to_katex: dict[str, str] | None = None
) -> tuple[str, list[str], list[list[str]]]:
    """Render a docx Table object as a GitHub Flavored Markdown table with smart column alignment and footnote extraction."""
    from ccba_legal.converters.standard.strategy import render_paragraph_with_runs

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
            row_rendered.append(clean_cell)

        if not row_rendered or not any(row_rendered):
            continue

        first_cell = row_rendered[0].strip()
        if re.match(
            r"^(?:<br>)*\s*(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)", first_cell, re.IGNORECASE
        ):
            combined_fn = "<br>".join([c for c in row_rendered if c.strip()])
            fn_parts = [p.strip() for p in re.split(r"<br\s*/?>", combined_fn) if p.strip()]
            has_explicit_numbered = any(
                re.search(r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*[2-9]", p, re.IGNORECASE)
                for p in fn_parts
            )

            for idx, fn_p in enumerate(fn_parts):
                fn_clean = re.sub(
                    r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)?\s*[:–-]\s*(?:\*\*)?\s*",
                    "",
                    fn_p,
                    flags=re.IGNORECASE,
                ).strip()
                fn_clean = re.sub(r"^\*\*\s*", "", fn_clean).strip()
                m_num = re.search(
                    r"^(?:\*\*)?(?:CHÚ\s+THÍCH|Chú\s+thích)\s*([0-9]+)", fn_p, flags=re.IGNORECASE
                )
                if m_num and m_num.group(1):
                    pfx = f"**CHÚ THÍCH {m_num.group(1)}:**"
                elif has_explicit_numbered and idx == 0:
                    pfx = "**CHÚ THÍCH 1:**"
                elif len(fn_parts) > 1 and not has_explicit_numbered:
                    pfx = f"**CHÚ THÍCH {idx + 1}:**"
                else:
                    pfx = "**CHÚ THÍCH:**"
                footnotes.append(f"{pfx} {fn_clean}")
            continue

        grid.append(row_rendered)

    if not grid:
        return ("", footnotes, [])

    # Resolve hierarchical 2-tier headers without dropping columns
    grid = resolve_hierarchical_headers(grid)

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
    ops = {
        "≤": r" \le ",
        "≥": r" \ge ",
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


def handle_table_block(ctx: Any, tbl: Any, i: int) -> None:
    """Parse a docx table block, checking for formula frames and exporting tables to CSV/JSON."""
    from ccba_legal.converters.standard.strategy import render_paragraph_with_runs

    # 1. Formula Frame Check
    all_row_formulas: list[tuple[str, Any]] = []
    for r in tbl.rows:
        r_texts = [c.text.strip() for c in r.cells]
        f_tag = next(
            (m.group(1) for t in r_texts if (m := re.match(r"^\(([0-9A-Za-z\.]+)\)$", t))), None
        )
        if f_tag:
            all_row_formulas.append((f_tag, r))

    if all_row_formulas and len(all_row_formulas) == len(tbl.rows):
        for f_tag, r in all_row_formulas:
            f_slug = f_tag.lower().replace(".", "_")
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
            tag_suffix = (
                "" if ("\\tag" in f_latex or "\\qquad" in f_latex) else f" \\tag{{{f_tag}}}"
            )
            ctx.emit(
                f'\n<a id="formula-{f_slug}"></a>\n$${f_latex}{tag_suffix}$$\n<!-- formula_id: "{fid}" -->\n\n'
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
                key = (
                    headers[c_idx]
                    if c_idx < len(headers) and headers[c_idx]
                    else f"col_{c_idx + 1}"
                )
                row_dict[key] = re.sub(r"<[^>]+>", "", val).strip()
            json_rows.append(row_dict)

        with open(json_dir / f"{t_slug}.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "table_id": t_slug,
                    "table_number": t_num,
                    "table_title": t_cap,
                    "rows": json_rows,
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
                "csv_file": f"tables/csv/{t_slug}.csv",
                "json_file": f"tables/json/{t_slug}.json",
            }
        )
