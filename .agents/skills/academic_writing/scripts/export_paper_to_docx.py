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
import urllib.request
import base64

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

try:
    from lxml import etree
except ImportError:
    etree = None


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


def get_mathml_for_formula(latex_str: str) -> str:
    """Hardcoded MathML for the specific mathematical equations in this paper."""
    # Formula 1: P_{cp} = \sum_{i=1}^{n} (C_i) \times (1 + \mu)
    if "P_{cp}" in latex_str or "P_{cp}" in latex_str:
        return (
            '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
            '<msub><mi>P</mi><mrow><mi>c</mi><mi>p</mi></mrow></msub>'
            '<mo>=</mo>'
            '<munderover><mo>&#x2211;</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover>'
            '<mo>(</mo><msub><mi>C</mi><mi>i</mi></msub><mo>)</mo>'
            '<mo>&#xD7;</mo>'
            '<mo>(</mo><mn>1</mn><mo>+</mo><mi>&#x3BC;</mi><mo>)</mo>'
            '</math>'
        )
    # Formula 2: P_{vb} = C_{base} + \alpha \times \Delta V
    if "P_{vb}" in latex_str or "P_{vb}" in latex_str:
        return (
            '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
            '<msub><mi>P</mi><mrow><mi>v</mi><mi>b</mi></mrow></msub>'
            '<mo>=</mo>'
            '<msub><mi>C</mi><mrow><mi>b</mi><mi>a</mi><mi>s</mi><mi>e</mi></mrow></msub>'
            '<mo>+</mo>'
            '<mi>&#x3B1;</mi>'
            '<mo>&#xD7;</mo>'
            '<mi>&#x394;</mi>'
            '<mi>V</mi>'
            '</math>'
        )
    return None


def get_mathml_for_inline(formula: str) -> str:
    """Get MathML for inline math formulas used in the paper."""
    f = formula.replace(" ", "")
    if f in ("P_{vb}", "P__{vb}", "P_{vb}"):
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><msub><mi>P</mi><mrow><mi>v</mi><mi>b</mi></mrow></msub></math>'
    if f in ("P_{cp}", "P__{cp}", "P_{cp}"):
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><msub><mi>P</mi><mrow><mi>c</mi><mi>p</mi></mrow></msub></math>'
    if f == "C_{base}":
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><msub><mi>C</mi><mrow><mi>b</mi><mi>a</mi><mi>s</mi><mi>e</mi></mrow></msub></math>'
    if f in ("\\DeltaV", "\\Delta"):
        # Match \Delta V or \Delta
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>&#x394;</mi><mi>V</mi></math>'
    if f == "\\alpha":
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>&#x3B1;</mi></math>'
    if f == "0<\\alpha<1":
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mn>0</mn><mo>&lt;</mo><mi>&#x3B1;</mi><mo>&lt;</mo><mn>1</mn></math>'
    if f == "\\mu":
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>&#x3BC;</mi></math>'
    if f in ("C_i", "C_{i}"):
        return '<math xmlns="http://www.w3.org/1998/Math/MathML"><msub><mi>C</mi><mi>i</mi></msub></math>'
    return None


def clean_latex_symbols(formula: str) -> str:
    """Clean up inline LaTeX syntax for fallback text rendering."""
    s = formula
    s = s.replace(r"\Delta", "Δ")
    s = s.replace(r"\alpha", "α")
    s = s.replace(r"\mu", "μ")
    s = s.replace(r"\times", "×")
    s = s.replace(r"_", "")
    s = s.replace(r"{", "")
    s = s.replace(r"}", "")
    return s


def parse_academic_text(paragraph, text: str):
    """Parse paragraph text supporting both inline math ($...$) and markdown styles."""
    tokens = re.split(r"(\$.*?\$)", text)
    
    for token in tokens:
        if not token:
            continue
            
        if token.startswith("$") and token.endswith("$") and len(token) > 2:
            formula = token[1:-1].strip()
            mathml = get_mathml_for_inline(formula)
            if mathml and etree is not None:
                success = add_math_equation(paragraph, mathml)
                if not success:
                    run = paragraph.add_run(clean_latex_symbols(formula))
                    run.font.name = "Times New Roman"
                    run.italic = True
            else:
                run = paragraph.add_run(clean_latex_symbols(formula))
                run.font.name = "Times New Roman"
                run.italic = True
        else:
            parse_inline_styles(paragraph, token)


def add_math_equation(paragraph, mathml_str: str) -> bool:
    """Transform MathML to OMML using Word's stylesheet and append to paragraph."""
    if etree is None:
        return False
        
    xslt_paths = [
        r'C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL',
        r'C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL'
    ]
    
    xslt_path = None
    for p in xslt_paths:
        if os.path.exists(p):
            xslt_path = p
            break
            
    if not xslt_path:
        return False
        
    try:
        xslt = etree.parse(xslt_path)
        transform = etree.XSLT(xslt)
        tree = etree.fromstring(mathml_str)
        omml = transform(tree)
        paragraph._element.append(omml.getroot())
        return True
    except Exception as e:
        print(f"Warning: OMML conversion failed: {e}")
        return False


def download_mermaid_image(code_text: str, output_path: Path) -> bool:
    """Download rendered Mermaid image from mermaid.ink."""
    try:
        graph_bytes = code_text.encode("utf-8")
        base64_bytes = base64.urlsafe_b64encode(graph_bytes)
        base64_string = base64_bytes.decode("ascii")
        
        url = f"https://mermaid.ink/img/{base64_string}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            output_path.write_bytes(response.read())
        return True
    except Exception as e:
        print(f"Warning: Failed to download Mermaid image: {e}")
        return False


def parse_and_add_table(document, table_lines):
    """Parse Markdown table lines and add a styled Word table with explicit column widths."""
    parsed_rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        # Skip separator rows like |:---|:---|
        if cells and all(re.match(r"^:?-+:?$", cell) for cell in cells):
            continue
        parsed_rows.append(cells)
        
    if not parsed_rows:
        return
        
    num_cols = max(len(row) for row in parsed_rows)
    for row in parsed_rows:
        while len(row) < num_cols:
            row.append("")
            
    table = document.add_table(rows=len(parsed_rows), cols=num_cols)
    table.style = 'Table Grid'
    
    # Standard column widths matching printable area (6.5 inches)
    # Tiêu chí: 1.5", Tư vấn truyền thống: 2.5", Tư vấn giá trị: 2.5"
    col_widths = [Inches(1.5), Inches(2.5), Inches(2.5)]
    
    for r_idx, row in enumerate(parsed_rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            
            # Apply column widths
            if c_idx < len(col_widths):
                cell.width = col_widths[c_idx]
                
            cell.text = ""  # Clear default text
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.space_before = Pt(4)
            
            # Parse inline formatting supporting inline math in table cell
            parse_academic_text(p, val)
            
            # Reset font formatting for cell runs
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(10)
                if r_idx == 0:
                    run.bold = True


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
    table_lines = []
    
    # Strip carriage returns and split into lines
    lines = md_body.replace("\r\n", "\n").split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()
        
        # Code block tracking (Mermaid or other source code)
        if in_code_block:
            if trimmed.startswith("```"):
                in_code_block = False
                p = document.add_paragraph()
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(12)
                
                code_text = "\n".join(code_lines)
                if "graph " in code_text or "sequenceDiagram" in code_text:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                    # Output scratch image path
                    img_path = Path("d:/GitHubProjects/ccba-agent-platform/.md/scratch/mermaid_flowchart.png")
                    img_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Try downloading chart image
                    if download_mermaid_image(code_text, img_path):
                        p.add_run().add_picture(str(img_path), width=Inches(6.0))
                        
                        # Add Fig Caption
                        p_cap = document.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        run_cap = p_cap.add_run("Hình 1: Sơ đồ luồng ra quyết định chống phản xạ giảm giá trong đấu thầu")
                        run_cap.font.name = "Times New Roman"
                        run_cap.font.size = Pt(10)
                        run_cap.italic = True
                        p_cap.paragraph_format.space_after = Pt(12)
                    else:
                        run_label = p.add_run("[Sơ đồ Mermaid - Xem mã nguồn bên dưới]\n")
                        run_label.font.name = "Times New Roman"
                        run_label.font.size = Pt(11)
                        run_label.italic = True
                        
                        run_code = p.add_run(code_text)
                        run_code.font.name = "Courier New"
                        run_code.font.size = Pt(9.5)
                else:
                    run_code = p.add_run(code_text)
                    run_code.font.name = "Courier New"
                    run_code.font.size = Pt(9.5)
                
                code_lines = []
            else:
                code_lines.append(line)
            i += 1
            continue
            
        if trimmed.startswith("```"):
            in_code_block = True
            i += 1
            continue
            
        # Table tracking
        if trimmed.startswith("|"):
            table_lines.append(trimmed)
            i += 1
            continue
        elif table_lines:
            parse_and_add_table(document, table_lines)
            table_lines = []
            # Do not increment i, let current line be parsed below
            
        if not trimmed:
            i += 1
            continue

        # Mathematical Formula block equations ($$...$$)
        if trimmed.startswith("$$") and trimmed.endswith("$$"):
            formula_text = trimmed[2:-2].strip()
            mathml = get_mathml_for_formula(formula_text)
            
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(12)
            
            if mathml and add_math_equation(p, mathml):
                # Rendered successfully via OMML
                pass
            else:
                # Fallback to plain text if Office XSLT is not found or fails
                run = p.add_run(formula_text)
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
                run.italic = True
            i += 1
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
            i += 1
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
            i += 1
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
            i += 1
            continue

        # Lists (Bulleted or Numbered)
        if trimmed.startswith("- ") or trimmed.startswith("* "):
            p = document.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.space_after = Pt(6)
            parse_academic_text(p, trimmed[2:])
            i += 1
            continue

        if re.match(r"^\d+\.", trimmed):
            content_list = re.sub(r"^\d+\.\s*", "", trimmed)
            p = document.add_paragraph(style="List Number")
            p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.space_after = Pt(6)
            parse_academic_text(p, content_list)
            i += 1
            continue

        # Normal Academic Paragraphs (Times New Roman, 12pt, Double-spaced, 0.5-inch indentation)
        p = document.add_paragraph()
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.first_line_indent = Inches(0.5)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Parse inline styling and populate paragraph
        parse_academic_text(p, trimmed)
        i += 1

    # Handline remaining table at the end of file
    if table_lines:
        parse_and_add_table(document, table_lines)

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
