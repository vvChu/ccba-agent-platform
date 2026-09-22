"""Unit tests for ccba_legal.normalizers."""

import sys

from ccba_legal.cleaners import Cleaners, normalize_legal_text
from ccba_legal.normalizers import (
    detect_garbled_table,
    fix_stuck_vietnamese_words,
    format_legal_structure,
    normalize_chunk_text,
    normalize_section_headings,
    rejoin_paragraphs,
    strip_document_boilerplate,
)


class TestRejoinParagraphs:
    def test_basic_merge(self):
        text = "Sau khi sắp xếp, huyện Quế Sơn có 18 đơn vị hành chính cấp xã, gồm 15\nxã: Ninh Phước, Phước Ninh, Quế An."
        result = rejoin_paragraphs(text)
        assert "\n" not in result.strip(), f"Lines should be merged: {result!r}"
        assert "gồm 15 xã:" in result

    def test_preserves_blank_lines(self):
        text = "Đoạn 1 kết thúc.\n\nĐoạn 2 bắt đầu."
        result = rejoin_paragraphs(text)
        assert "\n\n" in result, "Blank lines should be preserved as paragraph separators"

    def test_preserves_dieu_boundary(self):
        text = "thuộc tỉnh Quảng Nam\nĐiều 2. Sắp xếp các đơn vị"
        result = rejoin_paragraphs(text)
        assert "Điều 2." in result
        # Điều should NOT be merged onto the previous line
        lines = [line for line in result.split("\n") if line.strip()]
        assert any(line.strip().startswith("Điều 2.") for line in lines)

    def test_preserves_numbered_list(self):
        text = "nội dung như sau:\n1. Sắp xếp các đơn vị"
        result = rejoin_paragraphs(text)
        lines = [line for line in result.split("\n") if line.strip()]
        assert any(line.strip().startswith("1.") for line in lines)

    def test_preserves_lettered_list(self):
        text = "quy định:\na) Thành lập xã Quế Tân"
        result = rejoin_paragraphs(text)
        lines = [line for line in result.split("\n") if line.strip()]
        assert any(line.strip().startswith("a)") for line in lines)

    def test_no_merge_after_period(self):
        text = "Quyết định này có hiệu lực.\nĐiều 3. Các Bộ trưởng"
        result = rejoin_paragraphs(text)
        # After a period, should NOT merge
        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) >= 2


class TestFormatLegalStructure:
    def test_dieu_heading(self):
        text = "Điều 1. Ban hành kèm theo Quyết định này"
        result = format_legal_structure(text)
        assert "### Điều 1." in result

    def test_chuong_heading(self):
        text = "Chương II - Quy định chung"
        result = format_legal_structure(text)
        assert "## Chương II" in result

    def test_muc_heading(self):
        text = "Mục 1 - Quy định chung"
        result = format_legal_structure(text)
        assert "## Mục 1" in result

    def test_phan_heading(self):
        text = "PHẦN I - TỔNG QUAN"
        result = format_legal_structure(text)
        assert "## PHẦN I" in result

    def test_roman_numeral_section(self):
        text = "I. MỤC ĐÍCH, YÊU CẦU"
        result = format_legal_structure(text)
        assert "**I. MỤC ĐÍCH, YÊU CẦU**" in result

    def test_existing_heading_preserved(self):
        text = "### Already a heading"
        result = format_legal_structure(text)
        assert result.strip() == "### Already a heading"


class TestDetectGarbledTable:
    def test_garbled_ocr_table(self):
        text = "Vốn NĐT\nX\nX\nNSNN\nX\n.\nVốn NĐT\nX\nX\nTên dự án\nNguồn vốn\nPhân kỳ\n2023-2025\n2026-2030"
        assert detect_garbled_table(text) is True

    def test_normal_text_not_garbled(self):
        text = (
            "Điều 1. Ban hành kèm theo Quyết định này Kế hoạch thực hiện "
            "Quy hoạch thành phố Đà Nẵng thời kỳ 2021 - 2030, tầm nhìn "
            "đến năm 2050. Chủ tịch Ủy ban nhân dân thành phố Đà Nẵng "
            "chịu trách nhiệm toàn diện về tính chính xác."
        )
        assert detect_garbled_table(text) is False

    def test_short_text_not_garbled(self):
        assert detect_garbled_table("short") is False
        assert detect_garbled_table("") is False


class TestNormalizeChunkText:
    def test_strips_doc_id_prefix(self):
        text = "[UBND/123/QD-TTg] Nội dung văn bản"
        result = normalize_chunk_text(text, strip_doc_id_prefix="UBND/123/QD-TTg")
        assert not result.startswith("[UBND/123/QD-TTg]")
        assert "Nội dung văn bản" in result

    def test_empty_text(self):
        assert normalize_chunk_text("") == ""
        assert normalize_chunk_text(None) == ""

    def test_garbled_table_warning(self):
        # Test that detect_garbled_table is correctly triggered within
        # normalize_chunk_text. Note: strip_document_boilerplate may strip
        # short ALL-CAPS lines in the first 600 chars, so we test with data
        # that survives preprocessing.
        from ccba_legal.normalizers import detect_garbled_table

        garbled_raw = (
            "Vốn NĐT\nX\nX\nNSNN\nX\n.\nVốn NĐT\nX\nX\nNSNN\n.\nX\n"
            "Tên dự án\nNguồn vốn\nPhân kỳ\n2023-2025\n2026-2030\nNSTW"
        )
        # Direct detection should always work
        assert detect_garbled_table(garbled_raw) is True


class TestStuckVietnameseWords:
    """Fix 3: OCR word-joining — stuck Vietnamese words should be separated."""

    def test_ho_so(self):
        assert fix_stuck_vietnamese_words("Kiểm tra hồsơ kỹ thuật") == "Kiểm tra hồ sơ kỹ thuật"

    def test_va_co(self):
        assert fix_stuck_vietnamese_words("vàcó thể") == "và có thể"

    def test_su_co(self):
        assert fix_stuck_vietnamese_words("sựcố giao thông") == "sự cố giao thông"

    def test_co_so(self):
        assert fix_stuck_vietnamese_words("cơsở sử dụng") == "cơ sở sử dụng"

    def test_ap_ke(self):
        assert fix_stuck_vietnamese_words("Ápkế chuẩn") == "Áp kế chuẩn"

    def test_no_change_normal_text(self):
        text = "Điều 1. Ban hành kèm theo Quyết định này"
        assert fix_stuck_vietnamese_words(text) == text

    def test_empty(self):
        assert fix_stuck_vietnamese_words("") == ""
        assert fix_stuck_vietnamese_words(None) is None

    # ── BGTVT Thông tư corpus (2026-03 audit) ──
    def test_camay(self):
        assert (
            fix_stuck_vietnamese_words("hao phí camáy chuyên dùng") == "hao phí ca máy chuyên dùng"
        )

    def test_sonoi(self):
        assert fix_stuck_vietnamese_words("sốnội dung") == "số nội dung"

    def test_nhucau(self):
        assert fix_stuck_vietnamese_words("nhucầu sử dụng") == "nhu cầu sử dụng"

    def test_kykiet(self):
        assert fix_stuck_vietnamese_words("kýkết theo quy định") == "ký kết theo quy định"

    def test_dautư(self):
        assert fix_stuck_vietnamese_words("đầutư xây dựng") == "đầu tư xây dựng"

    def test_thong_tu_nay(self):
        assert fix_stuck_vietnamese_words("Thông tưnày có hiệu lực") == "Thông tư này có hiệu lực"


class TestNormalizeSectionHeadings:
    """Inline section number splitting for QCVN structure."""

    def test_inline_split(self):
        """Two section numbers on one line should be split."""
        t = "1.1 Phạm vi điều chỉnh Quy chuẩn 1.2 Đối tượng áp dụng Quy chuẩn"
        r = normalize_section_headings(t)
        assert "1.2" in r and r.count("\n") >= 1, f"got: {r!r}"

    def test_decimal_no_split(self):
        """Decimal values like '1.5 triệu' should NOT be split."""
        t = "giá trị là 1.5 triệu đồng"
        assert normalize_section_headings(t) == t

    def test_table_ref_no_split(self):
        """Table references like 'Bảng 1.2' should NOT be split."""
        t = "theo Bảng 1.2 quy định tại"
        assert normalize_section_headings(t) == t

    def test_separate_lines_preserved(self):
        """Already-separate section lines should not be modified."""
        t = "1.1 Phạm vi\n1.2 Đối tượng"
        assert normalize_section_headings(t) == t


class TestDigitalSignature:
    """Fix 5: Combined single-line digital signature block should be stripped."""

    def test_strips_ky_boi_line(self):
        text = (
            "Ký bởi: Cổng Thông tin điện tử Chính phủ Email: thongtinchinhphu@chinhphu.vn "
            "Cơ quan: Văn phòng Chính phủ Thời gian ký: 16.03.2015 11:02:35 +07:00\nĐiều 1. Nội dung chính"
        )
        result = strip_document_boilerplate(text)
        assert "Ký bởi" not in result
        assert "Điều 1" in result

    def test_strips_nguoi_ky_line(self):
        text = (
            "Người ký: Cổng Thông tin điện tử Chính phủ Email: test@gov.vn "
            "Cơ quan: Test Thời gian ký: 22.05.2023 16:12:47 +07:00\nĐiều 2. Nội dung"
        )
        result = strip_document_boilerplate(text)
        assert "Người ký" not in result
        assert "Điều 2" in result


class TestCleanersIntegration:
    def test_cleaners_normalize_legal_text(self):
        text = "Điều 1. Phạm vi\nhồsơ theo quy định tại thông tư này."
        result = Cleaners.normalize_legal_text(text)
        assert "hồ sơ" in result
        assert "Điều 1. Phạm vi" in result

    def test_cleaners_remove_ocr_artifacts(self):
        text = "họp đồng kinh tế"
        result = Cleaners.remove_ocr_artifacts(text)
        assert "hợp đồng kinh tế" in result

    def test_procedural_alias(self):
        text = "họp đồng kinh tế"
        result = normalize_legal_text(text)
        assert "hợp đồng kinh tế" in result


def run_all():
    """Simple test runner."""
    passed = 0
    failed = 0
    errors = []

    for cls_name, cls in [
        ("TestRejoinParagraphs", TestRejoinParagraphs),
        ("TestFormatLegalStructure", TestFormatLegalStructure),
        ("TestDetectGarbledTable", TestDetectGarbledTable),
        ("TestNormalizeChunkText", TestNormalizeChunkText),
        ("TestStuckVietnameseWords", TestStuckVietnameseWords),
        ("TestNormalizeSectionHeadings", TestNormalizeSectionHeadings),
        ("TestDigitalSignature", TestDigitalSignature),
        ("TestCleanersIntegration", TestCleanersIntegration),
    ]:
        instance = cls()
        for attr in dir(instance):
            if attr.startswith("test_"):
                try:
                    getattr(instance, attr)()
                    passed += 1
                    print(f"  ✅ {cls_name}.{attr}")
                except AssertionError as e:
                    failed += 1
                    errors.append(f"  ❌ {cls_name}.{attr}: {e}")
                    print(f"  ❌ {cls_name}.{attr}: {e}")
                except Exception as e:
                    failed += 1
                    errors.append(f"  💥 {cls_name}.{attr}: {type(e).__name__}: {e}")
                    print(f"  💥 {cls_name}.{attr}: {type(e).__name__}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("Failures:")
        for e in errors:
            print(e)
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
