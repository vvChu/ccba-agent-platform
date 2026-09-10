"""Pipeline & Batch Orchestrator — End-to-end multi-discipline coordination matrix runner."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz
import pandas as pd  # type: ignore[import-untyped]
from PIL import Image

from ccba_ai import AuditReport
from ccba_pdf_prep import render_page_to_image
from ccba_qc_core.quadview import QuadViewAuditEngine
from ccba_qc_core.reporter import ReporterEngine

logger = logging.getLogger(__name__)


class QCBatchOrchestrator:
    """Batch Orchestrator điều phối thẩm tra toàn bộ ma trận phối hợp (Coordination Matrix)."""

    def __init__(self, project_dir: str | Path, matrix_csv: str | Path, out_dir: str | Path) -> None:
        self.project_dir = Path(project_dir)
        self.matrix_csv = Path(matrix_csv)
        self.out_dir = Path(out_dir)
        self.renders_dir = self.out_dir / "renders"
        self.renders_dir.mkdir(parents=True, exist_ok=True)

        self.blank_img = self.renders_dir / "blank.png"
        self._generate_blank_image()
        self.pdf_cache: dict[Path, fitz.Document] = {}

    def _generate_blank_image(self) -> None:
        if not self.blank_img.exists():
            img = Image.new("RGB", (1000, 1000), "white")
            img.save(str(self.blank_img))

    def _get_doc(self, pdf_path: Path) -> fitz.Document | None:
        if not pdf_path.exists():
            return None
        if pdf_path not in self.pdf_cache:
            try:
                self.pdf_cache[pdf_path] = fitz.open(str(pdf_path))
            except Exception as e:
                logger.error("Error opening %s: %s", pdf_path, e)
                return None
        return self.pdf_cache[pdf_path]

    def find_page_in_dir(self, directory: Path, sheet_code: str) -> tuple[Path, int]:
        """Scans all PDFs in a directory to find the page containing the exact sheet_code."""
        if not directory.exists() or not sheet_code or pd.isna(sheet_code):
            return Path(""), -1

        target_code = str(sheet_code).split("|")[0].strip().upper()

        for pdf_path in directory.rglob("*.pdf"):
            doc = self._get_doc(pdf_path)
            if not doc:
                continue
            for i, page in enumerate(doc):
                text = page.get_text().upper()
                if target_code in text:
                    return pdf_path, i
        return Path(""), -1

    def render_page(self, pdf_path: Path, page_num: int, out_path: Path, dpi: int = 150) -> Path:
        if not pdf_path.exists() or page_num < 0:
            return self.blank_img

        try:
            render_page_to_image(
                pdf_path=pdf_path,
                page_num=page_num,
                output_path=out_path,
                dpi=dpi,
            )
            return out_path
        except Exception as e:
            logger.error("Error rendering %s page %d: %s", pdf_path, page_num, e)
            return self.blank_img

    async def prepare_level(
        self, row: dict[str, Any], hstk_dir: Path
    ) -> tuple[str, list[Path]]:
        """Gather images for one level from standard discipline folders."""
        level = str(row.get("NormalizedLevel", "Unknown"))
        logger.info("[%s] Gathering discipline images...", level)
        images: list[Path] = []

        disciplines = [
            ("Arch", hstk_dir / "Kien Truc", row.get("Arch_Sheet", "")),
            ("Struct", hstk_dir / "K Cau", row.get("Struct_Sheet", "")),
            ("MEP", hstk_dir / "M&E", row.get("MEP_Sheet", "")),
            ("PCCC", hstk_dir / "PCCC", row.get("PCCC_Sheet", "")),
        ]

        for disc_name, disc_dir, sheet_code in disciplines:
            target_dir = disc_dir if disc_dir.exists() else hstk_dir
            pdf_path, pnum = self.find_page_in_dir(target_dir, str(sheet_code))
            out_img = self.renders_dir / f"{level}_{disc_name}.png"
            final_img = self.render_page(pdf_path, pnum, out_img)
            images.append(final_img)

        return level, images

    async def run_batch(
        self,
        ai_model: str = "gemini-3.7-flash-high",
    ) -> list[AuditReport]:
        """Execute full batch audit across all matrix levels."""
        if not self.matrix_csv.exists():
            raise FileNotFoundError(f"Matrix file not found: {self.matrix_csv}")

        df = pd.read_csv(self.matrix_csv)
        engine = QuadViewAuditEngine(output_dir=self.out_dir, ai_model=ai_model, tile_dpi=150)
        hstk_dir = self.project_dir / "HSTK BVTC"

        level_images: dict[str, list[Path]] = {}
        for _, row in df.iterrows():
            level, images = await self.prepare_level(row.to_dict(), hstk_dir)
            level_images[level] = images

        logger.info("Starting concurrent AI audit for %d levels...", len(level_images))
        results = await engine.run_multi_level_audit(level_images)

        reporter = ReporterEngine(
            project_name=self.project_dir.name, author="CCBA Batch Orchestrator"
        )
        report_path = self.out_dir / "BATCH_QC_Report_Auto.md"
        reporter.synthesize(backbone=None, audit_results=results, output_path=report_path)
        logger.info("Batch Report saved to: %s", report_path)

        for doc in self.pdf_cache.values():
            doc.close()
        self.pdf_cache.clear()

        return results
