"""
IDOP Reporter Engine — Phase 3 upgrade.

Tong hop du lieu tu Discovery va Audit tao bao cao ky thuat Markdown.
Pipeline:
  1. Nhan ProjectBackbone (tu discovery) + list[AuditResult] (tu audit)
  2. Tao bang Ma tran Phoi hop (Coordination Matrix)
  3. Tao bang Xung dot theo Tang va Bo mon
  4. Xuat file Markdown chinh quy + JSON summary

Usage:
    from reporter_engine import IDOPReporter
    reporter = IDOPReporter(project_name="BV Nguyen Tri Phuong")
    reporter.synthesize(backbone, audit_results, output_path=Path("report.md"))
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IDOPReporter:
    """Tong hop du lieu va xuat bao cao ky thuat.

    Args:
        project_name: Ten du an.
        author: Nguoi lap bao cao.
        company: Ten don vi.
    """

    def __init__(
        self,
        project_name: str,
        author: str = "CCBA Platform",
        company: str = "CCBA Engineering",
    ) -> None:
        self.project_name = project_name
        self.author = author
        self.company = company

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        backbone: Any | None = None,
        audit_results: list[Any] | None = None,
        output_path: Path = Path("report.md"),
    ) -> Path:
        """Tao bao cao Markdown tong hop.

        Args:
            backbone: ProjectBackbone tu IDOPDiscovery.discover()
            audit_results: List AuditResult tu IDOPAuditEngine.run_audit()
            output_path: Duong dan file bao cao dau ra.

        Returns:
            Path to the written Markdown file.
        """
        audit_results = audit_results or []
        sections: list[str] = []

        sections.append(self._render_header())

        if backbone is not None:
            sections.append(self._render_backbone_summary(backbone))
            sections.append(self._render_coordination_matrix(backbone))

        if audit_results:
            sections.append(self._render_audit_overview(audit_results))
            sections.append(self._render_clash_details(audit_results))
            sections.append(self._render_risk_heatmap(audit_results))

        sections.append(self._render_footer())

        report = "\n\n".join(sections)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s", output_path)

        # Also export JSON summary
        json_path = output_path.with_suffix(".json")
        self._export_json_summary(backbone, audit_results, json_path)

        return output_path

    def synthesize_report(
        self,
        matrix_data: Any = None,
        audit_results: Any = None,
        output_path: str = "report.md",
    ) -> str:
        """Legacy API for backward compatibility with original skeleton."""
        result = self.synthesize(
            backbone=matrix_data,
            audit_results=audit_results or [],
            output_path=Path(output_path),
        )
        return str(result)

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def _render_header(self) -> str:
        date_str = datetime.now().strftime("%d/%m/%Y")
        return (
            f"# BAO CAO RA SOAT DUONG GANG KY THUAT\n"
            f"## Du an: {self.project_name}\n\n"
            f"| Thong tin | Noi dung |\n"
            f"|---|---|\n"
            f"| **Don vi** | {self.company} |\n"
            f"| **Nguoi lap** | {self.author} |\n"
            f"| **Ngay bao cao** | {date_str} |\n"
            f"| **Cong cu** | CCBA AI Platform v2 |\n"
        )

    def _render_backbone_summary(self, backbone: Any) -> str:
        bd = backbone.to_dict() if hasattr(backbone, "to_dict") else backbone
        total_files = bd.get("total_files", "N/A")
        total_sheets = bd.get("total_sheets", "N/A")
        sheets = bd.get("sheets", [])

        # Count by discipline
        disc_counts: dict[str, int] = {}
        for s in sheets:
            disc = s.get("discipline", "Unknown") or "Unknown"
            disc_counts[disc] = disc_counts.get(disc, 0) + 1

        lines = [
            "## 1. Tom Tat Ho So",
            "",
            f"| Chi so | Gia tri |",
            f"|---|---|",
            f"| Tong so file PDF | {total_files} |",
            f"| Tong so trang ban ve | {total_sheets} |",
        ]

        if bd.get("index_pages"):
            n_idx = sum(len(v) for v in bd["index_pages"].values())
            lines.append(f"| Trang muc luc phat hien | {n_idx} |")

        lines += ["", "**Phan bo theo Bo mon:**", ""]
        lines += [f"| Bo mon | So ban ve |", "|---|---|"]
        for disc, count in sorted(disc_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {disc} | {count} |")

        return "\n".join(lines)

    def _render_coordination_matrix(self, backbone: Any) -> str:
        bd = backbone.to_dict() if hasattr(backbone, "to_dict") else backbone
        sheets = bd.get("sheets", [])

        # Build level x discipline matrix
        matrix: dict[str, dict[str, int]] = {}
        disciplines: set[str] = set()

        for s in sheets:
            level = s.get("level", "Unknown") or "Unknown"
            disc = s.get("discipline", "Unknown") or "Unknown"
            disciplines.add(disc)
            if level not in matrix:
                matrix[level] = {}
            matrix[level][disc] = matrix[level].get(disc, 0) + 1

        if not matrix:
            return "## 2. Ma Tran Phoi Hop\n\n_Chua co du lieu_"

        disc_list = sorted(disciplines)
        header = "| Tang/Zone | " + " | ".join(disc_list) + " | Tong |"
        separator = "|---|" + "---|" * (len(disc_list) + 1)

        lines = ["## 2. Ma Tran Phoi Hop", "", header, separator]
        for level in sorted(matrix.keys()):
            row_data = matrix[level]
            total = sum(row_data.values())
            cells = [str(row_data.get(d, 0)) for d in disc_list]
            lines.append(f"| {level} | " + " | ".join(cells) + f" | {total} |")

        return "\n".join(lines)

    def _render_audit_overview(self, audit_results: list[Any]) -> str:
        total = len(audit_results)
        total_clashes = sum(
            r.clash_count if hasattr(r, "clash_count") else len(r.get("clashes", []))
            for r in audit_results
        )
        high_clashes = sum(
            r.high_severity_count if hasattr(r, "high_severity_count")
            else sum(1 for c in r.get("clashes", []) if c.get("severity") == "high")
            for r in audit_results
        )

        lines = [
            "## 3. Tong Quan Ket Qua Doi Soat",
            "",
            f"| Chi so | Gia tri |",
            f"|---|---|",
            f"| So tang duoc kiem tra | {total} |",
            f"| Tong xung dot phat hien | {total_clashes} |",
            f"| Xung dot nghiem trong (HIGH) | {high_clashes} |",
            "",
            "**Ket qua theo Tang:**",
            "",
            "| Tang | Xung dot | HIGH | MEDIUM | LOW | Model AI |",
            "|---|---|---|---|---|---|",
        ]

        for r in audit_results:
            if hasattr(r, "clashes"):
                level = r.level
                clashes = r.clashes
                ai_model = r.ai_model
            else:
                level = r.get("level", "?")
                clashes = r.get("clashes", [])
                ai_model = r.get("ai_model", "?")

            counts = {"high": 0, "medium": 0, "low": 0}
            for c in clashes:
                sev = (c.severity if hasattr(c, "severity") else c.get("severity", "medium")).lower()
                counts[sev] = counts.get(sev, 0) + 1

            lines.append(
                f"| {level} | {len(clashes)} | "
                f"{counts['high']} | {counts['medium']} | {counts['low']} | {ai_model} |"
            )

        return "\n".join(lines)

    def _render_clash_details(self, audit_results: list[Any]) -> str:
        lines = ["## 4. Chi Tiet Xung Dot"]

        for r in audit_results:
            level = r.level if hasattr(r, "level") else r.get("level", "?")
            clashes = r.clashes if hasattr(r, "clashes") else r.get("clashes", [])
            summary = r.summary if hasattr(r, "summary") else r.get("summary", "")

            lines += [f"\n### Tang: {level}", ""]
            if summary:
                lines += [f"**Nhan xet chung:** {summary}", ""]

            if not clashes:
                lines.append("_Khong phat hien xung dot_")
                continue

            lines += [
                "| # | Muc do | Vi tri | Bo mon | Mo ta | Khuyen nghi |",
                "|---|---|---|---|---|---|",
            ]
            for i, c in enumerate(clashes, 1):
                if hasattr(c, "severity"):
                    sev, loc, discs, desc, rec = (
                        c.severity, c.location,
                        "/".join(c.disciplines), c.description, c.recommendation,
                    )
                else:
                    sev = c.get("severity", "?")
                    loc = c.get("location", "")
                    discs = "/".join(c.get("disciplines", []))
                    desc = c.get("description", "")
                    rec = c.get("recommendation", "")

                sev_label = {"high": "**HIGH**", "medium": "MEDIUM", "low": "low"}.get(sev, sev)
                lines.append(
                    f"| {i} | {sev_label} | {loc[:50]} | {discs} | "
                    f"{desc[:80]} | {rec[:60]} |"
                )

        return "\n".join(lines)

    def _render_risk_heatmap(self, audit_results: list[Any]) -> str:
        """Render a simple text-based risk heat-map per level."""
        lines = ["## 5. Ban Do Rui Ro (Heat Map)", ""]
        lines += [
            "Muc do rui ro: HIGH = [!!!] | MEDIUM = [!!] | LOW = [!] | None = [ ]",
            "",
        ]

        for r in audit_results:
            level = r.level if hasattr(r, "level") else r.get("level", "?")
            clashes = r.clashes if hasattr(r, "clashes") else r.get("clashes", [])
            high = sum(
                1 for c in clashes
                if (c.severity if hasattr(c, "severity") else c.get("severity", "")) == "high"
            )
            med = sum(
                1 for c in clashes
                if (c.severity if hasattr(c, "severity") else c.get("severity", "")) == "medium"
            )
            low = len(clashes) - high - med

            if high > 0:
                risk = "[!!!]"
            elif med > 0:
                risk = "[!! ]"
            elif low > 0:
                risk = "[!  ]"
            else:
                risk = "[   ]"

            bar = f"Tang {level:<6} {risk} HIGH={high} MED={med} LOW={low}"
            lines.append(bar)

        return "\n".join(lines)

    def _render_footer(self) -> str:
        return (
            "---\n"
            f"*Bao cao duoc tao tu dong boi CCBA AI Platform vao {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"
            "*Cac xung dot can duoc xac nhan boi ky su truoc khi xu ly.*"
        )

    def _export_json_summary(
        self,
        backbone: Any | None,
        audit_results: list[Any],
        output_path: Path,
    ) -> None:
        """Export a machine-readable JSON summary."""
        data: dict[str, Any] = {
            "project": self.project_name,
            "generated_at": datetime.now().isoformat(),
            "backbone": backbone.to_dict() if backbone and hasattr(backbone, "to_dict") else None,
            "audit_results": [
                r.to_dict() if hasattr(r, "to_dict") else r
                for r in audit_results
            ],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("JSON summary written to %s", output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="IDOP Reporter Engine")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--backbone", help="Path to backbone.json from discovery")
    parser.add_argument("--audit", help="Path to audit results JSON")
    parser.add_argument("--output", default="report.md", help="Output report path")
    parser.add_argument("--author", default="CCBA Platform")
    args = parser.parse_args()

    backbone_data = None
    if args.backbone:
        with open(args.backbone, encoding="utf-8") as f:
            backbone_data = json.load(f)

    audit_data = []
    if args.audit:
        with open(args.audit, encoding="utf-8") as f:
            audit_data = json.load(f)

    reporter = IDOPReporter(project_name=args.project, author=args.author)
    out = reporter.synthesize(backbone_data, audit_data, Path(args.output))
    print(f"Report generated: {out}")
