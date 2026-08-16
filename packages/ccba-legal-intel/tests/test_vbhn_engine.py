"""test_vbhn_engine.py - TDD unit tests for VBHNEngine Deep Seam."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccba_legal import DeltaPatch, DeltaPatchItem, MergedLegalDocument, PatchAction, VBHNEngine

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_vbhn_engine_merge_with_delta_patch(tmp_path: Path) -> None:
    """Verify VBHNEngine.merge_documents applies a DeltaPatch onto base markdown."""
    base_text = """### Điều 1. Phạm vi điều chỉnh
Quy chuẩn này quy định về thiết kế an toàn cháy.

### Điều 2. Đối tượng áp dụng
Quy chuẩn áp dụng cho công trình dân dụng.
"""
    patch = DeltaPatch(
        target_doc_id="06/2022/TT-BXD",
        amending_doc_id="01/2026/TT-BXD",
        patches=[
            DeltaPatchItem(
                node_id="dieu-1",
                action=PatchAction.REPLACE,
                new_content="Quy chuẩn này quy định về thiết kế PCCC cho nhà và công trình.",
                citation="Khoản 1 Điều 1 Thông tư 01/2026/TT-BXD",
            ),
            DeltaPatchItem(
                node_id="dieu-2",
                action=PatchAction.ABROGATE,
                citation="Khoản 2 Điều 1 Thông tư 01/2026/TT-BXD",
            ),
        ],
    )

    engine = VBHNEngine()
    result = engine.merge_documents(
        base_doc=base_text,
        amending_doc=patch,
        doc_meta={"title": "VBHN Quy chuẩn QCVN 06:2022/BXD"},
        output_path=tmp_path / "vbhn_06.md",
    )

    assert isinstance(result, MergedLegalDocument)
    assert result.title == "VBHN Quy chuẩn QCVN 06:2022/BXD"
    assert "Quy chuẩn này quy định về thiết kế PCCC cho nhà và công trình." in result.content
    assert "~~### Điều 2. Đối tượng áp dụng" in result.content
    assert result.patch_summary["replaced"] == 1
    assert result.patch_summary["abrogated"] == 1
    assert result.output_path is not None
    assert result.output_path.exists()


def test_vbhn_engine_merge_raw_strings() -> None:
    """Verify VBHNEngine can merge two raw strings end-to-end with mock LLM response."""
    base_text = """### Điều 5. Trách nhiệm của chủ đầu tư
Chủ đầu tư có trách nhiệm tổ chức thẩm tra.
"""
    amending_text = """### Điều 1. Sửa đổi Thông tư
Sửa đổi Điều 5 như sau: Chủ đầu tư tự tổ chức thẩm định.
"""
    mock_payload = {
        "target_doc_id": "06/2022/TT-BXD",
        "amending_doc_id": "01/2026/TT-BXD",
        "patches": [
            {
                "node_id": "dieu-5",
                "action": "REPLACE",
                "old_text_anchor": "Chủ đầu tư có trách nhiệm tổ chức thẩm tra.",
                "new_content": "Chủ đầu tư tự tổ chức thẩm định.",
                "citation": "Khoản 1 Điều 1 Thông tư sửa đổi",
            }
        ],
    }

    engine = VBHNEngine()
    result = engine.merge_documents(
        base_doc=base_text,
        amending_doc=amending_text,
        doc_meta={"mock_llm_response": json.dumps(mock_payload)},
    )

    assert isinstance(result, MergedLegalDocument)
    assert result.content is not None
    assert "Chủ đầu tư tự tổ chức thẩm định." in result.content
    assert result.patch_summary["replaced"] == 1
