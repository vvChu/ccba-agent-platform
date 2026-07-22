"""Tests for On-Demand Consultation Dispatch Draft Generator."""

from pathlib import Path
import pytest
from ccba_legal.coordinator import LegalProcessor


def test_generate_consultation_dispatch_draft(tmp_path: Path) -> None:
    """Test generating On-Demand consultation dispatch draft when risk label is RED."""
    processor = LegalProcessor()
    
    output_docx_path = tmp_path / "Cong_van_Xin_y_kien.docx"
    draft_info = processor.generate_consultation_dispatch_draft(
        recipient="Cục Cảnh sát PCCC và CNCH - Bộ Công an",
        subject_summary="Thẩm duyệt thiết kế PCCC giai đoạn chuyển tiếp Luật 55/2024",
        output_file=output_docx_path,
    )
    
    assert draft_info["recipient"] == "Cục Cảnh sát PCCC và CNCH - Bộ Công an"
    assert draft_info["status"] == "success"
    assert output_docx_path.exists()
    assert output_docx_path.stat().st_size > 0
