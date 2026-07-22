"""Tests for Dual-Layer Reporter & Full Legal Advisory Coordinator Flow."""

from pathlib import Path

from ccba_legal.coordinator import LegalProcessor


def test_legal_processor_full_advisory_flow(tmp_path: Path) -> None:
    """Test full advisory flow: intake parsing -> conflict evaluation -> dual-layer report output."""
    processor = LegalProcessor()

    question = (
        "Năm 2026, Chủ đầu tư xin cấp phép thẩm định thiết kế PCCC cho công trình cấp I tại Hà Nội "
        "thì bị tạm đình chỉ thi công do hết hiệu lực văn bản."
    )

    output_file = tmp_path / "report_test.md"
    report = processor.generate_advisory_report(
        query_text=question,
        output_file=output_file,
    )

    assert "TẦNG 1: KHUYẾN NGHỊ TỐI ƯU" in report
    assert "TẦNG 2: MA TRẬN SO SÁNH RỦI RO CHI TIẾT" in report
    assert "Intake 5 Trục" in report
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == report
