"""QCAuditPipeline — Unified Orchestrator Deep Seam for Multi-Discipline QC Audits."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ccba_ai.models import AuditReport
from ccba_ai.routing import ModelArchetype

if TYPE_CHECKING:
    from ccba_ai.client import AIClient
    from ccba_ai.protocols import QCAuditEngine, QCDiscoveryEngine, QCReporterEngine

logger = logging.getLogger(__name__)


class AuditReportSummary(BaseModel):
    """Consolidated summary of multi-discipline QC audit across all levels."""

    project_name: str = ""
    levels_audited: list[str] = Field(default_factory=list)
    total_findings: int = 0
    high_severity_count: int = 0
    reports: list[AuditReport] = Field(default_factory=list)
    report_file: Path | None = None


def _synthesize_or_write_fallback(
    reporter_engine: QCReporterEngine | None,
    project_name: str,
    backbone: Any,
    audit_reports: list[AuditReport],
    report_file: Path,
) -> None:
    """Delegate report synthesis to QCReporterEngine or write fallback Markdown."""
    if reporter_engine:
        reporter_engine.synthesize(
            backbone=backbone,
            audit_results=audit_reports,  # type: ignore[arg-type]
            output_path=report_file,
        )
        return

    lines = [
        f"# Báo Cáo Thẩm Tra Chất Lượng Hồ Sơ: {project_name}",
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


class QCAuditPipeline:
    """Unified Orchestrator Deep Seam for Multi-Discipline QC Audits.

    Orchestrates Discovery -> Quad-View Alignment -> Vision Audit -> Technical Reporter.
    """

    _fault_tolerant: bool = False

    def __init__(
        self,
        discovery_engine: QCDiscoveryEngine | None = None,
        audit_engine: QCAuditEngine | None = None,
        reporter_engine: QCReporterEngine | None = None,
        ai_client: AIClient | None = None,
        ai_model: str = ModelArchetype.REASONING,
    ) -> None:
        self.discovery_engine = discovery_engine
        self.audit_engine = audit_engine
        self.reporter_engine = reporter_engine
        self.ai_client = ai_client
        self.ai_model = ai_model

    def _resolve_discovery_engine(self, p_dir: Path, out_dir: Path) -> QCDiscoveryEngine | None:
        return self.discovery_engine

    def _resolve_audit_engine(self, out_dir: Path) -> QCAuditEngine | None:
        return self.audit_engine

    def _resolve_reporter_engine(self, p_dir: Path) -> QCReporterEngine | None:
        return self.reporter_engine

    async def _invoke_discovery(self, disc_engine: QCDiscoveryEngine, pdf_files: list[Path]) -> Any:
        return await disc_engine.discover(pdf_files)

    async def _run_discovery_stage(self, p_dir: Path, out_dir: Path, pdf_files: list[Path]) -> Any:
        disc_engine = self._resolve_discovery_engine(p_dir, out_dir)
        if not disc_engine:
            return None
        if not self._fault_tolerant:
            return await self._invoke_discovery(disc_engine, pdf_files)
        try:
            return await self._invoke_discovery(disc_engine, pdf_files)
        except Exception as exc:
            logger.warning("Discovery warning: %s, continuing with file listing", exc)
            return None

    async def _run_audit_stage(
        self, out_dir: Path, pdf_files: list[Path], disc_list: list[str]
    ) -> list[AuditReport]:
        audit_engine = self._resolve_audit_engine(out_dir)
        if not audit_engine:
            return []
        level_map: dict[str, list[Path]] = {pdf.stem: [pdf] for pdf in pdf_files}
        if self._fault_tolerant and not level_map:
            return []
        if not self._fault_tolerant:
            return await audit_engine.run_multi_level_audit(level_map, discipline_order=disc_list)
        try:
            return await audit_engine.run_multi_level_audit(level_map, discipline_order=disc_list)
        except Exception as exc:
            logger.warning("Audit run warning: %s", exc)
            return []

    def _write_report(
        self,
        p_dir: Path,
        backbone: Any,
        audit_reports: list[AuditReport],
        report_file: Path,
    ) -> None:
        reporter = self._resolve_reporter_engine(p_dir)
        if not self._fault_tolerant:
            _synthesize_or_write_fallback(
                reporter, p_dir.name, backbone, audit_reports, report_file
            )
            return
        try:
            _synthesize_or_write_fallback(
                reporter, p_dir.name, backbone, audit_reports, report_file
            )
        except Exception as exc:
            logger.warning("Report synthesis warning: %s, writing fallback report", exc)
            _synthesize_or_write_fallback(None, p_dir.name, backbone, audit_reports, report_file)

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

        pdf_files = sorted(p_dir.glob("*.pdf"), key=lambda p: p.stem)
        backbone = await self._run_discovery_stage(p_dir, out_dir, pdf_files)
        audit_reports = await self._run_audit_stage(out_dir, pdf_files, disc_list)

        report_file = out_dir / "qc_audit_report.md"
        self._write_report(p_dir, backbone, audit_reports, report_file)

        return AuditReportSummary(
            project_name=p_dir.name,
            levels_audited=[r.level for r in audit_reports] or [p.stem for p in pdf_files],
            total_findings=sum(r.finding_count for r in audit_reports),
            high_severity_count=sum(r.high_severity_count for r in audit_reports),
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
