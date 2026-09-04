"""Comprehensive unit tests for CCBA Dual-Track Questionnaire Engine v2.0.

Tests parsing (v1.0 & v2.0), DOCX generation, HTML Form generation (with XSS/CSP guards),
micro-chat, email tables, and the two-way reply engine.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import tempfile
from pathlib import Path

import pytest

from ccba_ooxml.questionnaire import (
    QuestionnaireEngine,
    QuestionType,
    apply_questionnaire_reply,
    parse_questionnaire_markdown,
    parse_reply_string,
    render_chat_snippet,
    render_email_table,
    render_questionnaire_docx,
    render_questionnaire_html,
)

SAMPLE_V2_MD = """---
title: "BẢNG HỎI THỐNG NHẤT GIẢI PHÁP PCCC & TRẠM BƠM"
track: "delivery"
status: "PENDING"
doc_code: "CCBA-QST-PCCC-01"
---
# BẢNG HỎI THỐNG NHẤT GIẢI PHÁP PCCC & TRẠM BƠM

**Mục đích:** Thống nhất giải pháp bố trí trạm bơm và bể nước PCCC tầng hầm.
**Người gửi:** CCBA BIM/MEP — **Người nhận:** Công ty CP Phát triển Đô thị Sài Gòn
**Dự án:** Khu Phức Hợp Cao Cấp Thảo Điền — **Thời hạn:** 2026-09-10

## Ngữ cảnh (Context)
Dự án đang trong giai đoạn phối hợp thiết kế kỹ thuật V2. Cần chốt vị trí trạm bơm để tránh xung đột với đường ống cấp thoát nước chính.

## Hướng dẫn Trả lời (How to answer)
Vui lòng chọn 1 phương án cho mỗi câu hỏi bên dưới hoặc nhập ý kiến điều chỉnh.

## Vấn đề 1: Trạm bơm & Bể nước PCCC
### Câu hỏi 1: Lựa chọn vị trí bố trí cụm bơm chữa cháy
> **Tại sao cần quyết định:** Quyết định trực tiếp đến diện tích đỗ xe hầm B2 và tuân thủ khoảng cách an toàn theo QCVN 06:2022/BXD.

- [ ] **Phương án A (⭐ Khuyến nghị)**: Đặt tại khoang kỹ thuật trục 4-6 hầm B2
  * Trade-off: Giảm chiều dài ống hút 15m, chi phí tối ưu; chiếm 2 vị trí đỗ xe.
- [ ] **Phương án B**: Tách rời bể nước ngầm ngoài ranh tầng hầm
  * Trade-off: Giữ nguyên 100% diện tích đỗ xe; chi phí đào đất và chống thấm tăng 12%.
- [ ] **Phương án C**: Bố trí tại tầng kỹ thuật lửng
  * Trade-off: Cần gia cố kết cấu chịu tải trọng động; thời gian thi công kéo dài 1 tuần.
- [ ] **Phương án D**: Phương án khác của Tư vấn thiết kế
  * Trade-off: Do TVTK đề xuất và bảo vệ giải pháp.

### Câu hỏi 2: Cấp điện ưu tiên cho trạm bơm PCCC
*Tại sao điều này quan trọng: Đảm bảo độ tin cậy cấp điện loại 1 khi xảy ra sự cố cháy.*

- [ ] **Phương án A (⭐ Khuyến nghị)**: Cấp từ 2 nguồn điện lưới độc lập + Máy phát dự phòng
  * Trade-off: Độ tin cậy cao nhất, tuân thủ nghiêm ngặt quy chuẩn PCCC.
- [ ] **Phương án B**: 1 nguồn điện lưới + Máy phát điện diesel tự động khởi động
  * Trade-off: Tiết kiệm chi phí trạm biến áp thứ hai; thời gian chuyển mạch 15s.

## Ý kiến khác (Anything else?)
Quý đối tác vui lòng ghi chú thêm nếu có yêu cầu đặc thù về hãng sản xuất bơm.
"""

SAMPLE_V1_MD = """# BẢNG HỎI LÀM RÕ THÔNG TIN KẾT CẤU

**Mục đích:** Xác định tải trọng sàn tầng thượng.
**Người gửi:** Kỹ sư kết cấu — **Người nhận:** Kiến trúc sư trưởng

## Ngữ cảnh (Context)
Cần thông tin trước khi tính toán dầm chuyển.

### Câu hỏi 1: Tải trọng hoàn thiện sân vườn mái là bao nhiêu?
*Tại sao điều này quan trọng: Ảnh hưởng đến chiều dày sàn và cốt thép.*

> [Nhập câu trả lời tại đây]

### Câu hỏi 2: Có lắp đặt hồ bơi vô cực trên tầng thượng không?
*Tại sao điều này quan trọng: Tải trọng nước lớn cần bố trí cột tăng cường.*

> [Nhập câu trả lời tại đây]
"""


def test_parse_v2_hypothesis_matrix():
    """Verify v2.0 markdown parsing with hypotheses matrix options and trade-offs."""
    data = parse_questionnaire_markdown(SAMPLE_V2_MD)
    meta = data.metadata

    assert "PCCC" in meta.title
    assert meta.doc_code == "CCBA-QST-PCCC-01"
    assert meta.status == "PENDING"
    assert meta.track == "delivery"
    assert "Thảo Điền" in meta.project_name
    assert "Sài Gòn" in meta.recipient

    assert len(data.questions) == 2

    # Question 1 checks
    q1 = data.questions[0]
    assert q1.id == 1
    assert "vị trí" in q1.title
    assert "QCVN 06:2022/BXD" in q1.why_it_matters
    assert q1.q_type == QuestionType.HYPOTHESIS_MATRIX
    assert len(q1.options) == 4

    opt_a = q1.options[0]
    assert opt_a.key == "A"
    assert opt_a.is_recommended is True
    assert "khoang kỹ thuật" in opt_a.label
    assert "Giảm chiều dài ống" in opt_a.trade_off

    # Question 2 checks
    q2 = data.questions[1]
    assert q2.id == 2
    assert len(q2.options) == 2
    assert q2.options[0].key == "A"
    assert q2.options[1].key == "B"


def test_parse_v1_legacy_open_ended():
    """Verify backward compatibility: v1.0 without options is parsed as OPEN_ENDED."""
    data = parse_questionnaire_markdown(SAMPLE_V1_MD)
    assert len(data.questions) == 2

    for q in data.questions:
        assert q.q_type == QuestionType.OPEN_ENDED
        assert len(q.options) == 0


def test_docx_rendering_and_validation():
    """Verify DOCX rendering produces a valid OOXML document."""
    data = parse_questionnaire_markdown(SAMPLE_V2_MD)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_docx = Path(tmp_dir) / "test_output.docx"
        render_questionnaire_docx(data, out_docx)

        assert out_docx.exists()
        assert out_docx.stat().st_size > 5000

        # Validate that document opens cleanly in python-docx
        import docx
        doc = docx.Document(str(out_docx))
        assert len(doc.tables) >= 2
        assert len(doc.paragraphs) >= 3

        # Validate OOXML package integrity
        from ccba_ooxml.pack import validate_document
        assert validate_document(out_docx) is True


def test_html_rendering_security_and_offline():
    """Verify HTML rendering escapes malicious input and includes CSP."""
    # Test data with potential XSS payloads
    xss_md = SAMPLE_V2_MD.replace(
        "Khu Phức Hợp Cao Cấp Thảo Điền",
        "Thảo Điền <script>alert('XSS')</script> & 'Attack'",
    )
    data = parse_questionnaire_markdown(xss_md)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_html = Path(tmp_dir) / "test_output.html"
        render_questionnaire_html(data, out_html)

        content = out_html.read_text(encoding="utf-8")

        # Security checks: no unescaped script tags
        assert "<script>alert('XSS')</script>" not in content
        assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in content

        # CSP check
        assert "Content-Security-Policy" in content
        assert "default-src 'none'" in content

        # Interactivity checks
        assert "localStorage" in content
        assert "responseSyntax" in content
        assert "copyResponse()" in content


def test_chat_snippet_rendering():
    """Verify chat snippet is concise (<15 lines) and includes syntax hint."""
    data = parse_questionnaire_markdown(SAMPLE_V2_MD)
    snippet = render_chat_snippet(data)
    lines = snippet.strip().splitlines()

    assert len(lines) <= 15
    assert "1A, 2B, 3C" in snippet
    assert "PCCC" in snippet


def test_email_table_rendering():
    """Verify email HTML table contains styled inline elements."""
    data = parse_questionnaire_markdown(SAMPLE_V2_MD)
    email_html = render_email_table(data)

    assert "<table" in email_html
    assert "003366" in email_html  # CCBA Brand Navy Blue
    assert "Hypotheses Matrix" in email_html
    assert "1A, 2B, 3C" in email_html


def test_parse_reply_string():
    """Verify flexible parsing of reply syntax variants."""
    assert parse_reply_string("1A, 2B, 3C") == {1: ("A", ""), 2: ("B", ""), 3: ("C", "")}
    assert parse_reply_string("1:A, 2:C") == {1: ("A", ""), 2: ("C", "")}
    assert parse_reply_string("1-a; 2-b") == {1: ("A", ""), 2: ("B", "")}
    assert parse_reply_string("1=A, 2=D (Dùng trạm nổi)") == {
        1: ("A", ""),
        2: ("D", "Dùng trạm nổi"),
    }
    assert parse_reply_string("Câu 1: A, Câu 2: B") == {1: ("A", ""), 2: ("B", "")}


def test_apply_reply_idempotency_and_decision_log():
    """Verify applying reply updates markdown AST idempotently and appends Decision Log."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "questionnaire.md"
        test_file.write_text(SAMPLE_V2_MD, encoding="utf-8")

        # First reply
        apply_questionnaire_reply(
            test_file,
            reply_str="1A, 2B",
            resolved_by="Ban QLDA Masterise",
        )
        content_1 = test_file.read_text(encoding="utf-8")

        assert "status: \"RESOLVED\"" in content_1 or "RESOLVED" in content_1
        assert "- [x] **Phương án A (⭐ Khuyến nghị)**: Đặt tại khoang kỹ thuật" in content_1
        assert "- [ ] **Phương án B**: Tách rời bể nước ngầm" in content_1
        assert "- [x] **Phương án B**: 1 nguồn điện lưới" in content_1
        assert "## Nhật ký Quyết định (Decision Log)" in content_1
        assert "Ban QLDA Masterise" in content_1

        # Second reply (changing choice for Question 1 to B -> idempotency check)
        apply_questionnaire_reply(
            test_file,
            reply_str="1B, 2A",
            resolved_by="Chủ đầu tư",
        )
        content_2 = test_file.read_text(encoding="utf-8")

        # Must uncheck A and check B for question 1
        assert "- [ ] **Phương án A (⭐ Khuyến nghị)**: Đặt tại khoang kỹ thuật" in content_2
        assert "- [x] **Phương án B**: Tách rời bể nước ngầm" in content_2
        assert "- [x] **Phương án A (⭐ Khuyến nghị)**: Cấp từ 2 nguồn điện lưới" in content_2
        assert "Chủ đầu tư" in content_2


def test_apply_reply_boundary_validations():
    """Verify reply engine rejects invalid question IDs and out-of-bounds options."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "questionnaire.md"
        test_file.write_text(SAMPLE_V2_MD, encoding="utf-8")

        # Question 99 does not exist
        with pytest.raises(ValueError, match="Question 99 does not exist"):
            apply_questionnaire_reply(test_file, "99A")

        # Question 2 only has options A and B (E is invalid)
        with pytest.raises(ValueError, match="Option 'E' is invalid for Question 2"):
            apply_questionnaire_reply(test_file, "2E")


def test_questionnaire_engine_facade_export_all():
    """Verify QuestionnaireEngine.export_all exports all 4 file formats."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "pccc_qst.md"
        test_file.write_text(SAMPLE_V2_MD, encoding="utf-8")

        results = QuestionnaireEngine.export_all(test_file, output_dir=tmp_dir)

        assert "docx" in results and results["docx"].exists()
        assert "html" in results and results["html"].exists()
        assert "chat" in results and results["chat"].exists()
        assert "email" in results and results["email"].exists()
