# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests verifying vbpl_admin template extraction, natural sort, and legal basis graph."""

from __future__ import annotations

import re
from pathlib import Path

from ccba_legal.converters.vbpl_admin import (
    _extract_and_export_templates,
    extract_legal_basis_graph,
)


def test_form_sort_key_alphanumeric():
    """Verify that form numbers with alphanumeric suffixes sort naturally without ValueError."""
    forms = ["02", "01b", "10a", "01a", "01"]

    def _form_sort_key(tag: str) -> tuple[int, str]:
        m = re.match(r"^(\d+)(.*)$", tag)
        if m:
            return (int(m.group(1)), m.group(2))
        return (999, tag)

    sorted_result = sorted(forms, key=_form_sort_key)
    assert sorted_result == ["01", "01a", "01b", "02", "10a"]


def test_extract_and_export_templates_alphanumeric(tmp_path: Path):
    """Verify that templates with alphanumeric form numbers (01a, 01b) export without crashing."""
    sample_md = """
# Điều 1. Phạm vi điều chỉnh
Nội dung điều khoản...

# __PHỤ LỤC I__ BIỂU MẪU QUẢN LÝ DỰ ÁN

# __Mẫu số 01a.__ Tờ trình thẩm định báo cáo nghiên cứu khả thi
Kính gửi: Cơ quan chuyên môn về xây dựng.

# __Mẫu số 01b.__ Tờ trình thẩm định thiết kế xây dựng triển khai sau thiết kế cơ sở
Kính gửi: Người quyết định đầu tư.
"""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    pure_body, created_templates = _extract_and_export_templates(
        sample_md, templates_dir, doc_num_str="15/2021/NĐ-CP"
    )

    assert "Điều 1" in pure_body
    assert "PHỤ LỤC I" not in pure_body
    assert len(created_templates) == 2
    # Verify both templates were created successfully
    filenames = [t.name for t in created_templates]
    assert any("01a" in fn for fn in filenames)
    assert any("01b" in fn for fn in filenames)


def test_extract_legal_basis_graph():
    """Verify that legal basis citations are parsed and mapped to canonical doc_ids."""
    sample_text = """
CĂN CỨ:
Căn cứ Luật Xây dựng số 50/2014/QH13;
Căn cứ Luật sửa đổi, bổ sung một số điều của Luật Xây dựng số 62/2020/QH14;
Căn cứ Nghị định số 15/2021/NĐ-CP ngày 03 tháng 3 năm 2021 của Chính phủ;
"""
    registry_lookup = {
        "50/2014/QH13": "luat_50_2014_qh13",
        "62/2020/QH14": "luat_62_2020_qh14",
        "15/2021/NĐ-CP": "nghi_dinh_15_2021_nd_cp",
    }
    graph = extract_legal_basis_graph(sample_text, registry_lookup)
    assert len(graph) >= 3
    doc_ids = [item["doc_id"] for item in graph]
    assert "luat_50_2014_qh13" in doc_ids
    assert "nghi_dinh_15_2021_nd_cp" in doc_ids


def test_vbpl_bundle_exports_backward_compatibility():
    """Verify that SSoT constants and both canonical and legacy functions are exported and identical."""
    from ccba_legal.constants import CURRENT_OKF_SPEC, CURRENT_OKF_VERSION
    from ccba_legal.converters.vbpl_admin import (
        process_vbpl_bundle,
        process_vbpl_bundle_okf_v22,
        process_vbpl_bundle_okf_v24,
    )

    assert CURRENT_OKF_VERSION == "2.4"
    assert "v2.4" in CURRENT_OKF_SPEC
    assert callable(process_vbpl_bundle)
    assert process_vbpl_bundle_okf_v24 is process_vbpl_bundle
    assert process_vbpl_bundle_okf_v22 is process_vbpl_bundle
