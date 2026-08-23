"""Tests for CCBA Personal Sandbox Promotion Engine (ADR 0046)."""

import json
from pathlib import Path

import pytest
import yaml
from scripts.spoke.sandbox_promoter import (
    WATERMARK_HEADER,
    SandboxPromoter,
)


@pytest.fixture
def sandbox_workspace(tmp_path: Path) -> Path:
    """Create a mock personal sandbox workspace."""
    ws = tmp_path / "chuvu-sandbox"
    ws.mkdir()
    md_dir = ws / ".md"
    md_dir.mkdir()

    context = {
        "project": {
            "name": "chuvu-sandbox",
            "archetype": "specialized_extension",
            "sub_type": "personal_sandbox",
            "hub_path": str(tmp_path / "hub"),
        },
        "organizational_identity": {
            "owner_name": "Chu Vũ",
            "owner_email": "chuvu@ibst-bim.vn",
            "department": "PHONG_RD_HTQT",
            "seat_role": "IDOP_LEAD",
        },
        "guardrails": {
            "sandbox_mode": True,
        },
    }
    (md_dir / "workspace_context.yaml").write_text(yaml.safe_dump(context), encoding="utf-8")

    output_dir = ws / "output"
    output_dir.mkdir()
    doc = f"{WATERMARK_HEADER}\n\n# Báo Cáo Thẩm Tra Kỹ Thuật PCCC\nNội dung thẩm tra chi tiết...\n"
    (output_dir / "audit_report.md").write_text(doc, encoding="utf-8")

    return ws


@pytest.fixture
def target_delivery_project(tmp_path: Path) -> Path:
    """Create a mock project delivery workspace."""
    target = tmp_path / "2026-04-dh-viet-nhat"
    target.mkdir()
    md_dir = target / ".md"
    md_dir.mkdir()

    context = {
        "project": {
            "name": "2026-04-dh-viet-nhat",
            "archetype": "project_delivery",
            "type": "Thẩm tra thiết kế",
        }
    }
    (md_dir / "workspace_context.yaml").write_text(yaml.safe_dump(context), encoding="utf-8")
    return target


def test_promoter_blocks_non_sandbox_source(tmp_path: Path, target_delivery_project: Path):
    """Ensure promoter blocks execution if source is not a personal sandbox."""
    invalid_ws = tmp_path / "invalid-spoke"
    invalid_ws.mkdir()
    md_dir = invalid_ws / ".md"
    md_dir.mkdir()
    context = {
        "project": {
            "name": "invalid-spoke",
            "archetype": "project_delivery",
        }
    }
    (md_dir / "workspace_context.yaml").write_text(yaml.safe_dump(context), encoding="utf-8")

    with pytest.raises(ValueError, match="personal_sandbox"):
        SandboxPromoter(sandbox_root=invalid_ws)


def test_promoter_cleanse_watermark_and_copies_to_target(
    sandbox_workspace: Path, target_delivery_project: Path
):
    """Verify that promoter strips draft watermark and copies to target spoke."""
    promoter = SandboxPromoter(sandbox_root=sandbox_workspace)
    result = promoter.promote(
        target_spoke_path=target_delivery_project,
        files=["output/audit_report.md"],
        pgv_code="PGV-2026-08-014",
    )

    assert result.success is True
    assert len(result.promoted_files) == 1

    target_file = target_delivery_project / "output" / "audit_report.md"
    assert target_file.exists()
    content = target_file.read_text(encoding="utf-8")

    assert WATERMARK_HEADER not in content
    assert "# Báo Cáo Thẩm Tra Kỹ Thuật PCCC" in content


def test_promoter_creates_pgv_staging_receipt(
    sandbox_workspace: Path, target_delivery_project: Path
):
    """Verify that promoter creates an IDOP PGV staging receipt in .md/idop_staged/."""
    promoter = SandboxPromoter(sandbox_root=sandbox_workspace)
    result = promoter.promote(
        target_spoke_path=target_delivery_project,
        files=["output/audit_report.md"],
        pgv_code="PGV-2026-08-014",
    )

    assert result.staged_receipt_path is not None
    assert result.staged_receipt_path.exists()

    receipt_data = json.loads(result.staged_receipt_path.read_text(encoding="utf-8"))
    assert receipt_data["pgv_code"] == "PGV-2026-08-014"
    assert receipt_data["status"] == "AWAITING_PM_APPROVAL"
    assert receipt_data["author"]["owner_name"] == "Chu Vũ"
    assert receipt_data["author"]["seat_role"] == "IDOP_LEAD"
    assert len(receipt_data["deliverables"]) == 1


def test_promoter_dry_run_does_not_modify_files(
    sandbox_workspace: Path, target_delivery_project: Path
):
    """Verify dry-run execution makes no changes."""
    promoter = SandboxPromoter(sandbox_root=sandbox_workspace)
    result = promoter.promote(
        target_spoke_path=target_delivery_project,
        files=["output/audit_report.md"],
        pgv_code="PGV-2026-08-014",
        dry_run=True,
    )

    assert result.success is True
    target_file = target_delivery_project / "output" / "audit_report.md"
    assert not target_file.exists()
