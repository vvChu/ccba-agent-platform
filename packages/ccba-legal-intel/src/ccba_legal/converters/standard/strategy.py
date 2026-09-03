# Copyright (c) 2026 CCBA. All rights reserved.
"""Modular Technical Standard Strategy Converter (OKF v2.4 - ADR 0030, ADR 0034, ADR 0036)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docx import Document

from ccba_legal.converters.standard.handlers.figure_handler import handle_figure_card
from ccba_legal.converters.standard.handlers.formula_handler import handle_formula_block
from ccba_legal.converters.standard.handlers.heading_handler import handle_structural_heading
from ccba_legal.converters.standard.handlers.list_handler import handle_list_and_paragraph
from ccba_legal.converters.standard.handlers.table_handler import (
    handle_table_block,
)
from ccba_legal.converters.standard.models import HierarchyState
from ccba_legal.converters.standard.state_manager import HierarchyStateManager
from ccba_legal.converters.technical_formulas import (
    GREEK_MAP,
    INLINE_SYMBOLS_MAP,
    load_bundle_formula_overrides,
)
from ccba_legal.figure_extractor import (
    extract_docx_figures,
    render_markdown_figure_card,
)
from ccba_legal.formula_harvester import harvest_docx_formula_images
from ccba_legal.gold_standard import generate_bundle_ast_and_qa


def sanitize_prose_greeks_and_variables(text: str) -> str:
    """Sanitize Vietnamese prose text by converting raw Greek letters and subscripts into KaTeX math mode."""
    if not text:
        return text

    for g_char, g_latex in GREEK_MAP.items():
        pattern = r"(?<!\$)\b" + g_char + r"([a-zA-Z0-9]+)\b(?!\$)"
        text = re.sub(pattern, lambda m, gl=g_latex: f"${gl}_{{{m.group(1)}}}$", text)
        pattern_alone = r"(?<![\$\w])" + g_char + r"(?![\$\w])"
        text = re.sub(pattern_alone, lambda m, gl=g_latex: f"${gl}$", text)

    for var in [
        "qk,t",
        "Qk,t",
        "qk,qper",
        "Wk",
        "W0",
        "Gk",
        "Qk",
        "QL",
        "Qt",
        "Ad",
        "ze",
        "zs",
        "Gf",
    ]:
        k_var = var.replace(",", "_{").replace("0", "_0")
        if "_" in k_var and not k_var.endswith("}"):
            k_var += "}"
        elif len(var) > 1 and "_" not in k_var:
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
                    clean_k = k_sym.strip("$ ")
                    if "<!--" in clean_k:
                        clean_k = clean_k.split("<!--")[0].strip("$ \n\r")
                    grouped.append(("norm", f"${clean_k}$"))
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
            trailing_space = " " if text.endswith(" ") else ""
            out_tokens.append(f"${wrap}${trailing_comma}{trailing_space}")
        else:
            out_tokens.append(text)

    res = "".join(out_tokens)
    res = re.sub(
        r"([a-zA-ZÀ-ɏẠ-ỹͰ-Ͽ]+)\$(_\{[^}]+\}|_[a-zA-Z0-9,]+|\^\{[^}]+\}|\^[a-zA-Z0-9]+)\$",
        r"$\1\2$",
        res,
    )
    res = re.sub(
        r"\$([^$]+)\$", lambda m: f"${''.join(GREEK_MAP.get(c, c) for c in m.group(1))}$", res
    )
    # Heal orphaned strain subscripts like $_{b}$, $_{b1}$, $_{s}$
    res = re.sub(r"\$(_\{b[0-9]*\})\$", r"$\\varepsilon\1$", res)
    res = re.sub(r"\$(_\{s[0-9]*\})\$", r"$\\varepsilon\1$", res)
    res = re.sub(r"([0-9])\s*≤\s*(_\{[^}]+\})", r"\1 ≤ $\\varepsilon\2$", res)
    res = re.sub(r"([0-9])\s*<=\s*(_\{[^}]+\})", r"\1 <= $\\varepsilon\2$", res)
    res = res.replace("$$", "").replace("$_$", "").replace("$^$", "")
    res = re.sub(r"\$([\\a-zA-Z0-9][^$]*?)\$([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])", r"$\1$ \2", res)
    return res.strip()


@dataclass
class StandardConversionContext:
    """State machine container for technical standard conversions."""

    bundle_dir: Path
    output_filename: str | None
    rid_to_katex: dict[str, str] = field(default_factory=dict)
    body_md_parts: list[str] = field(default_factory=list)
    annex_buffers: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_target: str = "main"
    last_table_caption: str | None = None
    last_table_caption_num: str | None = None
    last_table_unit: str | None = None
    tables_extracted: list[dict[str, Any]] = field(default_factory=list)
    state_mgr: HierarchyStateManager = field(default_factory=HierarchyStateManager)
    formula_overrides: dict[str, Any] = field(default_factory=dict)
    doc_meta: dict[str, Any] = field(default_factory=dict)

    @property
    def active_parts(self) -> list[str]:
        """Return the active markdown parts buffer."""
        if self.current_target == "main":
            return self.body_md_parts
        return self.annex_buffers[self.current_target]["parts"]

    def emit(self, chunk: str) -> None:
        """Emit a markdown chunk to either the main body buffer or the active modular annex buffer."""
        self.active_parts.append(chunk)


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


def _find_standard_header_start_index(blocks: list[tuple[str, Any]]) -> int:
    """Find the index where the actual Standard/Quy chuẩn technical document begins,
    skipping any preceding administrative Circular (Thông tư ban hành) wrapper."""
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
                or t
                in (
                    "TIÊU CHUẨN QUỐC GIA",
                    "QUY CHUẨN KỸ THUẬT QUỐC GIA",
                )
                or t.startswith("QUY CHUẨN KỸ THUẬT QUỐC GIA")
            ):
                return idx
    return 0


def _find_normative_start_index(blocks: list[tuple[str, Any]], start_from: int = 0) -> int:
    """Locate the exact start index of the normative body (Section 1)."""
    in_toc = False
    for idx in range(start_from, len(blocks)):
        b_type, obj = blocks[idx]
        if b_type == "p":
            txt = obj.text.strip().upper()
            if txt in ("MỤC LỤC", "## MỤC LỤC"):
                in_toc = True
                continue
            if in_toc and txt.startswith("LỜI NÓI ĐẦU"):
                in_toc = False
            if in_toc:
                continue
            if re.match(r"^1[\.\s]+(?:QUY ĐỊNH CHUNG|PHẠM VI ÁP DỤNG)\b", txt):
                return idx

    for idx in range(start_from, len(blocks)):
        b_type, obj = blocks[idx]
        if b_type == "p":
            txt = obj.text.strip().upper()
            if re.match(r"^1[\.\s]+(?:QUY ĐỊNH CHUNG|PHẠM VI ÁP DỤNG)\b", txt):
                return idx
    return start_from


def _emit_figure_or_comment(ctx: StandardConversionContext, comment_str: str) -> None:
    """Render figure card from HTML comment if matching FIGURE format, else emit raw comment."""
    m_fig = re.match(r"^<!--\s*FIGURE:\s*([^|]+)\|(.*)-->$", comment_str.strip())
    if m_fig:
        fig_slug = m_fig.group(1).strip()
        fig_title = m_fig.group(2).strip().rstrip("-").strip()
        fig_num = fig_slug.replace("hinh_", "").replace("_", ".").upper()
        fig_entry = {
            "tag": fig_num,
            "title": fig_title,
            "anchor": fig_slug.replace("_", "-"),
            "image_relpath": f"figures/images/{fig_slug}.png",
            "geometry_rules": {},
        }
        ctx.emit(render_markdown_figure_card(fig_entry))
    else:
        ctx.emit(f"\n{comment_str}\n\n")


def _process_paragraph_block(
    ctx: StandardConversionContext, blocks: list[tuple[str, Any]], i: int
) -> int:
    """Dispatches a single paragraph block to the specialized handlers."""
    obj = blocks[i][1]
    text = obj.text.strip()
    if not text:
        # Check if the empty paragraph contains standalone formula images/drawings (e.g. MathType equations)
        xml = obj._element.xml
        rids = re.findall(r'r:(?:id|embed)="([^"]+)"', xml)
        if rids:
            for rid in rids:
                if rid in ctx.formula_overrides:
                    val = ctx.formula_overrides[rid]
                    if isinstance(val, tuple):
                        fid, f_latex = val[0], val[1]
                    elif isinstance(val, dict):
                        fid = val.get(
                            "formula_id", f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}"
                        )
                        f_latex = val.get("latex", "")
                    else:
                        fid = f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}"
                        f_latex = str(val)
                    f_latex = f_latex.strip()
                    if not f_latex:
                        return i + 1
                    if f_latex.startswith("<!--"):
                        _emit_figure_or_comment(ctx, f_latex)
                        ctx.state_mgr.reset()
                        return i + 1
                    if f_latex.startswith("$$") and f_latex.endswith("$$"):
                        f_latex = f_latex[2:-2].strip()
                    ctx.emit(f'\n$${f_latex}$$\n<!-- formula_id: "{fid}" -->\n\n')
                    if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
                        ctx.state_mgr.reset()
                    return i + 1
                elif ctx.rid_to_katex and rid in ctx.rid_to_katex:
                    raw_k = ctx.rid_to_katex[rid].strip()
                    if not raw_k:
                        return i + 1
                    if raw_k.startswith("<!--"):
                        _emit_figure_or_comment(ctx, raw_k)
                        ctx.state_mgr.reset()
                        return i + 1
                    fid = f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}"
                    f_latex = (
                        raw_k[2:-2].strip()
                        if (raw_k.startswith("$$") and raw_k.endswith("$$"))
                        else raw_k
                    )
                    ctx.emit(f'\n$${f_latex}$$\n<!-- formula_id: "{fid}" -->\n\n')
                    if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
                        ctx.state_mgr.reset()
                    return i + 1
        return i + 1

    rendered_p = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)

    # 1. Formula Handler
    res_f = handle_formula_block(ctx, blocks, i, text, obj, rendered_p)
    if res_f is not None:
        return res_f

    # 2. Structural Headings & Notes Handler
    res_h = handle_structural_heading(ctx, blocks, i, text, rendered_p, obj)
    if res_h is not None:
        return res_h

    # 3. Figure Card Handler
    res_fig = handle_figure_card(ctx, text, i)
    if res_fig is not None:
        return res_fig

    # 4. List Hierarchy & Paragraph Handler
    return handle_list_and_paragraph(ctx, blocks, i, text, rendered_p, obj)


def _process_table_block(ctx: StandardConversionContext, table_obj: Any, i: int) -> None:
    """Extract and render tabular data into 2D Markdown, CSV, and JSON."""
    handle_table_block(ctx, table_obj, i)


def _export_modular_annexes_and_moc(ctx: StandardConversionContext) -> dict[str, Any]:
    """Export modular annex files, 2D navigation matrix, tables catalog, and AST index."""
    # 1. Export Annexes
    from ccba_legal.table_cleaner import clean_markdown_tables_and_notes

    if ctx.annex_buffers:
        annexes_dir = ctx.bundle_dir / "annexes"
        annexes_dir.mkdir(parents=True, exist_ok=True)
        nav_rows: list[str] = []
        for a_letter, a_info in ctx.annex_buffers.items():
            annex_slug, annex_title, annex_type, annex_anchor = (
                a_info["slug"],
                a_info["title"],
                a_info["type"],
                a_info["anchor"],
            )
            annex_md = (
                "".join(a_info["parts"])
                .replace("figures/images/", "../figures/images/")
                .replace("tables/", "../tables/")
            )
            annex_md = clean_markdown_tables_and_notes(annex_md)
            (annexes_dir / f"{annex_slug}.md").write_text(annex_md, encoding="utf-8")
            nav_rows.append(
                f"| **Phụ lục {a_letter}** | {annex_title} | {annex_type} | [📑 **Xem Phụ lục**](annexes/{annex_slug}.md#{annex_anchor}) |"
            )

        nav_matrix = [
            "\n---\n",
            f"## 📑 DANH MỤC PHỤ LỤC KỸ THUẬT CHUYÊN ĐỀ (MODULAR ANNEXES)\n\nToàn bộ {len(ctx.annex_buffers)} Phụ lục kỹ thuật chuyên đề đã được module hóa thành các tệp độc lập nhằm tối ưu hóa tra cứu và thẩm tra thiết kế (ADR 0021 & ADR 0030):\n",
            "| Ký hiệu | Tên Phụ Lục | Tính chất | Liên kết Tập tin |",
            "| :---: | :--- | :---: | :---: |",
        ]
        nav_matrix.extend(nav_rows)
        nav_matrix.append(
            f"\n---\n\n## 📊 HỆ THỐNG TRA CỨU BẢNG & SƠ ĐỒ KỸ THUẬT\n\n- **Tra cứu {len(ctx.tables_extracted)} Bảng Số Liệu:** Tra cứu chi tiết dạng CSV/JSON tại [Thư mục Bảng Số Liệu](tables/README.md).\n- **Tra cứu Sơ Đồ Hình Vẽ:** Tra cứu ảnh nét cao và đặc tả phân vùng tại [Danh Mục Sơ Đồ Khí Động](figures/figures_catalog.yaml).\n\n"
        )
        ctx.body_md_parts.append("\n".join(nav_matrix))

    # 2. Write Primary Markdown
    out_name = ctx.output_filename or f"{ctx.bundle_dir.name}.md"
    target_md_path = ctx.bundle_dir / out_name
    final_body_md = clean_markdown_tables_and_notes("".join(ctx.body_md_parts))
    if not final_body_md.strip().startswith("---"):
        frontmatter = _build_frontmatter_yaml(ctx.bundle_dir, ctx.doc_meta)
        final_body_md = frontmatter + final_body_md
    target_md_path.write_text(final_body_md, encoding="utf-8")

    # 3. Export Tables Catalog & README
    if ctx.tables_extracted:
        tables_dir = ctx.bundle_dir / "tables"
        with open(tables_dir / "tables_catalog.json", "w", encoding="utf-8") as f:
            json.dump(
                {"total_tables": len(ctx.tables_extracted), "tables": ctx.tables_extracted},
                f,
                ensure_ascii=False,
                indent=2,
            )

        tbl_readme = [
            "# DANH MỤC BẢNG TRA CỨU KỸ THUẬT 2D (OKF v2.2)\n",
            "| Mã bảng | Tên bảng | CSV | JSON |",
            "| :--- | :--- | :---: | :---: |",
        ]
        for t in ctx.tables_extracted:
            tbl_readme.append(
                f"| {t['table_id']} | {t['title']} | [CSV]({t['csv_file']}) | [JSON]({t['json_file']}) |"
            )
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


def _build_frontmatter_yaml(bundle_dir: Path, doc_meta: dict[str, Any] | None = None) -> str:
    """Build standard OKF v2.4 YAML frontmatter for technical standard/QCVN document."""
    meta_file = bundle_dir / "metadata.yaml"
    m_data: dict[str, Any] = {}
    if meta_file.exists():
        try:
            import yaml

            loaded = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                m_data = loaded
        except Exception:
            pass
    if doc_meta:
        for k, v in doc_meta.items():
            if k not in m_data or not m_data[k]:
                m_data[k] = v

    doc_id = m_data.get("id", bundle_dir.name)
    doc_num = m_data.get("document_number", bundle_dir.name.replace("_", " ").upper())
    title = m_data.get("title", f"{doc_num} — {doc_id}")
    issued_by = m_data.get("issued_by", "Bộ Xây dựng")
    signer = m_data.get("signer", "")
    issued_date = m_data.get("issued_date", "")
    effective_date = m_data.get("effective_date", "")
    status = m_data.get("status", "active")
    cong_bao = m_data.get("cong_bao_number", "Đang cập nhật")
    pdf_path = m_data.get("pdf_path", f"./sources/{bundle_dir.name}.pdf")
    pdf_name = Path(pdf_path).name
    pdf_sha = m_data.get("pdf_sha256", "")

    replaces = (
        m_data.get("relations", {}).get("replaces", [])
        if isinstance(m_data.get("relations"), dict)
        else m_data.get("replaces", [])
    )

    fm_dict: dict[str, Any] = {
        "okf_version": "2.4",
        "type": "technical_standard_qcvn"
        if "qcvn" in bundle_dir.name.lower()
        else "technical_standard_tcvn",
        "title": title,
        "description": title,
        "tags": [
            "qcvn" if "qcvn" in bundle_dir.name.lower() else "tcvn",
            "quy_chuan_ky_thuat" if "qcvn" in bundle_dir.name.lower() else "tieu_chuan_ky_thuat",
        ],
        "timestamp": "2026-08-26T00:00:00Z",
        "resource": f"legal_docs/02_qcvn/{bundle_dir.name}/{bundle_dir.name}.md"
        if "qcvn" in bundle_dir.name.lower()
        else f"legal_docs/03_tcvn/{bundle_dir.name}/{bundle_dir.name}.md",
        "id": doc_id,
        "doc_id": doc_id,
        "document_number": doc_num,
        "document_type": m_data.get("type", "Quy chuẩn kỹ thuật quốc gia"),
        "issued_by": issued_by,
        "signer": signer,
        "issued_date": str(issued_date),
        "effective_date": str(effective_date),
        "status": status,
        "pdf_anchor": {
            "path": f"./sources/{pdf_name}",
            "sha256": pdf_sha,
            "cong_bao_number": cong_bao,
        },
    }
    if replaces:
        fm_dict["relations"] = {"replaces": replaces}
    fm_dict["artifacts"] = {
        "tables_dir": "./tables/",
        "tables_catalog": "./tables/tables_catalog.json",
        "benchmark_file": "./qa_benchmark.json",
        "figures_dir": "./figures/",
    }

    import yaml

    return (
        "---\n"
        + yaml.dump(fm_dict, allow_unicode=True, sort_keys=False, indent=2).strip()
        + "\n---\n\n"
    )


def process_technical_standard_strategy(
    docx_path: Path | str,
    bundle_dir: Path | str,
    output_filename: str | None = None,
    rid_to_katex: dict[str, str] | None = None,
    registry_file: Path | str | None = None,
    doc_meta: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Process a Technical Standard (TCVN / QCVN) DOCX file with 100% Visual Parity & Modular Annex Split."""
    docx_p = Path(docx_path)
    bundle_p = Path(bundle_dir)
    bundle_p.mkdir(parents=True, exist_ok=True)

    # 1. Harvest formulas and extract figures
    cache_dir = (
        bundle_p.parents[2] / ".md" / "cache" / "formula_vision"
        if len(bundle_p.parents) >= 3
        else bundle_p / ".cache"
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    skip_vis = os.environ.get("AI_SKIP_VISION") == "1"
    docx_rid_to_katex = rid_to_katex or harvest_docx_formula_images(
        docx_p, cache_dir=cache_dir, skip_vision=skip_vis
    )
    extract_docx_figures(docx_p, bundle_p / "figures")

    # 2. Extract and locate normative start
    doc = Document(docx_p)
    blocks = _extract_document_blocks(doc)
    std_start_idx = _find_standard_header_start_index(blocks)
    start_idx = _find_normative_start_index(blocks, start_from=std_start_idx)

    # 3. Process blocks with conversion context
    ctx = StandardConversionContext(
        bundle_dir=bundle_p,
        output_filename=output_filename,
        rid_to_katex=docx_rid_to_katex,
        formula_overrides=load_bundle_formula_overrides(bundle_p),
        doc_meta=doc_meta or kwargs.get("doc_meta") or {},
    )

    if start_idx > std_start_idx:
        preamble_parts: list[str] = []
        for p_idx in range(std_start_idx, start_idx):
            b_type, obj = blocks[p_idx]
            if b_type == "p":
                t = obj.text.strip()
                if t:
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
