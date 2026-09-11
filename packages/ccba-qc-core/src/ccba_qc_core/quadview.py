"""QuadView Audit Engine — Multi-discipline quad-view collage rendering and vision clash analysis."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path

from ccba_ai import AuditFinding, AuditReport, async_ai, parse_llm_json
from ccba_pdf_prep import PDFAnalyzer, VisionOptimizer, render_page_to_image
from ccba_pdf_prep.composite import CompositeBuilder

logger = logging.getLogger(__name__)

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


class QuadViewAuditEngine:
    """Doi soat da bo mon su dung ky thuat Quad-View."""

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

    def render_page_image(
        self,
        pdf_path: Path,
        page_num: int = 0,
        use_smart_tile: bool = True,
        min_ink_ratio: float = 0.01,
    ) -> Path:
        """Render a PDF page as a single image for composite assembly."""
        out_dir = self.output_dir / "renders"
        out_dir.mkdir(exist_ok=True)

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)
        is_oversized = any(p.is_oversized for p in report.page_details if p.page_num == page_num)

        if is_oversized and use_smart_tile:
            kept, _ = VisionOptimizer.tile_page_smart(
                pdf_path=pdf_path,
                page_num=page_num,
                output_dir=out_dir / "tiles",
                dpi=self.tile_dpi,
                tile_size_px=self.tile_size,
                min_ink_ratio=min_ink_ratio,
            )
            if kept:
                return kept[0]

        out_path = out_dir / f"{pdf_path.stem}_p{page_num + 1}.png"
        render_page_to_image(
            pdf_path=pdf_path,
            page_num=page_num,
            output_path=out_path,
            dpi=self.tile_dpi,
        )
        return out_path

    def generate_quad_view(
        self,
        images: list[Path],
        level_label: str,
        labels: list[str] | None = None,
        target_size: int = 2048,
    ) -> Path:
        """Ghep 4 anh ban ve thanh collage 2x2."""
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
    ) -> AuditReport:
        """Run complete visual audit on 4 discipline drawings for one level."""
        if discipline_order is None:
            discipline_order = ["Arch", "KC", "MEP", "PCCC"]

        quad_path = self.generate_quad_view(
            images=images,
            level_label=level_label,
            labels=discipline_order,
            target_size=target_size,
        )

        d = (discipline_order + ["", "", "", ""])[:4]
        prompt = _AUDIT_PROMPT.format(d0=d[0], d1=d[1], d2=d[2], d3=d[3])
        prompt += f"\n\n[Cache Buster: {time.time()}]"

        b64 = base64.b64encode(quad_path.read_bytes()).decode()

        try:
            response = await async_ai.chat_multi(
                model=self.ai_model,
                max_tokens=32768,
                temperature=0.2,
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
            findings, summary = _parse_audit_response(response)
        except Exception as e:
            logger.error("AI audit call failed: %s", e)
            response = ""
            findings, summary = [], f"AI call failed: {e}"

        return AuditReport(
            level=level_label,
            quad_view_path=str(quad_path),
            ai_model=self.ai_model,
            findings=findings,
            summary=summary,
            raw_response=response,
        )

    async def run_multi_level_audit(
        self,
        level_images: dict[str, list[Path]],
        discipline_order: list[str] | None = None,
    ) -> list[AuditReport]:
        """Run audit for multiple floor levels concurrently."""
        tasks = [
            self.run_audit(imgs, level, discipline_order) for level, imgs in level_images.items()
        ]
        return list(await asyncio.gather(*tasks))


# Backward compatibility alias
IDOPAuditEngine = QuadViewAuditEngine


def _parse_audit_response(text: str) -> tuple[list[AuditFinding], str]:
    """Parse AI response into structured AuditFinding list."""
    data = parse_llm_json(text) or {}
    if not data:
        logger.warning("Could not parse audit JSON response")
        return [], text[:200]

    summary = str(data.get("summary", ""))
    raw_clashes = data.get("clashes", [])
    findings: list[AuditFinding] = []

    for item in raw_clashes:
        findings.append(
            AuditFinding(
                severity=str(item.get("severity", "medium")).lower(),
                location=str(item.get("location", "")),
                disciplines=list(item.get("disciplines", [])),
                description=str(item.get("description", "")),
                recommendation=str(item.get("recommendation", "")),
                source="quadview_engine",
            )
        )

    return findings, summary
