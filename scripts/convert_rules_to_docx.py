
import os
import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def convert_md_to_docx(md_path, docx_path):
    document = Document()
    
    # Set default font (optional, but good for "Standard" look)
    style = document.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_frontmatter = False
    
    for line in lines:
        line = line.strip()
        
        # Skip YAML Frontmatter
        if line == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        
        if not line:
            continue

        # Handle Headers
        if line.startswith('# '):
            p = document.add_heading(line[2:], level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.bold = True
            run.font.color.rgb = None # Default black
            continue
        
        if line.startswith('## '):
            p = document.add_heading(line[3:], level=2)
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.bold = True
            run.font.color.rgb = None
            continue
            
        if line.startswith('### '):
            p = document.add_heading(line[4:], level=3)
            run = p.runs[0]
            run.font.name = 'Times New Roman'
            run.font.bold = True
            run.font.color.rgb = None
            continue

        # Handle specific centered bold lines (Titles)
        # Assuming lines starting with ** and ending with ** are centered titles if they are uppercase
        if line.startswith('**') and line.endswith('**'):
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
        if line.startswith('- ') or line.startswith('* '):
            p = document.add_paragraph(line[2:], style='List Bullet')
            continue
            
        if re.match(r'^\d+\.', line):
            # Ordered list
            # Remove the number and dot
            content = re.sub(r'^\d+\.\s*', '', line)
            p = document.add_paragraph(content, style='List Number')
            continue

        # Normal Paragraph with basic inline bold parsing
        p = document.add_paragraph()
        parts = re.split(r'(\*\*.*?\*\*)', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)

    document.save(docx_path)
    print(f"Successfully created {docx_path}")

if __name__ == "__main__":
    md_file = "g:/My Drive/00 QC BIM/Ban QC IBST 2025/CCBA_2026_QuyChe_ToChuc_HoatDong.md"
    docx_file = "g:/My Drive/00 QC BIM/Ban QC IBST 2025/CCBA_2026_QuyChe_ToChuc_HoatDong.docx"
    
    try:
        convert_md_to_docx(md_file, docx_file)
    except Exception as e:
        print(f"Error: {e}")
