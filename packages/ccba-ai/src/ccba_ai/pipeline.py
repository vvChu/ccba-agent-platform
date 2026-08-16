"""QCAuditPipeline — Unified Orchestrator Deep Seam for Multi-Discipline QC Audits."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ccba_ai.models import AuditReport

if TYPE_CHECKING:
    from ccba_ai.client import AIClient
    from ccba_ai.protocols import QCAuditEngine, QCDiscoveryEngine, QCReporterEngine


class AuditReportSummary(BaseModel):
    """Consolidated summary of multi-discipline QC audit across all levels."""

    project_name: str = ""
    levels_audited: list[str] = Field(default_factory=list)
    total_findings: int = 0
    high_severity_count: int = 0
    reports: list[AuditReport] = Field(default_factory=list)
    report_file: Path | None = None


class QCAuditPipeline:
    """Unified Orchestrator Deep Seam for Multi-Discipline QC Audits.

    Orchestrates Discovery -> Quad-View Alignment -> Vision Audit -> Technical Reporter.
    """

    def __init__(
        self,
        discovery_engine: QCDiscoveryEngine | None = None,
        audit_engine: QCAuditEngine | None = None,
        reporter_engine: QCReporterEngine | None = None,
        ai_client: AIClient | None = None,
    ) -> None:
        self.discovery_engine = discovery_engine
        self.audit_engine = audit_engine
        self.reporter_engine = reporter_engine
        self.ai_client = ai_client

    async def run_audit(
        self,
        project_dir: Path | str,
        output_dir: Path | str | None = None,
        disciplines: list[str] | None = None,
    ) -> AuditReportSummary:
        """Run full end-to-end QC audit on a project directory."""
        p_dir = Path(project_dir)
        out_dir = Path(output_dir) if output_dir else p_dir / "qc_reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        disc_list = disciplines or ["Architecture", "Structure", "MEP", "PCCC"]

        # 1. Discover drawings
        pdf_files = list(p_dir.glob("*.pdf"))
        backbone: Any = None
        if self.discovery_engine:
            backbone = await self.discovery_engine.discover(pdf_files)

        # 2. Audit levels
        audit_reports: list[AuditReport] = []
        if self.audit_engine:
            level_map: dict[str, list[Path]] = {}
            for pdf in pdf_files:
                level_name = pdf.stem
                level_map[level_name] = [pdf]
            audit_reports = await self.audit_engine.run_multi_level_audit(
                level_map, discipline_order=disc_list
            )

        # 3. Synthesize report
        report_file = out_dir / "qc_audit_report.md"
        if self.reporter_engine:
            self.reporter_engine.synthesize(
                backbone=backbone,
                audit_results=audit_reports,  # type: ignore[arg-type]
                output_path=report_file,
            )
        else:
            lines = [
                f"# Báo Cáo Thẩm Tra Chất Lượng Hồ Sơ: {p_dir.name}",
                f"- **Số lượng cấp độ/tầng đã quét**: {len(audit_reports)}",
                f"- **Tổng số lỗi phát hiện**: {sum(r.finding_count for r in audit_reports)}",
                "",
                "## Chi Tiết Các Tầng",
            ]
            for r in audit_reports:
                lines.append(f"### Tầng {r.level} (Mô hình: {r.ai_model})")
                for f in r.findings:
                    lines.append(f"- **[{f.severity.upper()}]** {f.location}: {f.description}")
            report_file.write_text("\n".join(lines), encoding="utf-8")

        total_find = sum(r.finding_count for r in audit_reports)
        high_sev = sum(r.high_severity_count for r in audit_reports)
        levels = [r.level for r in audit_reports] or [p.stem for p in pdf_files]

        return AuditReportSummary(
            project_name=p_dir.name,
            levels_audited=levels,
            total_findings=total_find,
            high_severity_count=high_sev,
            reports=audit_reports,
            report_file=report_file if report_file.exists() else None,
        )

    def run_audit_sync(
        self,
        project_dir: Path | str,
        output_dir: Path | str | None = None,
        disciplines: list[str] | None = None,
    ) -> AuditReportSummary:
        """Synchronously run full QC audit.

        Raises RuntimeError if an asyncio event loop is already running.
        Use 'await pipeline.run_audit(...)' directly instead.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "QCAuditPipeline.run_audit_sync() cannot be called from within a running event loop. "
                "Please use 'await pipeline.run_audit(...)' directly."
            )
        return asyncio.run(self.run_audit(project_dir, output_dir, disciplines))
