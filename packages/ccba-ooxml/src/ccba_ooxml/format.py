"""Formatting and styling engine for OpenXML documents (DOCX).

Provides deterministic typography, page setup, paragraph styling, table formatting,
and Markdown-to-DOCX conversion according to CCBA / Vietnamese administrative standards.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor
from pydantic import BaseModel


class FormattingProfile(BaseModel):
    """Configuration profile for formatting a DOCX document."""

    font_name: str = "Times New Roman"
    font_size_pt: float = 13.0
    line_spacing: float = 1.15
    paragraph_before_pt: float = 6.0
    paragraph_after_pt: float = 3.0
    first_line_indent_cm: float = 1.0
    margin_top_cm: float = 2.5
    margin_bottom_cm: float = 2.5
    margin_left_cm: float = 3.0
    margin_right_cm: float = 2.0
    page_width_cm: float = 21.0
    page_height_cm: float = 29.7
    header_distance_cm: float = 1.5
    footer_distance_cm: float = 1.5


def _set_font_all(style: Any, font_name: str = "Times New Roman") -> None:
    """Set font on both run properties and eastAsia/cs."""
    style.font.name = font_name
    rpr = style.element.find(qn("w:rPr"))
    if rpr is None:
        rpr = parse_xml(f"<w:rPr {nsdecls('w')}/>")
        style.element.append(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = parse_xml(f"<w:rFonts {nsdecls('w')}/>")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font_name)


def _add_shading(element: Any, color: str) -> None:
    """Add background shading to a paragraph element."""
    pPr = element.find(qn("w:pPr"))
    if pPr is None:
        pPr = parse_xml(f"<w:pPr {nsdecls('w')}/>")
        element.insert(0, pPr)
    for old in pPr.findall(qn("w:shd")):
        pPr.remove(old)
    pPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}" w:val="clear"/>'))


def _add_border_box(element: Any, color: str = "CCCCCC") -> None:
    """Add a border box around a paragraph."""
    pPr = element.find(qn("w:pPr"))
    if pPr is None:
        pPr = parse_xml(f"<w:pPr {nsdecls('w')}/>")
        element.insert(0, pPr)
    for old in pPr.findall(qn("w:pBdr")):
        pPr.remove(old)
    pPr.append(
        parse_xml(
            f"<w:pBdr {nsdecls('w')}>\n"
            f'  <w:top w:val="single" w:sz="4" w:space="4" w:color="{color}"/>\n'
            f'  <w:left w:val="single" w:sz="4" w:space="8" w:color="{color}"/>\n'
            f'  <w:bottom w:val="single" w:sz="4" w:space="4" w:color="{color}"/>\n'
            f'  <w:right w:val="single" w:sz="4" w:space="8" w:color="{color}"/>\n'
            f"</w:pBdr>"
        )
    )


def _add_bottom_border(element: Any, color: str = "1B5E20", size: str = "6") -> None:
    """Add a bottom border line under a paragraph."""
    pPr = element.find(qn("w:pPr"))
    if pPr is None:
        pPr = parse_xml(f"<w:pPr {nsdecls('w')}/>")
        element.insert(0, pPr)
    for old in pPr.findall(qn("w:pBdr")):
        pPr.remove(old)
    pPr.append(
        parse_xml(
            f"<w:pBdr {nsdecls('w')}>\n"
            f'  <w:bottom w:val="single" w:sz="{size}" w:space="3" w:color="{color}"/>\n'
            f"</w:pBdr>"
        )
    )


def _add_hr_border(element: Any) -> None:
    """Style empty paragraph as a horizontal rule."""
    pPr = element.find(qn("w:pPr"))
    if pPr is None:
        pPr = parse_xml(f"<w:pPr {nsdecls('w')}/>")
        element.insert(0, pPr)
    for old in pPr.findall(qn("w:pBdr")):
        pPr.remove(old)
    pPr.append(
        parse_xml(
            f"<w:pBdr {nsdecls('w')}>\n"
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="CCCCCC"/>\n'
            f"</w:pBdr>"
        )
    )


def format_docx(
    input_path: Path | str,
    output_path: Path | str | None = None,
    profile: FormattingProfile | None = None,
) -> Path:
    """Apply deterministic typography and layout styles to a Word (.docx) document.

    Args:
        input_path: Path to source DOCX file.
        output_path: Path to destination DOCX file (defaults to overwrite input_path).
        profile: Custom FormattingProfile (defaults to standard CCBA profile).

    Returns:
        Path object pointing to the formatted DOCX file.
    """
    in_file = Path(input_path)
    out_file = Path(output_path) if output_path is not None else in_file
    p = profile or FormattingProfile()

    doc = Document(str(in_file))

    # 1. Page Setup
    for section in doc.sections:
        section.top_margin = Cm(p.margin_top_cm)
        section.bottom_margin = Cm(p.margin_bottom_cm)
        section.left_margin = Cm(p.margin_left_cm)
        section.right_margin = Cm(p.margin_right_cm)
        section.page_width = Cm(p.page_width_cm)
        section.page_height = Cm(p.page_height_cm)
        section.header_distance = Cm(p.header_distance_cm)
        section.footer_distance = Cm(p.footer_distance_cm)

    # 2. Bullet Overrides in numbering.xml
    numbering_part = None
    for rel in doc.part.rels.values():
        if "numbering" in rel.reltype:
            numbering_part = rel.target_part
            break
    if numbering_part is not None:
        num_xml = numbering_part.element
        for abstractNum in num_xml.findall(qn("w:abstractNum")):
            for lvl in abstractNum.findall(qn("w:lvl")):
                ilvl_val = lvl.get(qn("w:ilvl"), "0")
                numFmt = lvl.find(qn("w:numFmt"))
                if numFmt is not None and numFmt.get(qn("w:val")) == "bullet":
                    lvlText = lvl.find(qn("w:lvlText"))
                    rPr = lvl.find(qn("w:rPr"))
                    if rPr is None:
                        rPr = parse_xml(f"<w:rPr {nsdecls('w')}/>")
                        lvl.append(rPr)
                    for old_rf in rPr.findall(qn("w:rFonts")):
                        rPr.remove(old_rf)
                    rPr.append(
                        parse_xml(
                            f'<w:rFonts {nsdecls("w")} w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
                        )
                    )
                    if lvlText is not None:
                        if ilvl_val == "0":
                            lvlText.set(qn("w:val"), "\u2013")
                        elif ilvl_val == "1":
                            lvlText.set(qn("w:val"), "\u25cf")

    # 3. Base Styles
    styles = doc.styles
    if "Normal" in styles:
        normal = styles["Normal"]
        _set_font_all(normal, p.font_name)
        normal.font.size = Pt(p.font_size_pt)
        normal.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        pf = normal.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = Cm(p.first_line_indent_cm)
        pf.space_before = Pt(p.paragraph_before_pt)
        pf.space_after = Pt(p.paragraph_after_pt)
        pf.line_spacing = p.line_spacing

    if "Heading 1" in styles:
        h1 = styles["Heading 1"]
        _set_font_all(h1, p.font_name)
        h1.font.size = Pt(16)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
        h1f = h1.paragraph_format
        h1f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h1f.space_before = Pt(24)
        h1f.space_after = Pt(12)
        h1f.first_line_indent = Cm(0)
        h1f.keep_with_next = True

    if "Heading 2" in styles:
        h2 = styles["Heading 2"]
        _set_font_all(h2, p.font_name)
        h2.font.size = Pt(14)
        h2.font.bold = True
        h2.font.color.rgb = RGBColor(0x1B, 0x5E, 0x20)
        h2f = h2.paragraph_format
        h2f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        h2f.space_before = Pt(18)
        h2f.space_after = Pt(6)
        h2f.first_line_indent = Cm(0)
        h2f.keep_with_next = True

    if "Heading 3" in styles:
        h3 = styles["Heading 3"]
        _set_font_all(h3, p.font_name)
        h3.font.size = Pt(13)
        h3.font.bold = True
        h3.font.color.rgb = RGBColor(0x00, 0x69, 0x7A)
        h3f = h3.paragraph_format
        h3f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        h3f.space_before = Pt(12)
        h3f.space_after = Pt(4)
        h3f.first_line_indent = Cm(0)
        h3f.keep_with_next = True

    # 4. Paragraph formatting & decorations
    has_chapters = any(p_item.text.strip().startswith("CHƯƠNG") for p_item in doc.paragraphs)

    for idx, para in enumerate(doc.paragraphs):
        style_name = para.style.name if para.style else ""
        text = para.text.strip()

        for run in para.runs:
            if not run.font.name:
                run.font.name = p.font_name
            rpr = run._element.find(qn("w:rPr"))
            if rpr is not None:
                rf = rpr.find(qn("w:rFonts"))
                if rf is not None:
                    for attr in ("w:eastAsia", "w:cs"):
                        rf.set(qn(attr), p.font_name)

        if "code" in style_name.lower() or style_name in ("Source Code", "Verbatim Char"):
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            para.paragraph_format.first_line_indent = Cm(0)
            _add_shading(para._element, "F0F4F8")
            _add_border_box(para._element, "D0D8E0")
            continue

        if style_name.startswith("Heading"):
            para.paragraph_format.first_line_indent = Cm(0)
            if style_name == "Heading 1":
                if has_chapters:
                    para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    para.paragraph_format.page_break_before = idx > 0
                else:
                    para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    para.paragraph_format.page_break_before = False
            elif style_name == "Heading 2":
                _add_bottom_border(para._element, "1B5E20", "4")
            continue

        if "block" in style_name.lower() or "quote" in style_name.lower():
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.first_line_indent = Cm(0)
            para.paragraph_format.left_indent = Cm(0.3)
            _add_shading(para._element, "E8F4FD")
            continue

        p_elem = para._element
        has_drawing = bool(p_elem.findall(".//" + qn("w:drawing")))
        if has_drawing:
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.first_line_indent = Cm(0)
        elif not text:
            para.paragraph_format.first_line_indent = Cm(0)
            prev_style = doc.paragraphs[idx - 1].style if idx > 0 else None
            prev_is_h = (
                prev_style is not None
                and hasattr(prev_style, "name")
                and str(prev_style.name).startswith("Heading")
            )
            next_style = doc.paragraphs[idx + 1].style if idx < len(doc.paragraphs) - 1 else None
            next_is_h = (
                next_style is not None
                and hasattr(next_style, "name")
                and str(next_style.name).startswith("Heading")
            )
            if not prev_is_h and not next_is_h:
                _add_hr_border(para._element)
        elif style_name.startswith("List") or style_name in ("Compact", "List Paragraph"):
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.first_line_indent = Cm(0)
            para.paragraph_format.left_indent = Cm(0.8)
        else:
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.first_line_indent = Cm(p.first_line_indent_cm)

    # 4b. Chapter cover pages
    cover_groups = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text.startswith("CHƯƠNG"):
            title_idx = i + 1 if i + 1 < len(doc.paragraphs) else None
            cover_groups.append((i, title_idx))

    for group_idx, (ch_idx, title_idx) in enumerate(cover_groups):
        para = doc.paragraphs[ch_idx]
        para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.first_line_indent = Cm(0)
        para.paragraph_format.space_before = Pt(200)
        para.paragraph_format.space_after = Pt(24)
        para.paragraph_format.page_break_before = group_idx > 0
        for run in para.runs:
            run.font.size = Pt(32)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
            run.font.name = p.font_name

        if title_idx is not None:
            title_para = doc.paragraphs[title_idx]
            title_para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_para.paragraph_format.first_line_indent = Cm(0)
            title_para.paragraph_format.space_before = Pt(0)
            title_para.paragraph_format.space_after = Pt(200)
            title_para.paragraph_format.page_break_before = False
            for run in title_para.runs:
                run.font.size = Pt(28)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
                run.font.name = p.font_name

    # 5. Tables
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl = table._tbl
        tblPr = tbl.find(qn("w:tblPr"))
        if tblPr is None:
            tblPr = parse_xml(f"<w:tblPr {nsdecls('w')}/>")
            tbl.insert(0, tblPr)

        for old in tblPr.findall(qn("w:tblW")):
            tblPr.remove(old)
        tblPr.append(parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>'))

        for old in tblPr.findall(qn("w:tblBorders")):
            tblPr.remove(old)
        tblPr.append(
            parse_xml(
                f"<w:tblBorders {nsdecls('w')}>\n"
                f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>\n'
                f"</w:tblBorders>"
            )
        )

        for old in tblPr.findall(qn("w:tblCellMar")):
            tblPr.remove(old)
        tblPr.append(
            parse_xml(
                f"<w:tblCellMar {nsdecls('w')}>\n"
                f'  <w:top w:w="60" w:type="dxa"/>\n'
                f'  <w:left w:w="100" w:type="dxa"/>\n'
                f'  <w:bottom w:w="60" w:type="dxa"/>\n'
                f'  <w:right w:w="100" w:type="dxa"/>\n'
                f"</w:tblCellMar>"
            )
        )

        for i, row in enumerate(table.rows):
            for cell in row.cells:
                tcPr = cell._tc.find(qn("w:tcPr"))
                if tcPr is None:
                    tcPr = parse_xml(f"<w:tcPr {nsdecls('w')}/>")
                    cell._tc.insert(0, tcPr)

                for para in cell.paragraphs:
                    para.paragraph_format.first_line_indent = Cm(0)
                    for run in para.runs:
                        run.font.name = p.font_name
                        run.font.size = Pt(11)
                    if i == 0:
                        para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in para.runs:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    else:
                        para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

                for old in tcPr.findall(qn("w:shd")):
                    tcPr.remove(old)
                if i == 0:
                    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="1565C0" w:val="clear"/>'))
                else:
                    bg = "F5F5F5" if i % 2 == 1 else "FFFFFF"
                    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg}" w:val="clear"/>'))

    out_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_file))
    return out_file


def convert_md_to_docx(
    md_path: Path | str,
    output_path: Path | str | None = None,
    title: str | None = None,
) -> Path:
    """Convert Markdown text or file into formatted Word DOCX.

    Args:
        md_path: Path to Markdown file or markdown text content.
        output_path: Destination DOCX file path.
        title: Optional title for cover page.

    Returns:
        Path to generated DOCX file.
    """
    path_obj = Path(md_path)
    if path_obj.exists() and path_obj.is_file():
        md_text = path_obj.read_text(encoding="utf-8")
        if output_path is None:
            output_path = path_obj.with_suffix(".docx")
    else:
        md_text = str(md_path)
        if output_path is None:
            output_path = Path("output.docx")

    out_file = Path(output_path)
    doc = Document()

    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_title.add_run(title)
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)

    for line in md_text.splitlines():
        striped = line.strip()
        if not striped:
            continue
        if striped.startswith("### "):
            doc.add_heading(striped[4:], level=3)
        elif striped.startswith("## "):
            doc.add_heading(striped[3:], level=2)
        elif striped.startswith("# "):
            doc.add_heading(striped[2:], level=1)
        else:
            para = doc.add_paragraph()
            # Simple bold/italic parsing
            tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", striped)
            for token in tokens:
                if not token:
                    continue
                if token.startswith("**") and token.endswith("**"):
                    r = para.add_run(token[2:-2])
                    r.bold = True
                elif token.startswith("*") and token.endswith("*"):
                    r = para.add_run(token[1:-1])
                    r.italic = True
                else:
                    para.add_run(token)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_file))
    return format_docx(out_file, out_file)


__all__ = [
    "FormattingProfile",
    "format_docx",
    "convert_md_to_docx",
]
