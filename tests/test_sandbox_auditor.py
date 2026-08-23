"""Unit tests for SandboxAuditor guardrails (ADR 0046)."""

from pathlib import Path

import pytest
import yaml
from scripts.governance.sandbox_auditor import SandboxAuditor
from scripts.spoke.sandbox_promoter import WATERMARK_HEADER


@pytest.fixture
def valid_sandbox_workspace(tmp_path: Path) -> Path:
    """Create a compliant personal sandbox."""
    ws = tmp_path / "chuvu-sandbox"
    ws.mkdir()
    (ws / ".md").mkdir()
    ctx = {
        "project": {
            "name": "chuvu-sandbox",
            "archetype": "specialized_extension",
            "sub_type": "personal_sandbox",
        },
        "qc_governance": {
            "authorized_qc_level": "LEVEL_1_TECHNICAL_CHECK",
            "can_approve_iso_documents": False,
        },
    }
    (ws / ".md" / "workspace_context.yaml").write_text(
        yaml.safe_dump(ctx), encoding="utf-8"
    )
    (ws / "output").mkdir()
    (ws / "output" / "report.md").write_text(
        f"{WATERMARK_HEADER}\n\n# Nội dung thẩm tra", encoding="utf-8"
    )
    return ws


def test_sandbox_auditor_passes_clean_sandbox(valid_sandbox_workspace: Path):
    """Ensure compliant sandbox produces zero audit issues."""
    auditor = SandboxAuditor(valid_sandbox_workspace)
    report = auditor.audit()
    assert report.total_issues == 0
    assert not report.has_hard_errors


def test_sandbox_auditor_flags_exceeded_qc_level(tmp_path: Path):
    """Ensure auditor flags QC authorization > LEVEL_1 in sandbox."""
    ws = tmp_path / "illegal-qc-sandbox"
    ws.mkdir()
    (ws / ".md").mkdir()
    ctx = {
        "project": {
            "name": "illegal-qc-sandbox",
            "archetype": "specialized_extension",
            "sub_type": "personal_sandbox",
        },
        "qc_governance": {
            "authorized_qc_level": "LEVEL_3_DEPARTMENT_REVIEW",
        },
    }
    (ws / ".md" / "workspace_context.yaml").write_text(
        yaml.safe_dump(ctx), encoding="utf-8"
    )

    auditor = SandboxAuditor(ws)
    report = auditor.audit()
    assert report.total_issues == 1
    assert "LEVEL_1_TECHNICAL_CHECK" in report.issues[0].message


def test_sandbox_auditor_flags_missing_watermark(valid_sandbox_workspace: Path):
    """Ensure auditor flags unwatermarked draft outputs."""
    (valid_sandbox_workspace / "output" / "unwatermarked.md").write_text(
        "# Báo cáo không có watermark", encoding="utf-8"
    )
    auditor = SandboxAuditor(valid_sandbox_workspace)
    report = auditor.audit()
    assert report.total_issues == 1
    assert "watermark" in report.issues[0].message.lower()


def test_sandbox_auditor_skips_non_sandbox_workspaces(tmp_path: Path):
    """Ensure non-sandbox project delivery is skipped without false alarms."""
    ws = tmp_path / "project-delivery"
    ws.mkdir()
    (ws / ".md").mkdir()
    ctx = {
        "project": {
            "name": "project-delivery",
            "archetype": "project_delivery",
        },
        "qc_governance": {
            "authorized_qc_level": "LEVEL_5_FINAL_APPROVAL",
        },
    }
    (ws / ".md" / "workspace_context.yaml").write_text(
        yaml.safe_dump(ctx), encoding="utf-8"
    )
    (ws / "output").mkdir()
    (ws / "output" / "final.md").write_text("# Final document", encoding="utf-8")

    auditor = SandboxAuditor(ws)
    report = auditor.audit()
    assert report.total_issues == 0
