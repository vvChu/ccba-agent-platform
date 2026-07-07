#!/usr/bin/env python3
"""export_paper_to_docx.py - Exposes utility to compile academic Markdown into standard docx.

Standard formats:
- 1-inch margins on all sides.
- Times New Roman, 12pt default font.
- Double-spaced (2.0) text with 0.5-inch paragraph indentation.
- Centered bold Title Page generated from YAML Frontmatter metadata.
"""

import sys
import re
import os
import argparse
from pathlib import Path

# Try importing docx and yaml, fail gracefully with instructions if missing
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Error: 'python-docx' library is missing. Install it using 'pip install python-docx'.")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: 'pyyaml' library is missing. Install it using 'pip install pyyaml'.")
    sys.exit(1)


def parse_inline_styles(paragraph, text: str):
    """Parse basic bold (**bold**) and italic (*italic* or _italic_) patterns in text."""
    # Pattern to tokenize bold, italic and normal text
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*|_.*?_)", text)
    
    for token in tokens:
        if not token:
            continue
            
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif (token.startswith("*") and token.endswith("*")) or (token.startswith("_") and token.endswith("_")):
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        else:
            paragraph.add_run(token)


def convert_md_to_docx(md_path: Path, docx_path: Path) -> None:
    document = Document()

    # 1. Set Margins to Standard 1-inch (72pt)
    for section in document.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # 2. Configure Default Font & Normal Style (Times New Roman, 12pt, Double-spaced)
    normal_style = document.styles["Normal"]
    font = normal_style.font
    font.name = "Times New Roman"
    font.size = Pt(12)
    
    # Read Markdown file
    content = md_path.read_text(encoding="utf-8")
    
    # Parse YAML Frontmatter
    frontmatter = {}
    md_body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                md_body = parts[2]
            except Exception as e:
                print(f"Warning: Failed to parse YAML frontmatter: {e}")
                
    # 3. Create Academic Title Page if metadata exists
    if frontmatter:
        title = frontmatter.get("title", "Research Paper Title")
        authors = frontmatter.get("authors", [])
        
        # Spacer before Title
        p_space = document.add_paragraph()
        p_space.paragraph_format.space_before = Pt(72)
        
        # Title: 16pt, Bold, Centered
        p_title = document.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_title = p_title.add_run(title)
        run_title.font.name = "Times New Roman"
        run_title.font.size = Pt(16)
        run_title.bold = True
        p_title.paragraph_format.space_after = Pt(24)
        
        # Authors
        for author in authors:
            name = author.get("name", "Author Name")
            affiliation = author.get("affiliation", "")
            email = author.get("email", "")
            is_corresponding = author.get("corresponding", False)
            
            p_author = document.add_paragraph()
            p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_name = p_author.add_run(name)
            run_name.font.name = "Times New Roman"
            run_name.font.size = Pt(12)
            run_name.bold = True
            
            if affiliation:
                p_aff = document.add_paragraph()
                p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_aff = p_aff.add_run(affiliation)
                run_aff.font.name = "Times New Roman"
                run_aff.font.size = Pt(10)
                run_aff.italic = True
                
            if email:
                p_email = document.add_paragraph()
                p_email.alignment = WD_ALIGN_PARAGRAPH.CENTER
                corr_label = " (Corresponding Author)" if is_corresponding else ""
                run_email = p_email.add_run(f"Email: {email}{corr_label}")
                run_email.font.name = "Times New Roman"
                run_email.font.size = Pt(10)
                
            # Paragraph space after each author block
            p_author.paragraph_format.space_after = Pt(12)
            
        # Add Page Break after Title Page
        document.add_page_break()

    # 4. Parse Markdown Body line by line
    in_code_block = False
    code_lines = []
    
    # Strip carriage returns and split into lines
    lines = md_body.replace("\r\n", "\n").split("\n")
    
    for line in lines:
        trimmed = line.strip()
        
        # Code block tracking (Mermaid or other source code)
        if trimmed.startswith("```"):
            if in_code_block:
                # Ending code block
                in_code_block = False
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)
                
                # Render code placeholder style (indented, grey background simulation or border)
                code_text = "\n".join(code_lines)
                if "graph " in code_text or "sequenceDiagram" in code_text:
                    p.add_run("[Sơ đồ hệ sinh thái Mermaid - Thêm ảnh xuất tương ứng tại đây]\n").italic = True
                run_code = p.add_run(code_text)
                run_code.font.name = "Courier New"
                run_code.font.size = Pt(9.5)
                
                code_lines = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_lines.append(line)
            continue

        if not trimmed:
            continue

        # Headings
        if trimmed.startswith("# "):
            p = document.add_heading(trimmed[2:], level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = None  # Use default text color
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            continue

        if trimmed.startswith("## "):
            p = document.add_heading(trimmed[3:], level=2)
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = None
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            continue

        if trimmed.startswith("### "):
            p = document.add_heading(trimmed[4:], level=3)
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = None
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            continue

        # Lists (Bulleted or Numbered)
        if trimmed.startswith("- ") or trimmed.startswith("* "):
            p = document.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.space_after = Pt(6)
            parse_inline_styles(p, trimmed[2:])
            continue

        if re.match(r"^\d+\.", trimmed):
            content_list = re.sub(r"^\d+\.\s*", "", trimmed)
            p = document.add_paragraph(style="List Number")
            p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.space_after = Pt(6)
            parse_inline_styles(p, content_list)
            continue

        # Normal Academic Paragraphs (Times New Roman, 12pt, Double-spaced, 0.5-inch indentation)
        p = document.add_paragraph()
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.first_line_indent = Inches(0.5)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Parse inline styling and populate paragraph
        parse_inline_styles(p, trimmed)

    # Save to file
    document.save(docx_path)
    print(f"Successfully generated academic DOCX paper at: {docx_path.absolute()}")


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Convert academic Markdown draft to standard double-spaced DOCX.")
    parser.add_argument("input_path", type=Path, help="Path to the input Markdown draft file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save the output Word file. Defaults to replacing extension with .docx",
    )

    args = parser.parse_args()
    input_path: Path = args.input_path

    if not input_path.exists() or not input_path.is_file():
        print(f"Error: Input draft file '{input_path}' does not exist.")
        sys.exit(1)

    output_path: Path = args.output if args.output else input_path.with_suffix(".docx")

    try:
        convert_md_to_docx(input_path, output_path)
    except Exception as e:
        print(f"Error converting document: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
