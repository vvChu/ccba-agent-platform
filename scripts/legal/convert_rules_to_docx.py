import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


def convert_md_to_docx(md_path: str | Path, docx_path: str | Path) -> None:
    document = Document()

    # Set default font (optional, but good for "Standard" look)
    style = document.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(12)

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_frontmatter = False

    for line in lines:
        line = line.strip()

        # Skip YAML Frontmatter
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue

        if not line:
            continue

        # Handle Headers
        if line.startswith("# "):
            p = document.add_heading(line[2:], level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.bold = True
            run.font.color.rgb = None  # Default black
            continue

        if line.startswith("## "):
            p = document.add_heading(line[3:], level=2)
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.bold = True
            run.font.color.rgb = None
            continue

        if line.startswith("### "):
            p = document.add_heading(line[4:], level=3)
            run = p.runs[0]
            run.font.name = "Times New Roman"
            run.font.bold = True
            run.font.color.rgb = None
            continue

        # Handle specific centered bold lines (Titles)
        # Assuming lines starting with ** and ending with ** are centered titles if they are uppercase
        if line.startswith("**") and line.endswith("**"):
            content = line[2:-2]
            # Check if it looks like a title (Uppercased or special specific lines)
            if content.isupper() or "Độc lập - Tự do" in content:
                p = document.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(content)
                run.bold = True
                continue
            # Else treat as normal bold paragraph or list item?
            # If it's just a bold line, let's treat it as a paragraph with bold text.

        # Handle Lists
        if line.startswith("- ") or line.startswith("* "):
            p = document.add_paragraph(line[2:], style="List Bullet")
            continue

        if re.match(r"^\d+\.", line):
            # Ordered list
            # Remove the number and dot
            content = re.sub(r"^\d+\.\s*", "", line)
            p = document.add_paragraph(content, style="List Number")
            continue

        # Normal Paragraph with basic inline bold parsing
        p = document.add_paragraph()
        parts = re.split(r"(\*\*.*?\*\*)", line)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)

    document.save(docx_path)
    print(f"Successfully created {docx_path}")


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Convert Markdown to Docx with standard styling.")
    parser.add_argument("input_path", type=Path, help="Path to the input Markdown file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path to output Docx file. Defines from input by default.",
    )

    args = parser.parse_args()
    input_path: Path = args.input_path

    if not input_path.exists() or not input_path.is_file():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    output_path: Path = args.output if args.output else input_path.with_suffix(".docx")

    try:
        convert_md_to_docx(input_path, output_path)
    except Exception as e:
        print(f"Error converting document: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
