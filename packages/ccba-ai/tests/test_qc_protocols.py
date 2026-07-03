"""Unit tests verifying CCBA QC Protocols and Mock-ability."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from ccba_ai import AuditFinding, AuditReport, QCAuditEngine, QCReporterEngine
from ccba_ai.protocols import QCDiscoveryEngine


class MockDiscoveryEngine:
    """A mock implementation of QCDiscoveryEngine protocol."""

    async def discover(
        self,
        pdf_paths: list[Path],
        extract_titleblocks: bool = True,
        run_ai: bool = True,
    ) -> dict[str, Any]:
        return {"project": "Mock Project", "total_files": len(pdf_paths), "sheets": []}


class MockAuditEngine:
    """A mock implementation of QCAuditEngine protocol."""

    async def run_multi_level_audit(
        self,
        level_images: dict[str, list[Path]],
        discipline_order: list[str] | None = None,
    ) -> list[AuditReport]:
        reports = []
        for level in level_images.keys():
            reports.append(
                AuditReport(
                    level=level,
                    ai_model="mock-model",
                    summary=f"Mock summary for {level}",
                    findings=[
                        AuditFinding(
                            severity="high",
                            location="Mock Location",
                            disciplines=["Arch", "KC"],
                            description="Mock clash detected",
                            recommendation="Review design",
                            source="mock_engine",
                        )
                    ],
                )
            )
        return reports


class MockReporterEngine:
    """A mock implementation of QCReporterEngine protocol."""

    def synthesize(
        self,
        backbone: Any | None = None,
        audit_results: list[AuditReport | dict] | None = None,
        output_path: Path = Path("report.md"),
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            f"Mock Technical Report\nResults count: {len(audit_results or [])}", encoding="utf-8"
        )
        return output_path


def test_protocol_conformance():
    """Verify mock engines satisfy their respective QC protocols."""
    discovery = MockDiscoveryEngine()
    audit = MockAuditEngine()
    reporter = MockReporterEngine()

    assert isinstance(discovery, QCDiscoveryEngine)
    assert isinstance(audit, QCAuditEngine)
    assert isinstance(reporter, QCReporterEngine)


def test_mock_orchestration_run():
    """Verify that we can run an orchestration flow using mock adapters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = Path(temp_dir) / "output"
        out_dir.mkdir()

        # Set up mock input data structure
        level_images = {
            "L1": [
                Path("dummy_arch.png"),
                Path("dummy_kc.png"),
                Path("dummy_mep.png"),
                Path("dummy_pccc.png"),
            ]
        }

        # Inject Mock engines mimicking orchestrator pipeline run
        audit_engine: QCAuditEngine = MockAuditEngine()
        reporter_engine: QCReporterEngine = MockReporterEngine()

        # Run mock audit pass
        import asyncio

        reports = asyncio.run(audit_engine.run_multi_level_audit(level_images))
        assert len(reports) == 1
        assert reports[0].level == "L1"
        assert reports[0].findings[0].severity == "high"

        # Run mock report synthesize
        report_file = out_dir / "QC_Report.md"
        saved_path = reporter_engine.synthesize(
            backbone=None, audit_results=reports, output_path=report_file
        )

        assert saved_path.exists()
        content = saved_path.read_text(encoding="utf-8")
        assert "Mock Technical Report" in content
        assert "Results count: 1" in content
