"""
CCBA AI QC Batch Orchestrator
Platform SDK for generalized Multi-Level QC Audit via Coordination Matrix.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
from pathlib import Path

import fitz
import pandas as pd

from ccba_ai import QCAuditEngine, QCReporterEngine


# ---------------------------------------------------------------------------
# Cross-skill script loader (no sys.path pollution)
# Scripts within .agents/skills/ are standalone — not installable packages.
# We use importlib.util to load them explicitly from their __file__ paths,
# which is safer than mutating the global sys.path at module level.
# ---------------------------------------------------------------------------

_SKILLS_ROOT = Path(__file__).parent.parent.parent  # .agents/skills/


def _load_script_module(skill_name: str, script_name: str):
    """Load a sibling skill's script module without mutating sys.path."""
    script_path = _SKILLS_ROOT / skill_name / "scripts" / f"{script_name}.py"
    if not script_path.exists():
        raise ImportError(
            f"[Orchestrator] Script not found: {script_path}. "
            "Ensure you run this inside the CCBA Hub context."
        )
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _audit_mod = _load_script_module("ccba-ai-qc-integrated-audit", "legacy_quadview_engine")
    _reporter_mod = _load_script_module("ccba-ai-qc-reporter", "reporter_engine")
    IDOPAuditEngine = _audit_mod.IDOPAuditEngine
    IDOPReporter = _reporter_mod.IDOPReporter
except ImportError as _e:
    print(f"Warning: {_e}")
    IDOPAuditEngine = None  # type: ignore[assignment]
    IDOPReporter = None  # type: ignore[assignment]



class QCBatchOrchestrator:
    def __init__(self, project_dir: str | Path, matrix_csv: str | Path, out_dir: str | Path):
        self.project_dir = Path(project_dir)
        self.matrix_csv = Path(matrix_csv)
        self.out_dir = Path(out_dir)
        self.renders_dir = self.out_dir / "renders"
        self.renders_dir.mkdir(parents=True, exist_ok=True)

        self.blank_img = self.renders_dir / "blank.png"
        self._generate_blank_image()

        # Cache for pdf page searches
        self.pdf_cache: dict[Path, fitz.Document] = {}

    def _generate_blank_image(self):
        from PIL import Image

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
                print(f"Error opening {pdf_path}: {e}")
                return None
        return self.pdf_cache[pdf_path]

    def find_page_in_dir(self, directory: Path, sheet_code: str) -> tuple[Path, int]:
        """Scans all PDFs in a directory to find the page containing the exact sheet_code."""
        if not directory.exists() or not sheet_code or pd.isna(sheet_code):
            return Path(""), -1

        # Pick the first valid sheet code if multiple (e.g. A.B1.01 | A.BTD.01)
        target_code = str(sheet_code).split("|")[0].strip()

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

        from ccba_pdf_prep import render_page_to_image

        try:
            render_page_to_image(
                pdf_path=pdf_path,
                page_num=page_num,
                output_path=out_path,
                dpi=dpi,
            )
            return out_path
        except Exception as e:
            print(f"Error rendering {pdf_path} page {page_num}: {e}")
            return self.blank_img


    async def _prepare_level(
        self, engine: QCAuditEngine, row: dict, hstk_dir: Path
    ) -> tuple[str, list[Path]]:
        level = row.get("NormalizedLevel", "Unknown")
        print(f"\n[{level}] Gathering images...")
        images = []

        # Mapping rules based on standard CCBA folder structure
        disciplines = [
            ("Arch", hstk_dir / "Kien Truc", row.get("Arch_Sheet", "")),
            ("Struct", hstk_dir / "K Cau", row.get("Struct_Sheet", "")),
            ("MEP", hstk_dir / "M&E", row.get("MEP_Sheet", "")),
            ("PCCC", hstk_dir / "PCCC", row.get("PCCC_Sheet", "")),
        ]

        for disc_name, disc_dir, sheet_code in disciplines:
            # Fallbacks just in case the folder name varies
            if not disc_dir.exists():
                # naive search in project root if standard folder missing
                disc_dir = hstk_dir

            pdf_path, pnum = self.find_page_in_dir(disc_dir, sheet_code)
            out_img = self.renders_dir / f"{level}_{disc_name}.png"
            final_img = self.render_page(pdf_path, pnum, out_img)
            images.append(final_img)

        return level, images

    async def run_batch(self, ai_model: str = "gemini-3.1-pro-low"):
        print("=" * 60)
        print("CCBA QC BATCH ORCHESTRATOR")
        print("=" * 60)

        import pandas as pd

        if not self.matrix_csv.exists():
            print(f"Error: Matrix file not found: {self.matrix_csv}")
            return

        df = pd.read_csv(self.matrix_csv)
        
        if IDOPAuditEngine is None:
            raise ImportError("IDOPAuditEngine not loaded. Check skill scripts.")
            
        engine: QCAuditEngine = IDOPAuditEngine(output_dir=self.out_dir, ai_model=ai_model, tile_dpi=150)

        hstk_dir = self.project_dir / "HSTK BVTC"

        # Prepare all images (sync fallback inside async)
        level_images = {}
        for _, row in df.iterrows():
            level, images = await self._prepare_level(engine, row, hstk_dir)
            level_images[level] = images

        print("\nStarting CONCURRENT AI Audit via LiteLLM...")
        results = await engine.run_multi_level_audit(level_images)

        print(f"\nProcessed {len(results)} levels. Generating Combined Report...")
        
        if IDOPReporter is None:
            raise ImportError("IDOPReporter not loaded. Check skill scripts.")
            
        reporter: QCReporterEngine = IDOPReporter(
            project_name=self.project_dir.name, author="CCBA Batch Orchestrator"
        )
        report_path = self.out_dir / "BATCH_QC_Report_Auto.md"
        reporter.synthesize(backbone=None, audit_results=results, output_path=report_path)


        print(f"\nDone! Batch Report saved to: {report_path}")

        # Cleanup cache
        for doc in self.pdf_cache.values():
            doc.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Batch QC Audit")
    parser.add_argument("--project-dir", type=str, required=True, help="Path to project directory")
    parser.add_argument("--matrix", type=str, required=True, help="Path to Coordination Matrix CSV")
    parser.add_argument(
        "--out-dir", type=str, required=True, help="Output directory for reports and renders"
    )
    parser.add_argument("--model", type=str, default="gemini-3.1-pro-low", help="AI Model to use")
    args = parser.parse_args()

    orchestrator = QCBatchOrchestrator(args.project_dir, args.matrix, args.out_dir)
    asyncio.run(orchestrator.run_batch(args.model))
