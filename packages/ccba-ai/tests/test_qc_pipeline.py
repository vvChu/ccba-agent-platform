"""test_qc_pipeline.py - TDD unit tests for QCAuditPipeline Deep Seam."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from ccba_ai import AuditFinding, AuditReport, AuditReportSummary, QCAuditPipeline

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_qc_pipeline_run_audit_async(tmp_path: Path) -> None:
    """Verify QCAuditPipeline.run_audit coordinates Discovery, Audit, and Reporter."""

    async def _test_flow() -> None:
        drawing_dir = tmp_path / "drawings"
        drawing_dir.mkdir()
        (drawing_dir / "tang_01.pdf").write_bytes(b"%PDF-1.4 dummy")
        (drawing_dir / "tang_02.pdf").write_bytes(b"%PDF-1.4 dummy")

        mock_discovery = MagicMock()
        mock_discovery.discover = AsyncMock(return_value={"total_sheets": 2})

        mock_audit = MagicMock()
        mock_audit.run_multi_level_audit = AsyncMock(
            return_value=[
                AuditReport(
                    level="tang_01",
                    ai_model="gemini-2.5-flash",
                    findings=[
                        AuditFinding(
                            severity="high",
                            location="Trục A-B",
                            description="Xung đột ống gió MEP và dầm kết cấu",
                        )
                    ],
                )
            ]
        )

        mock_reporter = MagicMock()
        mock_reporter.synthesize.return_value = tmp_path / "qc_report.md"

        pipeline = QCAuditPipeline(
            discovery_engine=mock_discovery,
            audit_engine=mock_audit,
            reporter_engine=mock_reporter,
        )

        summary = await pipeline.run_audit(project_dir=drawing_dir, output_dir=tmp_path)

        assert isinstance(summary, AuditReportSummary)
        assert summary.project_name == "drawings"
        assert "tang_01" in summary.levels_audited
        assert summary.total_findings == 1
        assert summary.high_severity_count == 1
        assert mock_discovery.discover.called
        assert mock_audit.run_multi_level_audit.called
        assert mock_reporter.synthesize.called

    asyncio.run(_test_flow())


def test_qc_pipeline_run_audit_sync(tmp_path: Path) -> None:
    """Verify QCAuditPipeline.run_audit_sync executes synchronously with default fallback."""
    drawing_dir = tmp_path / "drawings"
    drawing_dir.mkdir()
    (drawing_dir / "tang_01.pdf").write_bytes(b"%PDF-1.4 dummy")

    pipeline = QCAuditPipeline()
    summary = pipeline.run_audit_sync(project_dir=drawing_dir, output_dir=tmp_path)

    assert isinstance(summary, AuditReportSummary)
    assert summary.project_name == "drawings"
    assert summary.report_file is not None
    assert summary.report_file.exists()
