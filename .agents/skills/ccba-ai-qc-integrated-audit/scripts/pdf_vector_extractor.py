from pathlib import Path
from typing import Any

import fitz


class PDFVectorExtractor:
    """
    Extrator for Semantic Auditing.
    Extracts text blocks, notes, and tables from engineering PDFs.
    """

    def __init__(self, dpi: int = 150):
        self.dpi = dpi

    def extract_data(self, pdf_path: Path | str) -> dict[str, Any]:
        """
        Extract semantic data from a PDF document.
        Returns a dictionary containing extracted text blocks grouped by page.
        """
        doc = fitz.open(str(pdf_path))
        data = {
            "filename": Path(pdf_path).name,
            "page_count": len(doc),
            "pages": []
        }

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text blocks
            # block format: (x0, y0, x1, y1, "lines in block", block_no, block_type)
            text_blocks = page.get_text("blocks")

            # Filter and clean blocks
            cleaned_blocks = []
            for b in text_blocks:
                text = b[4].strip()
                if text and b[6] == 0:  # b[6] == 0 means text block (1 is image)
                    cleaned_blocks.append({
                        "bbox": [round(c, 2) for c in b[:4]],
                        "text": text
                    })

            page_data = {
                "page_num": page_num,
                "text_blocks": cleaned_blocks
            }
            data["pages"].append(page_data)

        doc.close()
        return data

    def extract_to_markdown(self, pdf_path: Path | str) -> str:
        """
        Extract data and format it into a clean Markdown string for LLM consumption.
        """
        data = self.extract_data(pdf_path)
        md_lines = []
        md_lines.append(f"# Dữ liệu bóc tách: {data['filename']}")
        md_lines.append(f"Số trang: {data['page_count']}\n")

        for page in data["pages"]:
            md_lines.append(f"## Trang {page['page_num']}")
            # Sort blocks top-to-bottom, left-to-right
            blocks = page["text_blocks"]
            blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

            for b in blocks:
                md_lines.append(f"- {b['text'].replace(chr(10), ' ')}")
            md_lines.append("\n")

        return "\n".join(md_lines)
