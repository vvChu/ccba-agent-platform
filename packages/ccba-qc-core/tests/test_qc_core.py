"""test_qc_core.py - Fast isolated unit tests for ccba_qc_core Deep Seams."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ccba_ai import AuditFinding, AuditReport, AuditReportSummary
from ccba_qc_core import QCAuditPipeline
from ccba_qc_core.discovery import (
    DiscoveryEngine,
    ProjectBackbone,
    SheetEntry,
    _normalize_vn,
)
from ccba_qc_core.pccc import PcccMapReduceEngine
from ccba_qc_core.quadview import _parse_audit_response
from ccba_qc_core.reporter import ReporterEngine
from ccba_qc_core.semantic import SemanticAuditEngine

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_sheet_entry_and_backbone_models(tmp_path: Path) -> None:
    """Verify SheetEntry and ProjectBackbone dataclass serialization."""
    s1 = SheetEntry(
        file="drawings.pdf",
        page_num=0,
        sheet_no="A-101",
        title="Mat bang Tang 1",
        level="Tang 1",
        discipline="Arch",
    )
    backbone = ProjectBackbone(
        project="Test Hospital",
        generated_at="2026-09-10T00:00:00",
        total_files=1,
        total_sheets=1,
        sheets=[s1],
        index_pages={"drawings.pdf": [0]},
    )

    data = backbone.to_dict()
    assert data["project"] == "Test Hospital"
    assert len(data["sheets"]) == 1
    assert data["sheets"][0]["sheet_no"] == "A-101"

    engine = DiscoveryEngine(project_name="Test Hospital", output_dir=tmp_path)
    out_file = tmp_path / "backbone.json"
    engine.export(backbone, out_file)
    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["total_sheets"] == 1


def test_normalize_vn() -> None:
    """Verify Vietnamese normalization strips diacritics for robust matching."""
    assert "danh sach" in _normalize_vn("danh sa\u0301ch").lower()
    assert "muc luc" in _normalize_vn("mu\u0323c lu\u0323c").lower()


def test_reporter_engine_synthesize(tmp_path: Path) -> None:
    """Verify ReporterEngine generates Markdown report, matrix, and JSON summary."""
    s1 = SheetEntry(
        file="arch.pdf",
        page_num=0,
        sheet_no="A-01",
        title="Kien truc",
        level="L1",
        discipline="Arch",
    )
    s2 = SheetEntry(
        file="kc.pdf",
        page_num=0,
        sheet_no="S-01",
        title="Ket cau",
        level="L1",
        discipline="KC",
    )
    backbone = ProjectBackbone(
        project="Sample Project",
        generated_at="2026-09-10",
        total_files=2,
        total_sheets=2,
        sheets=[s1, s2],
    )

    findings = [
        AuditFinding(
            severity="high",
            location="Truc 1-2",
            disciplines=["Arch", "KC"],
            description="Cot lech tim",
            recommendation="Doi vi tri cot",
        ),
        AuditFinding(
            severity="low",
            location="Phong ky thuat",
            disciplines=["MEP"],
            description="Thieu cua gio",
            recommendation="Bo sung",
        ),
    ]
    report_item = AuditReport(
        level="L1",
        ai_model="mock-model",
        findings=findings,
        summary="Co 2 van de can phoi hop.",
    )

    reporter = ReporterEngine(project_name="Sample Project", author="Unit Tester")
    out_md = tmp_path / "report.md"
    res = reporter.synthesize(backbone=backbone, audit_results=[report_item], output_path=out_md)

    assert res.exists()
    content = out_md.read_text(encoding="utf-8")
    assert "# BAO CAO RA SOAT DUONG GANG KY THUAT" in content
    assert "Sample Project" in content
    assert "Truc 1-2" in content
    assert "Ban Do Rui Ro (Heat Map)" in content

    out_json = out_md.with_suffix(".json")
    assert out_json.exists()
    json_data = json.loads(out_json.read_text(encoding="utf-8"))
    assert json_data["project"] == "Sample Project"
    assert len(json_data["audit_results"]) == 1


def test_quadview_parse_audit_response() -> None:
    """Verify _parse_audit_response extracts findings correctly from json."""
    sample_json = json.dumps(
        {
            "summary": "Overall good",
            "clashes": [
                {
                    "severity": "HIGH",
                    "location": "Grid C4",
                    "disciplines": ["MEP", "Struct"],
                    "description": "Pipe penetrates beam without sleeve",
                    "recommendation": "Add sleeve box",
                }
            ],
        }
    )
    findings, summary = _parse_audit_response(sample_json)
    assert summary == "Overall good"
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].location == "Grid C4"
    assert "MEP" in findings[0].disciplines


def test_semantic_audit_engine() -> None:
    """Verify SemanticAuditEngine parses LLM response into AuditReport."""

    async def _run() -> None:
        mock_response = json.dumps(
            {
                "summary": "Nhat quan tuong doi.",
                "conflicts": [
                    {
                        "severity": "medium",
                        "disciplines": "Arch vs KC",
                        "location": "Phong hop",
                        "description": "Ten phong Arch la Phong Hop, KC ghi la Kho",
                        "recommendation": "Sua lai KC thanh Phong Hop",
                    }
                ],
            }
        )
        engine = SemanticAuditEngine()
        with patch("ccba_ai.async_ai.chat_multi", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            report = await engine.run_audit(
                level_label="Tang 2",
                arch_text="Phong Hop",
                kc_text="Kho",
                mep_text="",
                pccc_text="",
            )

        assert report.level == "Tang 2"
        assert len(report.findings) == 1
        assert report.findings[0].severity == "medium"
        assert "Phong Hop" in report.findings[0].description

    asyncio.run(_run())


def test_pccc_map_reduce_engine(tmp_path: Path) -> None:
    """Verify PcccMapReduceEngine executes full map reduce workflow with mock LLM."""

    async def _run() -> None:
        engine = PcccMapReduceEngine(ai_model="mock-pccc")

        mock_res1 = json.dumps({"findings": [{"severity": "high", "issue": "Thieu GTEL"}]})
        mock_res2 = json.dumps({"findings": [{"severity": "medium", "issue": "Cot ap bom"}]})
        mock_res3 = json.dumps({"findings": [{"severity": "low", "issue": "Bien bao Exit"}]})
        mock_res4 = json.dumps(
            {
                "overall_quality_score": 88,
                "summary": "Ho so co 3 loi can chinh sua",
                "qcvn_compliance_status": "NEEDS_REVIEW",
                "final_findings": [
                    {
                        "severity": "high",
                        "category": "Legal",
                        "issue": "Thieu GTEL",
                        "recommendation": "Bo sung truyen tin",
                    }
                ],
            }
        )

        with patch("ccba_ai.async_ai.chat_multi", new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = [mock_res1, mock_res2, mock_res3, mock_res4]

            out_report = tmp_path / "pccc_out.md"
            res = await engine.execute_full_audit(
                thuyet_minh="Noi dung thuyet minh",
                arch_pccc="Ban ve kien truc",
                mep_pccc="Ban ve mep",
                gop_y="",
                output_file=out_report,
            )

        assert res["overall_quality_score"] == 88
        assert res["qcvn_compliance_status"] == "NEEDS_REVIEW"
        assert out_report.exists()
        content = out_report.read_text(encoding="utf-8")
        assert "Thieu GTEL" in content
        assert "NEEDS_REVIEW" in content

    asyncio.run(_run())


def test_qc_audit_pipeline_orchestration(tmp_path: Path) -> None:
    """Verify QCAuditPipeline coordinates discovery, audit, and reporter end-to-end."""
    # Setup dummy project dir with a sample pdf
    p_dir = tmp_path / "project_alpha"
    p_dir.mkdir()
    pdf_dummy = p_dir / "tang_01.pdf"
    pdf_dummy.write_bytes(b"%PDF-1.4 dummy pdf content")

    mock_discovery = AsyncMock()
    mock_discovery.discover.return_value = ProjectBackbone(
        project="project_alpha",
        generated_at="2026-09-10",
        total_files=1,
        total_sheets=1,
        sheets=[],
    )

    finding = AuditFinding(
        category="Architecture",
        location="Grid A-1",
        description="Dam bi lech truc 50mm",
        severity="high",
    )
    mock_report = AuditReport(
        level="tang_01",
        ai_model="gemini-3.7-flash",
        findings=[finding],
    )
    mock_audit = AsyncMock()
    mock_audit.run_multi_level_audit.return_value = [mock_report]

    mock_reporter = ReporterEngine(project_name="project_alpha")

    pipeline = QCAuditPipeline(
        discovery_engine=mock_discovery,
        audit_engine=mock_audit,
        reporter_engine=mock_reporter,
    )

    out_dir = tmp_path / "qc_output"
    summary = pipeline.run_audit_sync(
        project_dir=p_dir,
        output_dir=out_dir,
    )

    assert isinstance(summary, AuditReportSummary)
    assert summary.project_name == "project_alpha"
    assert summary.total_findings == 1
    assert summary.high_severity_count == 1
    assert len(summary.reports) == 1
    assert summary.report_file is not None
    assert summary.report_file.exists()

