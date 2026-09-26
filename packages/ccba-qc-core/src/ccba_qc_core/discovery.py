"""Discovery Engine — PDF structure extraction and Project Backbone compilation."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ccba_ai import async_ai, parse_llm_json
from ccba_pdf_prep import PDFAnalyzer, PDFCategory, TitleBlockDetector

logger = logging.getLogger(__name__)


@dataclass
class SheetEntry:
    """A single drawing sheet extracted from the PDF."""

    file: str
    page_num: int
    sheet_no: str = ""
    title: str = ""
    level: str = ""
    zone: str = ""
    discipline: str = ""
    titleblock_path: str = ""


@dataclass
class ProjectBackbone:
    """Top-level project document map."""

    project: str
    generated_at: str
    total_files: int
    total_sheets: int
    sheets: list[SheetEntry] = field(default_factory=list)
    index_pages: dict[str, list[int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict (JSON-serializable)."""
        d = asdict(self)
        d["sheets"] = [asdict(s) for s in self.sheets]
        return d


class DiscoveryEngine:
    """Khai pha cau truc ho so thiet ke PDF va trich xuat Metadata qua AI Gateway."""

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
        ai_model: str = "gemini-3.7-flash",
    ) -> None:
        self.project_name = project_name
        self.output_dir = Path(output_dir) if output_dir else Path("discovery_output")
        self.ai_model = ai_model
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_file(self, pdf_path: Path) -> dict[str, Any]:
        """Run PDFAnalyzer on a single file and return the report dict."""
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)
        return report.to_dict()

    def find_index_pages(self, pdf_path: Path, search_limit: int = 15) -> list[int]:
        """Find pages containing a drawing index table."""
        import fitz  # ccba:allow-raw-bypass (low-level drawing index text scan)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        index_pages: list[int] = []
        limit = min(len(doc), search_limit)

        for i in range(limit):
            text = doc[i].get_text().upper()
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
        """Extract title block images from drawing pages."""
        import fitz  # ccba:allow-raw-bypass (low-level page count inspection)

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
                force=True,
            )
            if extracted:
                results.append((page_num, extracted))

        return results

    async def extract_metadata_from_titleblock(
        self,
        titleblock_path: Path,
        pdf_name: str,
        page_num: int,
    ) -> SheetEntry:
        """Send a title block image to AI Gateway for metadata extraction."""
        import base64
        from io import BytesIO

        from PIL import Image

        img = Image.open(titleblock_path).convert("RGB")
        max_dim = 1024
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()

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
            raw_data = parse_llm_json(response) or {}
            data = {
                k: str(raw_data.get(k, ""))
                for k in ("sheet_no", "title", "level", "zone", "discipline")
            }
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
        """Run full discovery pipeline on a list of PDF files."""
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

            if report.category in (PDFCategory.TEXT_RICH, PDFCategory.HYBRID):
                idx = self.find_index_pages(pdf_path)
                if idx:
                    all_index_pages[pdf_path.name] = idx

            if report.category in (PDFCategory.DRAWING, PDFCategory.HYBRID):
                tb_results = (
                    self.extract_titleblocks(pdf_path, range(len(report.page_details)))
                    if extract_titleblocks
                    else []
                )

                if run_ai and tb_results:
                    tasks = [
                        self.extract_metadata_from_titleblock(tb_path, pdf_path.name, pnum)
                        for pnum, tb_path in tb_results
                    ]
                    sheets = await asyncio.gather(*tasks)
                    all_sheets.extend(sheets)
                else:
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


# Backward compatibility alias
IDOPDiscovery = DiscoveryEngine


def _normalize_vn(text: str) -> str:
    """Strip Vietnamese diacritics for robust keyword matching."""
    import unicodedata

    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")
