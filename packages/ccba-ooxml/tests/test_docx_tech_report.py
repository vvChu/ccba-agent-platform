"""Unit and XML DOM tests for CCBA Brand v3.4 Technical Evaluation Report DOCX builder."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from docx import Document
from lxml import etree
from PIL import Image as PILImage

from ccba_ooxml import (
    CCBADocxTheme,
    TechnicalReportBuilder,
    build_tech_report_from_yaml,
    validate_document,
)
from ccba_ooxml.cli import main as ooxml_cli_main
from ccba_ooxml.docx._report_theme import (
    CONTENT_WIDTH_DXA,
    HEADER_COL_WIDTHS_DXA,
    SIGNOFF_2COL_WIDTHS_DXA,
    SIGNOFF_3COL_WIDTHS_DXA,
    normalize_col_widths,
    normalize_hex,
    sanitize_xml_text,
    wcag_safe_text_hex,
)
from ccba_ooxml.docx._tech_report import load_report_spec
from ccba_ooxml.form_filler.exceptions import EngineUnavailableError

pytestmark = [pytest.mark.fast, pytest.mark.unit]

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"


def _sample_report_spec(*, num_sections: int = 3, signoff_cols: int = 2) -> dict[str, Any]:
    """Return an anonymized technical evaluation report YAML IR specification."""
    signers = [
        {
            "title_vi": "NGƯỜI LẬP BÁO CÁO",
            "title_en": "PREPARED BY",
            "name": "Nguyen Van A",
            "role_vi": "Kỹ sư Đánh giá",
            "role_en": "Engineer",
        },
        {
            "title_vi": "PHÊ DUYỆT",
            "title_en": "APPROVED BY",
            "name": "Tran Van B",
            "role_vi": "Giám đốc",
            "role_en": "Director",
        },
    ]
    if signoff_cols == 3:
        signers.insert(
            1,
            {
                "title_vi": "KIỂM TRA KỸ THUẬT",
                "title_en": "CHECKED BY",
                "name": "Le Thi C",
                "role_vi": "Chủ trì Bộ môn",
                "role_en": "Lead Engineer",
            },
        )
    all_sections = [
        {
            "code": "I",
            "title_vi": "TÓM TẮT BÁO CÁO",
            "title_en": "EXECUTIVE SUMMARY",
            "paragraphs": [
                "Báo cáo đánh giá tổng thể hệ thống kỹ thuật mẫu theo tiêu chuẩn thiết kế.",
            ],
            "callouts": [
                {
                    "tone": "recommendation",
                    "title": "Đề xuất của Tư vấn",
                    "body": "Áp dụng giải pháp chuẩn hóa mô hình và kiểm định trước thi công.",
                }
            ],
        },
        {
            "code": "II",
            "title_vi": "KẾT QUẢ ĐÁNH GIÁ CHI TIẾT",
            "title_en": "DETAILED EVALUATION RESULTS",
            "bullets": [
                {"label": "Phạm vi kiểm tra", "text": "Hệ thống cấp thoát nước và thông gió mẫu."},
                "Đối chiếu bảng tính thủy lực và bố trí mặt bằng kỹ thuật.",
            ],
            "tables": [
                {
                    "caption": "Bảng 1. Tổng hợp tiêu chí đánh giá kỹ thuật",
                    "header_rows": [
                        ["TT", "Hạng mục đánh giá", "Kết quả", "Ghi chú"],
                        ["No.", "Evaluation Item", "Status", "Remarks"],
                    ],
                    "rows": [
                        ["1", "Lưu lượng thiết kế", "Đạt", "Phù hợp định mức"],
                        ["2", "Áp suất vận hành", "Cần lưu ý", "Kiểm tra van giảm áp"],
                    ],
                    "col_widths": [10, 45, 20, 25],
                    "alignments": ["center", "left", "center", "left"],
                }
            ],
            "subsections": [
                {
                    "code": "2.1",
                    "title_vi": "Phân tích sai lệch thông số",
                    "title_en": "Parameter Deviation Analysis",
                    "paragraphs": ["Không phát hiện sai lệch vượt ngưỡng cho phép."],
                }
            ],
        },
        {
            "code": "III",
            "title_vi": "KẾT LUẬN VÀ KIẾN NGHỊ",
            "title_en": "CONCLUSIONS & RECOMMENDATIONS",
            "paragraphs": [
                "Hồ sơ đủ điều kiện chuyển bước thiết kế tiếp theo sau khi cập nhật ghi chú."
            ],
            "callouts": [
                {
                    "tone": "warn",
                    "title": "Lưu ý triển khai",
                    "body": "Hoàn thiện hồ sơ hoàn công theo biểu mẫu kiểm soát.",
                }
            ],
        },
        {
            "code": "IV",
            "title_vi": "PHỤ LỤC ĐỐI SOÁT",
            "title_en": "VERIFICATION APPENDIX",
            "bullets": ["Danh mục bản vẽ đối soát Rev. 01."],
        },
    ]
    return {
        "document": {
            "doc_no": "CCBA-RPT-SAMPLE-01",
            "revision": "Rev. 01",
            "date": "22/11/2026",
            "title_vi": "BÁO CÁO ĐÁNH GIÁ KỸ THUẬT HỆ THỐNG MẪU",
            "title_en": "SAMPLE TECHNICAL EVALUATION REPORT",
            "short_title": "CCBA-PROJ-MEP-RPT-001 Technical Evaluation",
            "project_vi": "Dự án Hạ tầng Kỹ thuật Mẫu (CCBA-PROJ-MEP-RPT-001)",
            "project_en": "Sample Technical Infrastructure Project",
            "client_vi": "Chủ đầu tư Mẫu",
            "client_en": "Sample Client Corp.",
            "location_vi": "Khu công nghiệp Mẫu",
            "location_en": "Sample Industrial Park",
            "discipline_vi": "Cơ điện & Thủy lực",
            "discipline_en": "MEP & Hydraulics",
            "consultant": "IBST - CCBA",
            "contact_email": "contact@example.com",
        },
        "organization": {
            "parent_vi": "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG",
            "parent_en": "Institute for Building Science and Technology",
            "unit_vi": "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG",
            "unit_en": "Center for Consulting Services and BIM Application in Construction (CCBA)",
        },
        "kpis": [
            {
                "label_vi": "TỔNG HẠNG MỤC",
                "label_en": "TOTAL ITEMS",
                "value": "24",
                "accent": "#363883",
            },
            {
                "label_vi": "TỶ LỆ ĐẠT",
                "label_en": "PASS RATE",
                "value": "95.8%",
                "accent": "#0093DD",
            },
            {"label_vi": "CẢNH BÁO", "label_en": "ALERTS", "value": "1", "accent": "#DA251C"},
        ],
        "sections": all_sections[:num_sections],
        "signoff": signers,
    }


def test_theme_helpers_and_spec_validation(tmp_path: Path) -> None:
    """Verify hex idempotence, WCAG contrast mapping, DXA normalization, and YAML validation."""
    assert normalize_hex("#0093dd") == "0093DD"
    assert normalize_hex(normalize_hex("363883")) == "363883"
    assert normalize_hex("") == "363883"
    with pytest.raises(ValueError, match="Invalid 6-digit hex"):
        normalize_hex("ZZZZZZ")

    theme = CCBADocxTheme()
    assert wcag_safe_text_hex("#0093DD", theme) == "005A9C"
    assert wcag_safe_text_hex("#363883", theme) == "363883"

    assert normalize_col_widths(2) == list(SIGNOFF_2COL_WIDTHS_DXA)
    assert normalize_col_widths(3) == list(SIGNOFF_3COL_WIDTHS_DXA)
    scaled = normalize_col_widths(4, [10, 45, 20, 25])
    assert sum(scaled) == CONTENT_WIDTH_DXA
    assert all(w > 0 for w in scaled)
    with pytest.raises(ValueError):
        normalize_col_widths(2, [100])
    with pytest.raises(ValueError):
        normalize_col_widths(2, [100, 0])

    assert sanitize_xml_text("OK\x00\x0bTEXT") == "OKTEXT"

    with pytest.raises(FileNotFoundError):
        load_report_spec(tmp_path / "absent.yaml")
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("document: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required report spec keys"):
        load_report_spec(bad_yaml)


def test_technical_report_openxml_invariants_and_chrome(tmp_path: Path) -> None:
    """Verify A4 geometry, 4-slot Segoe UI, fixed tblGrid, cantSplit, tblHeader, cover, and fields."""
    spec = _sample_report_spec(num_sections=3, signoff_cols=2)
    # Inject forbidden ministry/tautology lines to prove RULE-6.1 sanitization
    spec["organization"]["parent_vi"] = "BỘ XÂY DỰNG — VIỆN KHCN (IBST)"
    spec["organization"]["unit_vi"] = "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG (CCBA)"

    out_docx = tmp_path / "tech_report.docx"
    saved = TechnicalReportBuilder().build(spec, out_docx)
    assert saved.is_file()
    assert validate_document(saved) is True

    doc = Document(str(saved))
    sec = doc.sections[0]
    assert sec.page_width.twips == 11906
    assert sec.page_height.twips == 16838
    assert sec.left_margin.twips == 1701
    assert sec.right_margin.twips == 1134
    assert sec.top_margin.twips == 1134
    assert sec.bottom_margin.twips == 1134
    assert sec.different_first_page_header_footer is True

    # Normal style w:rFonts must specify Segoe UI across all 4 slots
    normal_rfonts = doc.styles["Normal"].element.find(f".//{_W}rFonts")
    assert normal_rfonts is not None
    for slot in ("ascii", "hAnsi", "eastAsia", "cs"):
        assert normal_rfonts.get(f"{_W}{slot}") == "Segoe UI"

    # Cover Page RULE-6.1 org block & Document Control Matrix checks
    cover_text = "\n".join(p.text for c in doc.tables[0].rows[0].cells for p in c.paragraphs)
    assert "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG" in cover_text
    assert "BỘ XÂY DỰNG" not in cover_text
    assert "(IBST)" not in cover_text
    assert "(CCBA)" not in doc.tables[0].rows[0].cells[0].paragraphs[2].text

    matrix_text = "\n".join(c.text for row in doc.tables[1].rows for c in row.cells)
    assert "contact@example.com" in matrix_text
    assert "IBST - CCBA" in matrix_text

    # Every body table must have tblLayout=fixed, gridCol sum == 9071, and cantSplit on all rows
    for tbl in doc.tables:
        tbl_xml = tbl._tbl
        layout = tbl_xml.find(f"{_W}tblPr/{_W}tblLayout")
        assert layout is not None and layout.get(f"{_W}val") == "fixed"
        grid_cols = [int(gc.get(f"{_W}w")) for gc in tbl_xml.findall(f"{_W}tblGrid/{_W}gridCol")]
        assert sum(grid_cols) == CONTENT_WIDTH_DXA
        for tr in tbl_xml.findall(f"{_W}tr"):
            assert tr.find(f"{_W}trPr/{_W}cantSplit") is not None

    # Data table (with 2 header_rows) must carry <w:tblHeader/> on both header rows
    data_tbl = next(
        t for t in doc.tables if any("Hạng mục đánh giá" in c.text for r in t.rows for c in r.cells)
    )
    for hdr_idx in (0, 1):
        assert data_tbl.rows[hdr_idx]._tr.find(f"{_W}trPr/{_W}tblHeader") is not None

    # KPI card WCAG check: #0093DD border maps metric text color to #005A9C
    kpi_tbl = doc.tables[2]
    card_cyan = kpi_tbl.rows[0].cells[1]
    top_bdr = card_cyan._tc.find(f"{_W}tcPr/{_W}tcBorders/{_W}top")
    assert top_bdr is not None and top_bdr.get(f"{_W}color") == "0093DD"
    val_color_el = card_cyan.paragraphs[-1]._p.find(f".//{_W}rPr/{_W}color")
    assert val_color_el is not None and val_color_el.get(f"{_W}val") == "005A9C"

    # Symmetric 2-col sign-off check: 4535 + 4536 = 9071 and zero email/org leakage in signature boxes
    signoff_tbl = doc.tables[-1]
    sign_cols = [
        int(gc.get(f"{_W}w")) for gc in signoff_tbl._tbl.findall(f"{_W}tblGrid/{_W}gridCol")
    ]
    assert sign_cols == [4535, 4536]
    sign_text = "\n".join(c.text for c in signoff_tbl.rows[0].cells)
    assert "contact@example.com" not in sign_text
    assert "VIỆN KHOA HỌC" not in sign_text
    assert "Giám đốc / Director" in sign_text

    # Running header [3571, 5500] and footer XML fields PAGE / NUMPAGES + logo embedded
    with zipfile.ZipFile(saved) as zf:
        hdr_root = etree.fromstring(zf.read("word/header1.xml"))
        ftr_root = etree.fromstring(zf.read("word/footer1.xml"))
        doc_xml_str = zf.read("word/document.xml").decode("utf-8")
        assert any(name.startswith("word/media/") for name in zf.namelist())
    assert [
        int(gc.get(f"{_W}w")) for gc in hdr_root.findall(f".//{_W}tblGrid/{_W}gridCol")
    ] == list(HEADER_COL_WIDTHS_DXA)
    instr_texts = " ".join(el.text or "" for el in ftr_root.findall(f".//{_W}instrText"))
    assert "PAGE" in instr_texts and "NUMPAGES" in instr_texts
    assert "contact@example.com" in "".join(ftr_root.itertext())
    assert "Smarter" in "".join(ftr_root.itertext())
    assert "<w:drawing>" in doc_xml_str


def test_section_agnostic_3col_signoff_and_custom_logo(tmp_path: Path) -> None:
    """Verify dynamic section counts, 3-column sign-off (3024+3023+3024), and custom logo ratio."""
    spec = _sample_report_spec(num_sections=4, signoff_cols=3)
    logo_path = tmp_path / "wide_logo.png"
    PILImage.new("RGB", (200, 100), color=(54, 56, 131)).save(logo_path)

    out_docx = tmp_path / "four_sec.docx"
    TechnicalReportBuilder(logo_path=logo_path).build(spec, out_docx)
    doc = Document(str(out_docx))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "IV. PHỤ LỤC ĐỐI SOÁT" in full_text
    sign_tbl = doc.tables[-1]
    assert [int(gc.get(f"{_W}w")) for gc in sign_tbl._tbl.findall(f"{_W}tblGrid/{_W}gridCol")] == [
        3024,
        3023,
        3024,
    ]
    assert len(doc.inline_shapes) == 1
    shape = doc.inline_shapes[0]
    assert round(shape.width / shape.height, 2) == 2.0


def test_build_tech_report_from_yaml_and_cli_with_pdf(tmp_path: Path) -> None:
    """Verify YAML entrypoint, CLI tech-report JSON output, and docx_to_pdf success/error paths."""
    cfg_path = tmp_path / "report_spec.yaml"
    cfg_path.write_text(
        yaml.safe_dump(_sample_report_spec(num_sections=2), allow_unicode=True), encoding="utf-8"
    )

    out_docx = tmp_path / "cli_report.docx"
    out_pdf = tmp_path / "cli_report.pdf"
    report_json = tmp_path / "summary.json"

    def _fake_pdf(_src: Path | str, dst: Path | str) -> Path:
        dst_path = Path(dst).resolve()
        dst_path.write_bytes(b"%PDF-1.5 mock")
        return dst_path

    argv = [
        "ccba-ooxml",
        "tech-report",
        str(cfg_path),
        "-o",
        str(out_docx),
        "--pdf",
        str(out_pdf),
        "--output",
        str(report_json),
    ]
    with (
        patch("ccba_ooxml.converter.docx_to_pdf", side_effect=_fake_pdf),
        patch.object(sys, "argv", argv),
    ):
        ooxml_cli_main()

    assert out_docx.is_file() and out_pdf.is_file()
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert payload["section_count"] == 2
    assert Path(payload["docx_path"]) == out_docx.resolve()
    assert Path(payload["pdf_path"]) == out_pdf.resolve()

    with patch(
        "ccba_ooxml.converter.docx_to_pdf", side_effect=EngineUnavailableError("no soffice")
    ):
        err_res = build_tech_report_from_yaml(
            cfg_path, tmp_path / "fail_pdf.docx", export_pdf=tmp_path / "x.pdf"
        )
    assert err_res["success"] is False
    assert "no soffice" in err_res["error"]
