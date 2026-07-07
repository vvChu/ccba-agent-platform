"""
Script chuyển đổi MD sang DOCX theo format template
Sử dụng python-docx để tạo DOCX với format chuẩn văn bản hành chính
"""

import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def set_run_font(run, font_name="Times New Roman", font_size=12, bold=False, italic=False):
    """Set font properties for a run"""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    # Set font for Asian characters
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def add_paragraph_with_format(
    doc, text, alignment="left", font_size=12, bold=False, italic=False, spacing_after=6
):
    """Add a paragraph with specific formatting"""
    para = doc.add_paragraph()

    # Set alignment
    if alignment == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif alignment == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif alignment == "justify":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Set spacing
    para.paragraph_format.space_after = Pt(spacing_after)
    para.paragraph_format.line_spacing = 1.15

    # Add text with formatting
    run = para.add_run(text)
    set_run_font(run, font_size=font_size, bold=bold, italic=italic)

    return para


def parse_md_line(line):
    """Parse markdown formatting from a line"""
    # Remove ** for bold markers
    text = line.strip()
    is_bold = text.startswith("**") and "**" in text[2:]
    is_italic = text.startswith("*") and not text.startswith("**")

    # Clean markdown syntax
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # Remove bold markers
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # Remove italic markers

    return text, is_bold, is_italic


def add_mixed_paragraph(doc, text, alignment="justify", base_size=12, spacing_after=6):
    """Add paragraph with mixed bold/normal text"""
    para = doc.add_paragraph()

    if alignment == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif alignment == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif alignment == "justify":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    para.paragraph_format.space_after = Pt(spacing_after)
    para.paragraph_format.line_spacing = 1.15

    # Parse bold sections **text** and italic *text*
    pattern = r"(\*\*[^*]+\*\*|\*[^*]+\*|[^*]+)"
    parts = re.findall(pattern, text)

    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = para.add_run(part[2:-2])
            set_run_font(run, font_size=base_size, bold=True)
        elif part.startswith("*") and part.endswith("*") and not part.startswith("**"):
            run = para.add_run(part[1:-1])
            set_run_font(run, font_size=base_size, italic=True)
        else:
            run = para.add_run(part)
            set_run_font(run, font_size=base_size)

    return para


def convert_md_to_docx(md_file, output_file):
    """Convert MD file to DOCX with proper formatting"""

    # Read MD content
    with open(md_file, encoding="utf-8") as f:
        lines = f.readlines()

    # Create new document
    doc = Document()

    # Set up page margins (A4)
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(2)

    # Process lines
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Header: CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in line:
            add_paragraph_with_format(
                doc,
                "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
                alignment="center",
                font_size=14,
                bold=True,
            )
            i += 1
            continue

        # Độc lập - Tự do - Hạnh phúc
        if "Độc lập" in line and "Tự do" in line:
            add_paragraph_with_format(
                doc, "Độc lập - Tự do - Hạnh phúc", alignment="center", font_size=14, bold=True
            )
            i += 1
            continue

        # Date line (right aligned, italic)
        if line.startswith("Bình Dương, ngày"):
            add_paragraph_with_format(doc, line, alignment="right", font_size=12, italic=True)
            i += 1
            continue

        # Main title: ĐƠN TỐ CÁO TỘI PHẠM
        if "ĐƠN TỐ CÁO TỘI PHẠM" in line or "ĐƠN TỐ GIÁC TỘI PHẠM" in line:
            clean_title = line.replace("**", "")
            add_paragraph_with_format(
                doc, clean_title, alignment="center", font_size=14, bold=True, spacing_after=0
            )
            i += 1
            continue

        # Subtitle (italic, centered)
        if line.startswith("*Về hành vi"):
            clean_text = line.replace("*", "")
            add_paragraph_with_format(
                doc, clean_text, alignment="center", font_size=12, italic=True
            )
            i += 1
            continue

        # Section headers (I., II., III., etc.)
        if re.match(r"^\*\*[IVX]+\.", line):
            clean_text = line.replace("**", "")
            add_paragraph_with_format(
                doc, clean_text, alignment="left", font_size=12, bold=True, spacing_after=6
            )
            i += 1
            continue

        # Sub-headers within sections (1., 2., 3.)
        if re.match(r"^\*\*\d+\.", line):
            clean_text = line.replace("**", "")
            add_paragraph_with_format(
                doc, clean_text, alignment="left", font_size=12, bold=True, spacing_after=6
            )
            i += 1
            continue

        # Kính gửi
        if line.startswith("**Kính gửi:**"):
            add_paragraph_with_format(
                doc, "Kính gửi:", alignment="left", font_size=12, bold=True, spacing_after=0
            )
            i += 1
            continue

        # List items (- or numbered)
        if line.startswith("- ") or line.startswith("+ "):
            clean_text = line[2:].strip()
            para = add_mixed_paragraph(doc, "• " + clean_text, alignment="justify", base_size=12)
            para.paragraph_format.left_indent = Cm(0.5)
            i += 1
            continue

        # Numbered list items (1., 2., etc. at start)
        if re.match(r"^\d+\.\s", line):
            add_mixed_paragraph(doc, line, alignment="justify", base_size=12)
            i += 1
            continue

        # Sub-list items with indent
        if line.startswith("   -") or line.startswith("   +"):
            clean_text = line.strip()[2:].strip()
            para = add_mixed_paragraph(doc, "  ○ " + clean_text, alignment="justify", base_size=12)
            para.paragraph_format.left_indent = Cm(1)
            i += 1
            continue

        # Signature section
        if "CÔNG TY CỔ PHẦN NỀN TẢNG" in line:
            add_paragraph_with_format(doc, "", alignment="left", spacing_after=24)  # Space before
            add_paragraph_with_format(
                doc,
                "CÔNG TY CỔ PHẦN NỀN TẢNG",
                alignment="right",
                font_size=12,
                bold=True,
                spacing_after=0,
            )
            i += 1
            continue

        if "TÀI TRỢ CHUỖI CUNG ỨNG SCP" in line:
            add_paragraph_with_format(
                doc, "TÀI TRỢ CHUỖI CUNG ỨNG SCP", alignment="right", font_size=12, bold=True
            )
            i += 1
            continue

        if "Người đại diện pháp luật" in line and "Ký" not in line:
            add_paragraph_with_format(
                doc, "Người đại diện pháp luật", alignment="right", font_size=12, spacing_after=0
            )
            i += 1
            continue

        if "(Ký tên, đóng dấu)" in line:
            add_paragraph_with_format(
                doc,
                "(Ký tên, đóng dấu)",
                alignment="right",
                font_size=12,
                italic=True,
                spacing_after=48,
            )
            i += 1
            continue

        if "Lê Minh Đức" in line:
            add_paragraph_with_format(
                doc, "Lê Minh Đức", alignment="right", font_size=12, bold=True, spacing_after=0
            )
            i += 1
            continue

        if "Tổng giám đốc" in line and "Chức vụ" not in line:
            add_paragraph_with_format(doc, "Tổng giám đốc", alignment="right", font_size=12)
            i += 1
            continue

        # Note at bottom
        if line.startswith("*Lưu ý:"):
            add_paragraph_with_format(doc, "", alignment="left", spacing_after=12)
            clean_text = line.replace("*", "")
            add_paragraph_with_format(
                doc, clean_text, alignment="left", font_size=11, italic=True, spacing_after=0
            )
            i += 1
            continue

        # Regular paragraph with mixed formatting
        add_mixed_paragraph(doc, line, alignment="justify", base_size=12)
        i += 1

    # Save document
    doc.save(output_file)
    print(f"Created: {output_file}")


if __name__ == "__main__":
    convert_md_to_docx("don-to-cao-scp-tmart-hoan-chinh.md", "don-to-cao-scp-tmart-FINAL.docx")
