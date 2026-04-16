"""
IDOP Audit Engine — Phase 3 upgrade.

Doi soat da bo mon su dung ky thuat Quad-View + AI Gateway.
Pipeline:
  1. Nhan vao 4 anh trang ban ve (Arch / KC / MEP / PCCC) cho cung mot tang
  2. Dung CompositeBuilder de ghep quad-view 2x2
  3. Gui anh composite len AI Gateway (model vision) de nhan dien xung dot
  4. Parse ket qua va tra ve clash report co cau truc

Usage:
    from audit_engine import IDOPAuditEngine
    engine = IDOPAuditEngine(output_dir=Path("audit_out"))
    result = asyncio.run(engine.run_audit(images, level_label="L1"))
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ClashItem:
    """A single detected clash / coordination issue."""

    severity: str = "medium"  # high / medium / low
    location: str = ""        # Description of location in the drawing
    disciplines: list[str] = field(default_factory=list)  # e.g. ["MEP", "KC"]
    description: str = ""
    recommendation: str = ""


@dataclass
class AuditResult:
    """Result of a single Quad-View audit pass."""

    level: str
    quad_view_path: str
    ai_model: str
    clashes: list[ClashItem] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""

    @property
    def clash_count(self) -> int:
        return len(self.clashes)

    @property
    def high_severity_count(self) -> int:
        return sum(1 for c in self.clashes if c.severity == "high")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["clash_count"] = self.clash_count
        d["high_severity_count"] = self.high_severity_count
        return d


# ---------------------------------------------------------------------------
# Audit Engine
# ---------------------------------------------------------------------------

DISCIPLINE_LABELS = {
    "arch": "Kien Truc (Arch)",
    "kc": "Ket Cau (KC)",
    "mep": "Co Dien Nuoc (MEP)",
    "pccc": "PCCC",
}

_AUDIT_PROMPT = """\
You are a senior BIM coordination engineer reviewing a 4-discipline quad-view drawing image.
The image shows 4 building sections for the same floor/level:
  Top-left: {d0}
  Top-right: {d1}
  Bottom-left: {d2}
  Bottom-right: {d3}

Identify ALL spatial clashes, coordination conflicts, and missing information.
For each issue found, output a JSON object with these fields:
  - severity: "high" | "medium" | "low"
  - location: where in the drawing (e.g. "North staircase, Column G3")
  - disciplines: list of disciplines involved (e.g. ["MEP", "KC"])
  - description: detailed description of the clash
  - recommendation: suggested resolution

Respond ONLY with a JSON object:
{{
  "summary": "brief overall assessment",
  "clashes": [ ... ]
}}
"""


class IDOPAuditEngine:
    """Doi soat da bo mon su dung ki thuat Quad-View.

    Args:
        output_dir: Thu muc luu anh composite va ket qua audit.
        ai_model: Model AI cho phan tich clash (can support vision).
        tile_dpi: DPI khi render anh trang cho composite.
        tile_size: Max size moi anh trong composite (px).
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        ai_model: str = "gemini-2.5-flash",
        tile_dpi: int = 150,
        tile_size: int = 1024,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path("audit_output")
        self.ai_model = ai_model
        self.tile_dpi = tile_dpi
        self.tile_size = tile_size
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_page_image(
        self,
        pdf_path: Path,
        page_num: int = 0,
        use_smart_tile: bool = True,
        min_ink_ratio: float = 0.01,
    ) -> Path:
        """Render a PDF page as a single image for composite assembly.

        For oversized drawings (A0/A1), uses the first content-bearing tile
        from tile_page_smart to avoid sending mostly-blank images.

        Args:
            pdf_path: Path to the PDF file.
            page_num: Page index (0-indexed).
            use_smart_tile: If True, use smart tiling for oversized pages.
            min_ink_ratio: Minimum ink ratio for smart tiling.

        Returns:
            Path to the rendered PNG image.
        """
        from ccba_pdf_prep import PDFAnalyzer, VisionOptimizer

        out_dir = self.output_dir / "renders"
        out_dir.mkdir(exist_ok=True)

        # Check if oversized
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)
        is_oversized = any(
            p.is_oversized for p in report.page_details if p.page_num == page_num
        )

        if is_oversized and use_smart_tile:
            kept, all_results = VisionOptimizer.tile_page_smart(
                pdf_path=pdf_path,
                page_num=page_num,
                output_dir=out_dir / "tiles",
                dpi=self.tile_dpi,
                tile_size_px=self.tile_size,
                min_ink_ratio=min_ink_ratio,
            )
            if kept:
                return kept[0]  # Use first content tile as representative

        # Standard single-image render
        import fitz

        doc = fitz.open(str(pdf_path))
        page = doc[page_num]
        matrix = fitz.Matrix(self.tile_dpi / 72, self.tile_dpi / 72)
        pix = page.get_pixmap(matrix=matrix)
        out_path = out_dir / f"{pdf_path.stem}_p{page_num+1}.png"
        pix.save(str(out_path))
        doc.close()
        return out_path

    def generate_quad_view(
        self,
        images: list[Path],
        level_label: str,
        labels: Optional[list[str]] = None,
        target_size: int = 2048,
    ) -> Path:
        """Ghep 4 anh ban ve thanh collage 2x2.

        Args:
            images: Exactly 4 image paths (one per discipline).
            level_label: Label for the output filename (e.g. "L1", "Tang3").
            labels: Optional 4 discipline labels for the composite.
            target_size: Edge length of the output composite in pixels.

        Returns:
            Path to the saved quad-view PNG.
        """
        from ccba_pdf_prep.composite import CompositeBuilder

        if len(images) < 4:
            raise ValueError(f"Need 4 images for quad-view, got {len(images)}")

        output_path = self.output_dir / f"{level_label}_QuadView.png"
        return CompositeBuilder.quad_view(
            images=images[:4],
            output_path=output_path,
            labels=labels,
            target_size=target_size,
        )

    async def run_audit(
        self,
        images: list[Path],
        level_label: str,
        discipline_order: list[str] | None = None,
        target_size: int = 2048,
    ) -> AuditResult:
        """Run a complete audit on 4 discipline drawings for one floor level.

        Args:
            images: 4 image paths ordered by discipline.
            level_label: Floor/level label for naming and reporting.
            discipline_order: Names of the 4 disciplines (default: Arch/KC/MEP/PCCC).
            target_size: Composite image size in pixels.

        Returns:
            AuditResult with clash list and summary.
        """
        if discipline_order is None:
            discipline_order = ["Arch", "KC", "MEP", "PCCC"]

        # 1. Generate quad view
        quad_path = self.generate_quad_view(
            images=images,
            level_label=level_label,
            labels=discipline_order,
            target_size=target_size,
        )
        logger.info("Quad-view generated: %s", quad_path)

        # 2. Prepare prompt
        d = (discipline_order + ["", "", "", ""])[:4]
        prompt = _AUDIT_PROMPT.format(d0=d[0], d1=d[1], d2=d[2], d3=d[3])

        # 3. Encode composite image
        img_bytes = quad_path.read_bytes()
        b64 = base64.b64encode(img_bytes).decode()

        # 4. Call AI Gateway (OpenAI multimodal format)
        try:
            client = _get_vision_client()
            raw_response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.ai_model,
                max_tokens=2048,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{b64}"
                        }},
                    ],
                }],
            )
            response = raw_response.choices[0].message.content or ""
            clashes, summary = _parse_audit_response(response)
            logger.info(
                "Audit %s: %d clashes detected (model=%s)",
                level_label, len(clashes), self.ai_model,
            )
        except Exception as e:
            logger.error("AI audit call failed: %s", e)
            response = ""
            clashes, summary = [], f"AI call failed: {e}"

        return AuditResult(
            level=level_label,
            quad_view_path=str(quad_path),
            ai_model=self.ai_model,
            clashes=clashes,
            summary=summary,
            raw_response=response,
        )

    async def run_multi_level_audit(
        self,
        level_images: dict[str, list[Path]],
        discipline_order: list[str] | None = None,
    ) -> list[AuditResult]:
        """Run audit for multiple floor levels concurrently.

        Args:
            level_images: Mapping of level_label -> list of 4 discipline images.
            discipline_order: Discipline names list.

        Returns:
            List of AuditResult, one per level.
        """
        tasks = [
            self.run_audit(imgs, level, discipline_order)
            for level, imgs in level_images.items()
        ]
        return list(await asyncio.gather(*tasks))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_vision_client():
    """Return an OpenAI-compatible client for the AI Gateway (vision capable)."""
    import os

    from openai import OpenAI

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    url = os.getenv("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1")
    key = os.getenv("AI_GATEWAY_KEY", "sk-spark-secure-key-2026")
    return OpenAI(base_url=url, api_key=key)


def _parse_audit_response(text: str) -> tuple[list[ClashItem], str]:
    """Parse AI response into structured ClashItem list."""
    import re

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse audit JSON response")
        return [], text[:200]

    summary = str(data.get("summary", ""))
    raw_clashes = data.get("clashes", [])
    clashes: list[ClashItem] = []

    for item in raw_clashes:
        clashes.append(ClashItem(
            severity=str(item.get("severity", "medium")).lower(),
            location=str(item.get("location", "")),
            disciplines=list(item.get("disciplines", [])),
            description=str(item.get("description", "")),
            recommendation=str(item.get("recommendation", "")),
        ))

    return clashes, summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="IDOP Audit Engine")
    parser.add_argument("--arch", required=True, help="Architecture drawing image")
    parser.add_argument("--kc", required=True, help="Structure drawing image")
    parser.add_argument("--mep", required=True, help="MEP drawing image")
    parser.add_argument("--pccc", required=True, help="Fire protection drawing image")
    parser.add_argument("--level", default="L1", help="Floor level label")
    parser.add_argument("--output-dir", default="audit_output", help="Output directory")
    parser.add_argument("--model", default="gemini-2.5-flash", help="AI Vision model")
    args = parser.parse_args()

    images = [Path(args.arch), Path(args.kc), Path(args.mep), Path(args.pccc)]
    disciplines = ["Arch", "KC", "MEP", "PCCC"]

    engine = IDOPAuditEngine(
        output_dir=Path(args.output_dir),
        ai_model=args.model,
    )
    result = asyncio.run(
        engine.run_audit(images, args.level, disciplines)
    )

    print(f"\nAudit: {result.level}")
    print(f"Clashes: {result.clash_count} ({result.high_severity_count} HIGH)")
    print(f"Summary: {result.summary}")
    print(f"Quad-view: {result.quad_view_path}")
