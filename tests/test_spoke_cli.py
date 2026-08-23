"""Tests for ccba-spoke CLI Tool (WF-04)."""

import json
from pathlib import Path

import pytest
import yaml
from scripts.spoke.spoke_cli import SpokeCLI, main


@pytest.fixture
def mock_spoke(tmp_path: Path) -> Path:
    """Create a mock spoke directory with workspace_context.yaml."""
    spoke_dir = tmp_path / "mock-spoke"
    spoke_dir.mkdir()
    md_dir = spoke_dir / ".md"
    md_dir.mkdir()

    context_data = {
        "project": {
            "name": "mock-spoke",
            "project_code": "2026-04-DHVN",
            "national_project_id": "VN-2026-001",
            "contract_id": "HD-2026-01",
            "archetype": "project_delivery",
            "type": "Thẩm tra thiết kế",
            "mode": "consulting",
        },
        "organizational_identity": {
            "owner_name": "Chu Vũ",
            "owner_email": "chuvu@ibst-bim.vn",
            "department": "PHONG_BIM_DU_AN",
            "seat_role": "CHU_TRI_HOP_DONG_PM",
        },
    }
    (md_dir / "workspace_context.yaml").write_text(
        yaml.safe_dump(context_data, allow_unicode=True), encoding="utf-8"
    )
    return spoke_dir


def test_spoke_cli_status(mock_spoke: Path, capsys: pytest.CaptureFixture[str]):
    """Test `ccba-spoke status` command."""
    cli = SpokeCLI(spoke_root=mock_spoke)
    res = cli.status()
    assert res == 0
    captured = capsys.readouterr().out
    assert "2026-04-DHVN" in captured
    assert "project_delivery" in captured
    assert "chuvu@ibst-bim.vn" in captured


def test_spoke_cli_stage_success(mock_spoke: Path, capsys: pytest.CaptureFixture[str]):
    """Test `ccba-spoke stage` creates valid PGV staging receipt."""
    report_file = mock_spoke / "bao_cao_tham_tra_pccc.md"
    report_file.write_text(
        "# Báo cáo Thẩm tra PCCC\n\nÁp dụng Nghị định 105/2025/NĐ-CP và QCVN 06:2022/BXD.\n",
        encoding="utf-8",
    )

    cli = SpokeCLI(spoke_root=mock_spoke)
    res = cli.stage(
        file_path=report_file,
        task_id="PGV-2026-001",
        title="Báo cáo Thẩm tra PCCC Đợt 1",
        notes="Nghiệm thu giai đoạn thiết kế kỹ thuật",
    )
    assert res == 0

    staged_dir = mock_spoke / ".md" / "idop_staged"
    assert staged_dir.exists()

    receipts = list(staged_dir.glob("PGV-*.json"))
    assert len(receipts) == 1

    receipt_data = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt_data["task_id"] == "PGV-2026-001"
    assert receipt_data["status"] == "STAGED_LOCAL"
    assert receipt_data["project_code"] == "2026-04-DHVN"
    assert receipt_data["author_email"] == "chuvu@ibst-bim.vn"
    assert len(receipt_data["sha256"]) == 64


def test_spoke_cli_stage_fails_on_superseded_law(
    mock_spoke: Path, capsys: pytest.CaptureFixture[str]
):
    """Test `ccba-spoke stage` catches superseded Decree 06/2021 violation."""
    bad_file = mock_spoke / "bad_report.md"
    bad_file.write_text(
        "# Báo cáo sai luật\n\nÁp dụng Nghị định 06/2021/NĐ-CP để quản lý chất lượng.\n",
        encoding="utf-8",
    )

    cli = SpokeCLI(spoke_root=mock_spoke)
    res = cli.stage(file_path=bad_file, task_id="PGV-ERR-001")
    assert res == 1  # Blocked by AI Pre-Submission Gate

    err_output = capsys.readouterr().err
    assert "Vi phạm Pháp luật Xây dựng" in err_output
    assert "Nghị định 06/2021/NĐ-CP đã hết hiệu lực" in err_output


def test_spoke_cli_flush_and_idempotent_replay(mock_spoke: Path):
    """Test `ccba-spoke flush` transitions records and performs idempotent replay."""
    report_file = mock_spoke / "report.md"
    report_file.write_text("# Report content per 105/2025", encoding="utf-8")

    cli = SpokeCLI(spoke_root=mock_spoke)
    cli.stage(file_path=report_file, task_id="PGV-FLUSH-001")

    # Flush 1: Should sync 1 record
    res = cli.flush(dry_run=False)
    assert res == 0

    staged_dir = mock_spoke / ".md" / "idop_staged"
    receipts = list(staged_dir.glob("PGV-*.json"))
    assert len(receipts) == 1

    receipt_data = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt_data["status"] == "SYNCED_SHAREPOINT"
    assert "synced_at" in receipt_data

    # Flush 2 (Idempotent replay): Queue is already clean
    res2 = cli.flush(dry_run=False)
    assert res2 == 0


def test_spoke_cli_main_entrypoint(mock_spoke: Path, capsys: pytest.CaptureFixture[str]):
    """Test `main()` entrypoint with CLI arguments."""
    report_file = mock_spoke / "cli_report.md"
    report_file.write_text("# Deliverable per 105/2025", encoding="utf-8")

    # 1. Test status via CLI
    ret = main(["--spoke", str(mock_spoke), "status"])
    assert ret == 0

    # 2. Test stage via CLI
    ret = main(
        [
            "--spoke",
            str(mock_spoke),
            "stage",
            "--file",
            str(report_file),
            "--task-id",
            "CLI-TASK-001",
            "--title",
            "CLI Test Report",
        ]
    )
    assert ret == 0

    # 3. Test flush via CLI
    ret = main(["--spoke", str(mock_spoke), "flush"])
    assert ret == 0
