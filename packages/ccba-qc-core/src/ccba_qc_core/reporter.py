"""Reporter Engine — Coordination matrix generation, clash summary tables, and Markdown report synthesis."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from ccba_ai import AuditReport

logger = logging.getLogger(__name__)


class ReporterEngine:
    """Tổng hợp dữ liệu từ Discovery và Audit để xuất báo cáo kỹ thuật Markdown và Heat Map."""

    def __init__(
        self,
        project_name: str,
        author: str = "CCBA Platform",
        company: str = "CCBA Engineering",
    ) -> None:
        self.project_name = project_name
        self.author = author
        self.company = company

    def synthesize(
        self,
        backbone: Any | None = None,
        audit_results: Sequence[AuditReport | dict[str, Any]] | None = None,
        output_path: Path = Path("report.md"),
    ) -> Path:
        """Tạo báo cáo Markdown tổng hợp."""
        standardized_results: list[AuditReport] = []
        for r in audit_results or []:
            if isinstance(r, dict):
                standardized_results.append(AuditReport.model_validate(r))
            else:
                standardized_results.append(r)

        sections: list[str] = [
            self._render_header(),
        ]

        if backbone is not None:
            sections.append(self._render_backbone_summary(backbone))
            sections.append(self._render_coordination_matrix(backbone))

        if standardized_results:
            sections.append(self._render_audit_overview(standardized_results))
            sections.append(self._render_clash_details(standardized_results))
            sections.append(self._render_risk_heatmap(standardized_results))

        sections.append(self._render_footer())

        report = "\n\n".join(sections)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s", output_path)

        json_path = output_path.with_suffix(".json")
        self._export_json_summary(backbone, standardized_results, json_path)

        return output_path

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

        disc_counts: dict[str, int] = {}
        for s in sheets:
            disc = s.get("discipline", "Unknown") or "Unknown"
            disc_counts[disc] = disc_counts.get(disc, 0) + 1

        lines = [
            "## 1. Tom Tat Ho So",
            "",
            "| Chi so | Gia tri |",
            "|---|---|",
            f"| Tong so file PDF | {total_files} |",
            f"| Tong so trang ban ve | {total_sheets} |",
        ]

        if bd.get("index_pages"):
            n_idx = sum(len(v) for v in bd["index_pages"].values())
            lines.append(f"| Trang muc luc phat hien | {n_idx} |")

        lines += ["", "**Phan bo theo Bo mon:**", ""]
        lines += ["| Bo mon | So ban ve |", "|---|---|"]
        for disc, count in sorted(disc_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {disc} | {count} |")

        return "\n".join(lines)

    def _render_coordination_matrix(self, backbone: Any) -> str:
        bd = backbone.to_dict() if hasattr(backbone, "to_dict") else backbone
        sheets = bd.get("sheets", [])

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

    def _render_audit_overview(self, audit_results: list[AuditReport]) -> str:
        total = len(audit_results)
        total_clashes = sum(r.finding_count for r in audit_results)
        high_clashes = sum(r.high_severity_count for r in audit_results)

        lines = [
            "## 3. Tong Quan Ket Qua Doi Soat",
            "",
            "| Chi so | Gia tri |",
            "|---|---|",
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
            findings = r.findings
            counts = {"high": 0, "medium": 0, "low": 0}
            for f in findings:
                sev = f.severity.lower()
                counts[sev] = counts.get(sev, 0) + 1

            lines.append(
                f"| {r.level} | {len(findings)} | "
                f"{counts['high']} | {counts['medium']} | {counts['low']} | {r.ai_model} |"
            )

        return "\n".join(lines)

    def _render_clash_details(self, audit_results: list[AuditReport]) -> str:
        lines = ["## 4. Chi Tiet Xung Dot"]

        for r in audit_results:
            lines += [f"\n### Tang: {r.level}", ""]
            if r.summary:
                lines += [f"**Nhan xet chung:** {r.summary}", ""]

            if not r.findings:
                lines.append("_Khong phat hien xung dot_")
                continue

            lines += [
                "| # | Muc do | Vi tri | Bo mon | Mo ta | Khuyen nghi |",
                "|---|---|---|---|---|---|",
            ]

            for i, f in enumerate(r.findings, 1):
                sev, loc, discs, desc, rec = (
                    f.severity,
                    f.location,
                    "/".join(f.disciplines),
                    f.description,
                    f.recommendation,
                )
                sev_label = {"high": "**HIGH**", "medium": "MEDIUM", "low": "low"}.get(sev, sev)
                lines.append(
                    f"| {i} | {sev_label} | {loc[:50]} | {discs} | {desc[:80]} | {rec[:60]} |"
                )

        return "\n".join(lines)

    def _render_risk_heatmap(self, audit_results: list[AuditReport]) -> str:
        lines = [
            "## 5. Ban Do Rui Ro (Heat Map)",
            "",
            "Muc do rui ro: HIGH = [!!!] | MEDIUM = [!!] | LOW = [!] | None = [ ]",
            "",
        ]

        for r in audit_results:
            findings = r.findings
            high = sum(1 for f in findings if f.severity.lower() == "high")
            med = sum(1 for f in findings if f.severity.lower() == "medium")
            low = len(findings) - high - med

            if high > 0:
                risk = "[!!!]"
            elif med > 0:
                risk = "[!! ]"
            elif low > 0:
                risk = "[!  ]"
            else:
                risk = "[   ]"

            lines.append(f"Tang {r.level:<6} {risk} HIGH={high} MED={med} LOW={low}")

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
        audit_results: list[AuditReport],
        output_path: Path,
    ) -> None:
        data: dict[str, Any] = {
            "project": self.project_name,
            "generated_at": datetime.now().isoformat(),
            "backbone": backbone.to_dict() if backbone and hasattr(backbone, "to_dict") else None,
            "audit_results": [r.to_dict() for r in audit_results],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("JSON summary written to %s", output_path)


# Backward compatibility alias
IDOPReporter = ReporterEngine
