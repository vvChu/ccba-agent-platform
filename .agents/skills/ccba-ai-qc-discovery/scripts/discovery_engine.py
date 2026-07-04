"""
IDOP Discovery Engine — Phase 3 upgrade.

Khai phá cấu trúc hồ sơ thiết kế PDF sử dụng ccba-pdf-prep + AI Gateway.
Pipeline:
  1. PDFAnalyzer phan tich file -> bao cao (category, pages, oversized)
  2. Ti`m trang muc luc (index pages) bang text search
  3. Voi moi trang biet la drawing: TitleBlockDetector cat khung ten
  4. Gui anh khung ten qua AI Gateway (ocr-primary) de lay metadata JSON
  5. Xuat Project Backbone JSON

Usage:
    python discovery_engine.py --input path/to/drawings.pdf --output backbone.json
    python discovery_engine.py --input folder/ --output backbone.json --recursive
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ccba_ai import async_ai, parse_llm_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SheetEntry:
    """A single drawing sheet extracted from the PDF."""

    file: str  # Source PDF filename
    page_num: int  # 0-indexed page number
    sheet_no: str = ""  # e.g. "ACMV-M-201"
    title: str = ""  # Drawing title
    level: str = ""  # Building level / floor
    zone: str = ""  # Zone / block
    discipline: str = ""  # Arch / KC / ME / PCCC
    titleblock_path: str = ""  # Path to extracted title block image


@dataclass
class ProjectBackbone:
    """Top-level project document map."""

    project: str
    generated_at: str
    total_files: int
    total_sheets: int
    sheets: list[SheetEntry] = field(default_factory=list)
    index_pages: dict[str, list[int]] = field(default_factory=dict)  # file -> pages

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict (JSON-serializable)."""
        d = asdict(self)
        d["sheets"] = [asdict(s) for s in self.sheets]
        return d


# ---------------------------------------------------------------------------
# Discovery Engine
# ---------------------------------------------------------------------------


class IDOPDiscovery:
    """Khai pha cau truc ho so thiet ke PDF.

    Tim Index, trich xuat Metadata (SheetNo, Title, Level, Zone)
    su dung AI Gateway.

    Args:
        project_name: Ten du an (hien thi trong bao cao).
        output_dir: Thu muc luu anh khung ten (titleblock images).
        ai_model: Model AI cho OCR title blocks.
    """

    INDEX_KEYWORDS = (
        "DANH MUC BAN VE",
        "LIST OF DRAWINGS",
        "MUC LUC",
        "INDEX OF DRAWINGS",
        "DANH SACH BAN VE",
    )

    def __init__(
        self,
        project_name: str = "CCBA Project",
        output_dir: Path | None = None,
        ai_model: str = "gemini-3.1-pro-low",
    ) -> None:
        self.project_name = project_name
        self.output_dir = Path(output_dir) if output_dir else Path("discovery_output")
        self.ai_model = ai_model
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_file(self, pdf_path: Path) -> dict[str, Any]:
        """Run PDFAnalyzer on a single file and return the report dict."""
        from ccba_pdf_prep import PDFAnalyzer

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)
        return report.to_dict()

    def find_index_pages(self, pdf_path: Path, search_limit: int = 15) -> list[int]:
        """Find pages containing a drawing index table.

        Searches the first ``search_limit`` pages for Vietnamese/English
        keywords indicating an index page.

        Args:
            pdf_path: Path to the PDF file.
            search_limit: Max pages to scan.

        Returns:
            List of 0-indexed page numbers containing an index.
        """
        import fitz

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        index_pages: list[int] = []
        limit = min(len(doc), search_limit)

        for i in range(limit):
            text = doc[i].get_text().upper()
            # Normalize Vietnamese diacritics for robust matching
            text_normalized = _normalize_vn(text)
            if any(kw in text_normalized for kw in self.INDEX_KEYWORDS):
                index_pages.append(i)
                logger.info("Index page found at page %d in %s", i + 1, pdf_path.name)

        doc.close()
        return index_pages

    def extract_titleblocks(
        self,
        pdf_path: Path,
        page_range: range | None = None,
        dpi: int = 200,
    ) -> list[tuple[int, Path]]:
        """Extract title block images from drawing pages.

        Args:
            pdf_path: Path to the PDF file.
            page_range: Pages to process (default: all pages).
            dpi: Rendering DPI for extracted images.

        Returns:
            List of (page_num, titleblock_path) tuples.
        """
        import fitz

        from ccba_pdf_prep.vision import TitleBlockDetector

        doc = fitz.open(str(pdf_path))
        total = len(doc)
        doc.close()

        pages = list(page_range) if page_range else list(range(total))
        results: list[tuple[int, Path]] = []

        for page_num in pages:
            out = self.output_dir / f"{pdf_path.stem}_p{page_num + 1}_titleblock.png"
            extracted = TitleBlockDetector.extract(
                pdf_path=pdf_path,
                page_num=page_num,
                output_path=out,
                dpi=dpi,
                force=True,  # Always extract bottom-right corner for AI processing
            )
            if extracted:
                results.append((page_num, extracted))
            else:
                logger.debug("No title block on page %d of %s", page_num + 1, pdf_path.name)

        return results

    async def extract_metadata_from_titleblock(
        self,
        titleblock_path: Path,
        pdf_name: str,
        page_num: int,
    ) -> SheetEntry:
        """Send a title block image to AI Gateway for metadata extraction.

        Args:
            titleblock_path: Path to the cropped title block PNG.
            pdf_name: Source PDF filename (for reference).
            page_num: Page index (0-indexed).

        Returns:
            SheetEntry populated from AI response, with fallback empty fields.
        """
        import base64
        from io import BytesIO

        from PIL import Image

        # Resize image to max 1024x1024 if needed
        img = Image.open(titleblock_path)
        img = img.convert("RGB")
        max_dim = 1024
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        b64 = base64.b64encode(img_bytes).decode()

        prompt = (
            "You are reading a title block (khung ten) from a Vietnamese construction drawing.\n"
            "Extract the following fields from the image:\n"
            "- sheet_no: Drawing number/code (e.g. ACMV-M-201, A-001)\n"
            "- title: Drawing title in Vietnamese or English\n"
            "- level: Building floor/level (e.g. Tang 1, Floor 2, Mong)\n"
            "- zone: Zone or block (e.g. Khoi A, Block B). Leave empty if not found.\n"
            "- discipline: One of Arch / KC / ME / PCCC / EL / PL\n\n"
            "Respond ONLY with a JSON object, no markdown or explanation:\n"
            '{"sheet_no":"","title":"","level":"","zone":"","discipline":""}'
        )

        try:
            response = await async_ai.chat_multi(
                model=self.ai_model,
                max_tokens=2048,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            raw = response
            logger.info("Raw AI response: %s", raw)
            raw_data = parse_llm_json(raw) or {}
            data = {
                k: str(raw_data.get(k, "")) for k in ("sheet_no", "title", "level", "zone", "discipline")
            }
            logger.info(
                "AI extracted %s p%d: sheet_no=%s disc=%s",
                pdf_name,
                page_num + 1,
                data.get("sheet_no", "?"),
                data.get("discipline", "?"),
            )
            return SheetEntry(
                file=pdf_name,
                page_num=page_num,
                titleblock_path=str(titleblock_path),
                **data,
            )
        except Exception as e:
            logger.warning("AI extraction failed for %s p%d: %s", pdf_name, page_num + 1, e)
            return SheetEntry(
                file=pdf_name,
                page_num=page_num,
                titleblock_path=str(titleblock_path),
            )

    async def discover(
        self,
        pdf_paths: list[Path],
        extract_titleblocks: bool = True,
        run_ai: bool = True,
    ) -> ProjectBackbone:
        """Run full discovery pipeline on a list of PDF files.

        Args:
            pdf_paths: List of PDF files to analyze.
            extract_titleblocks: Whether to extract title block images.
            run_ai: Whether to call AI Gateway for metadata.

        Returns:
            ProjectBackbone with all discovered sheets.
        """
        from datetime import datetime

        from ccba_pdf_prep import PDFAnalyzer, PDFCategory

        analyzer = PDFAnalyzer()
        all_sheets: list[SheetEntry] = []
        all_index_pages: dict[str, list[int]] = {}

        for pdf_path in pdf_paths:
            logger.info("Discovering: %s", pdf_path.name)

            try:
                report = analyzer.analyze(pdf_path)
            except Exception as e:
                logger.error("Analysis failed for %s: %s", pdf_path.name, e)
                continue

            # Find index pages in text-heavy files
            if report.category in (PDFCategory.TEXT_RICH, PDFCategory.HYBRID):
                idx = self.find_index_pages(pdf_path)
                if idx:
                    all_index_pages[pdf_path.name] = idx

            # Extract title blocks from drawing pages
            if report.category in (PDFCategory.DRAWING, PDFCategory.HYBRID):
                pass  # drawing_pages not used yet

                if extract_titleblocks:
                    tb_results = self.extract_titleblocks(pdf_path, range(len(report.page_details)))
                else:
                    tb_results = []

                if run_ai and tb_results:
                    tasks = [
                        self.extract_metadata_from_titleblock(tb_path, pdf_path.name, pnum)
                        for pnum, tb_path in tb_results
                    ]
                    sheets = await asyncio.gather(*tasks)
                    all_sheets.extend(sheets)
                else:
                    # No AI — create stub entries
                    for pnum, tb_path in tb_results:
                        all_sheets.append(
                            SheetEntry(
                                file=pdf_path.name,
                                page_num=pnum,
                                titleblock_path=str(tb_path),
                            )
                        )

        return ProjectBackbone(
            project=self.project_name,
            generated_at=datetime.now().isoformat(),
            total_files=len(pdf_paths),
            total_sheets=len(all_sheets),
            sheets=all_sheets,
            index_pages=all_index_pages,
        )

    def export(self, backbone: ProjectBackbone, output_path: Path) -> Path:
        """Export ProjectBackbone to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(backbone.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("Backbone exported to %s (%d sheets)", output_path, backbone.total_sheets)
        return output_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_vn(text: str) -> str:
    """Strip common Vietnamese diacritics for keyword matching."""
    replacements = {
        "a\u0300": "a",
        "a\u0301": "a",
        "a\u0302": "a",
        "a\u0303": "a",
        "u\u0300": "u",
        "u\u0301": "u",
        "u\u01b0": "u",
        "d\u0111": "d",
        "\u0110": "D",
        "e\u0323": "e",
        "\u1ec7": "e",
        "\u1eb9": "e",
        "\u1ee5": "u",
    }
    result = text
    for src, tgt in replacements.items():
        result = result.replace(src, tgt)
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="IDOP Discovery Engine")
    parser.add_argument("--input", required=True, help="PDF file or folder")
    parser.add_argument("--output", default="backbone.json", help="Output JSON path")
    parser.add_argument("--project", default="CCBA Project", help="Project name")
    parser.add_argument("--recursive", action="store_true", help="Scan subfolders")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI metadata extraction")
    parser.add_argument("--ai-model", default="gemini-3.1-pro-low", help="AI model to use for extraction")
    parser.add_argument(
        "--titleblocks-dir",
        default="titleblocks",
        help="Directory for extracted title block images",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_file():
        pdfs = [input_path]
    else:
        pattern = "**/*.pdf" if args.recursive else "*.pdf"
        pdfs = sorted(input_path.glob(pattern))

    if not pdfs:
        print(f"No PDFs found in {input_path}")
        raise SystemExit(1)

    engine = IDOPDiscovery(
        project_name=args.project,
        output_dir=Path(args.titleblocks_dir),
        ai_model=args.ai_model,
    )

    backbone = asyncio.run(engine.discover(pdfs, run_ai=not args.no_ai))
    engine.export(backbone, Path(args.output))
    print(
        f"Done: {backbone.total_sheets} sheets from {backbone.total_files} files -> {args.output}"
    )
