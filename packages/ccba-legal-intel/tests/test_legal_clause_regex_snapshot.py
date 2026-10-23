"""Unit tests for robust legal clause regex parsing & snapshot regression suite (COND-15 / CCILF)."""

from ccba_legal.gold_standard import get_doc_profile, inject_semantic_anchors


def test_khoan_pattern_multi_dialect_snapshot() -> None:
    """Verifies that khoan_pattern correctly matches all real-world markdown variants across VBPL corpus."""
    profile = get_doc_profile("vbpl")
    pattern = profile.khoan_pattern

    test_cases = [
        # (input_line, expected_num, expected_rest_prefix)
        ("1. Lập hồ sơ thiết kế xây dựng.", "1", "Lập hồ sơ"),
        ("**1.** Quyền và nghĩa vụ của chủ đầu tư.", "1", "Quyền và nghĩa vụ"),
        ("  2. Thực hiện thẩm tra thiết kế.", "2", "Thực hiện thẩm tra"),
        ("**10.** Chi phí quản lý dự án.", "10", "Chi phí quản lý"),
        ("1.* Bên mời thầu* là cơ quan, tổ chức có thẩm quyền.", "1", "Bên mời thầu*"),
        ("2.* Chủ đầu tư* là cơ quan, tổ chức sở hữu vốn.", "2", "Chủ đầu tư*"),
        ("1.* Kiến trúc *là nghệ thuật và khoa học, kỹ thuật.", "1", "Kiến trúc *là"),
        ("19*.* *Kiểm tra công tác nghiệm thu về PCCC* là việc...", "19", "*Kiểm tra công tác"),
        ("22.* Quy định chuyển tiếp áp dụng cho...", "22", "Quy định chuyển tiếp"),
        ("_1._ Gạch dưới số khoản hợp lệ.", "1", "Gạch dưới số khoản"),
        ("**30.** Khoản ba mươi của Luật Xây dựng.", "30", "Khoản ba mươi"),
    ]

    for line, exp_num, exp_prefix in test_cases:
        match = pattern.match(line.strip())
        assert match is not None, f"Failed to match valid clause line: '{line}'"
        assert match.group(1) == exp_num, (
            f"Expected clause num '{exp_num}', got '{match.group(1)}' for '{line}'"
        )
        assert match.group(2).startswith(exp_prefix), (
            f"Expected rest to start with '{exp_prefix}', got '{match.group(2)}' for '{line}'"
        )


def test_khoan_pattern_negative_safeguards() -> None:
    """Ensures that normal text, sub-items, bullet lists, and section titles are NOT falsely matched."""
    profile = get_doc_profile("vbpl")
    pattern = profile.khoan_pattern

    negative_cases = [
        "a) Điều kiện năng lực hoạt động xây dựng.",
        "b) Chứng chỉ hành nghề của cá nhân.",
        "- Danh mục các hồ sơ giao nộp kèm theo.",
        "* Ghi chú bổ sung về tiêu chuẩn áp dụng.",
        "### Điều 12. Quản lý chất lượng",
        "Năm 2026 là năm có nhiều cải cách thể chế.",
        "QCVN 06:2022/BXD Quy chuẩn kỹ thuật quốc gia về an toàn cháy.",
    ]

    for line in negative_cases:
        match = pattern.match(line.strip())
        assert match is None, f"Falsely matched negative line: '{line}'"


def test_inject_semantic_anchors_recovers_missing_clauses() -> None:
    """End-to-end test verifying that anchor injection produces deterministic HTML anchors for all dialects."""
    raw_text = (
        "Điều 4. Giải thích từ ngữ\n"
        "1.* Bên mời thầu* là cơ quan, tổ chức có chuyên môn.\n"
        "2.* Chủ đầu tư* là cơ quan, tổ chức sở hữu vốn.\n"
        "19*.* *Kiểm tra công tác nghiệm thu về PCCC* là hoạt động kiểm tra.\n"
        "20. Quy định khác của pháp luật."
    )
    profile = get_doc_profile("vbpl")
    anchored = inject_semantic_anchors(raw_text, profile=profile)

    assert '<a id="dieu-4"></a>' in anchored
    assert '<a id="dieu-4-khoan-1"></a>' in anchored
    assert '<a id="dieu-4-khoan-2"></a>' in anchored
    assert '<a id="dieu-4-khoan-19"></a>' in anchored
    assert '<a id="dieu-4-khoan-20"></a>' in anchored
    assert "**1.** Bên mời thầu* là cơ quan, tổ chức có chuyên môn." in anchored
    assert "**2.** Chủ đầu tư* là cơ quan, tổ chức sở hữu vốn." in anchored
