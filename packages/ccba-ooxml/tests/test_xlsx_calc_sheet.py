"""Unit and XML DOM round-trip tests for CCBA bilingual engineering calculation sheets."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import openpyxl
import pytest
import yaml
from openpyxl.utils.units import pixels_to_EMU
from PIL import Image as PILImage

from ccba_ooxml import (
    CalculationSheetBuilder,
    CCBAExcelTheme,
    build_calc_sheet_from_yaml,
    resolve_formula,
)
from ccba_ooxml.cli import main as ooxml_cli_main
from ccba_ooxml.xlsx._calc_sheet import extract_item_no, load_calc_spec

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _sample_spec() -> dict[str, object]:
    """Return a generic anonymized engineering calculation specification."""
    return {
        "document": {
            "doc_no": "CCBA-CALC-SAMPLE-01",
            "revision": "Rev. 01",
            "date": "22/11/2026",
            "title_vi": "BẢNG TÍNH LƯU LƯỢNG THỦY LỰC MẪU",
            "title_en": "SAMPLE HYDRAULIC FLOW CALCULATION SHEET",
            "project_vi": "Dự án Hạ tầng Kỹ thuật Mẫu",
            "project_en": "Sample Technical Infrastructure Project",
            "client_vi": "Chủ đầu tư Mẫu",
            "client_en": "Sample Client Corp.",
            "pmc": "Đơn vị Quản lý Dự án Mẫu",
            "location_vi": "Khu công nghiệp Mẫu, Việt Nam",
            "location_en": "Sample Industrial Park, Vietnam",
            "consultant": "IBST - CCBA",
            "discipline_vi": "Cấp thoát nước",
            "discipline_en": "Hydraulics & MEP",
        },
        "organization": {
            "parent_vi": "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG",
            "parent_en": "Institute for Building Science and Technology",
            "unit_vi": "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG",
            "unit_en": "Center for Consulting Services and BIM Application in Construction (CCBA)",
        },
        "inputs": [
            {
                "id": "area",
                "item_no": "1.1",
                "desc_vi": "Diện tích khu vực phục vụ",
                "desc_en": "Served zone area",
                "symbol": "A",
                "value": 120.0,
                "unit_vi": "m²",
                "unit_en": "m²",
                "ref_vi": "Mặt bằng thiết kế",
                "ref_en": "Design Layout",
            },
            {
                "id": "rate",
                "item_no": "1.2",
                "desc_vi": "Cường độ thiết kế đơn vị",
                "desc_en": "Unit design flow rate",
                "symbol": "q",
                "value": 0.15,
                "unit_vi": "L/(s·m²)",
                "unit_en": "L/(s·m²)",
                "ref_vi": "TCVN 4513",
                "ref_en": "TCVN 4513",
            },
            {
                "id": "duration",
                "item_no": "1.3",
                "desc_vi": "Thời gian dự trữ",
                "desc_en": "Storage duration",
                "symbol": "t",
                "value": 1.0,
                "unit_vi": "giờ",
                "unit_en": "h",
                "ref_vi": "Tiêu chuẩn thiết kế",
                "ref_en": "Design Standard",
            },
        ],
        "sections": [
            {
                "code": "I",
                "title_vi": "LƯU LƯỢNG & THỂ TÍCH",
                "title_en": "FLOW RATE & STORAGE VOLUME",
                "rows": [
                    {
                        "id": "q_total",
                        "item_no": "1",
                        "desc_vi": "Tổng lưu lượng thiết kế",
                        "desc_en": "Total design flow rate",
                        "formula_display": "Q = A × q",
                        "formula": "=ROUND({area}*{rate}, 2)",
                        "unit_vi": "L/s",
                        "unit_en": "L/s",
                        "ref_vi": "Mục 4.1",
                        "ref_en": "Clause 4.1",
                        "style": "subtotal",
                    },
                    {
                        "id": "v_total",
                        "item_no": "2",
                        "desc_vi": "Thể tích bể dự trữ tối thiểu",
                        "desc_en": "Minimum storage volume",
                        "formula_display": "V = Q × 3.6 × t",
                        "formula": "=ROUND({q_total}*3.6*{duration}, 2)",
                        "unit_vi": "m³",
                        "unit_en": "m³",
                        "ref_vi": "Tổng hợp",
                        "ref_en": "Summary",
                        "style": "grand_total",
                    },
                ],
            }
        ],
        "summary_kpis": [
            {
                "label_vi": "LƯU LƯỢNG (Q)",
                "label_en": "DESIGN FLOW",
                "target_id": "q_total",
                "num_fmt": '#,##0.00" L/s"',
                "accent": "363883",
            },
            {
                "label_vi": "THỂ TÍCH (V)",
                "label_en": "STORAGE VOLUME",
                "target_id": "v_total",
                "num_fmt": '#,##0.00" m³"',
                "accent": "DA251C",
            },
            {
                "label_vi": "THỜI GIAN (t)",
                "label_en": "DURATION",
                "target_id": "duration",
                "num_fmt": '#,##0.00" h"',
                "accent": "0093DD",
            },
        ],
        "signoff": [
            {
                "title_vi": "NGƯỜI TÍNH TOÁN",
                "title_en": "PREPARED BY",
                "role_vi": "Kỹ sư",
                "role_en": "Engineer",
            },
            {
                "title_vi": "NGƯỜI KIỂM TRA",
                "title_en": "CHECKED BY",
                "role_vi": "Chủ trì",
                "role_en": "Lead",
            },
            {
                "title_vi": "PHÊ DUYỆT",
                "title_en": "APPROVED BY",
                "role_vi": "Giám đốc",
                "role_en": "Director",
            },
        ],
        "references": {
            "standards": [
                {
                    "code": "TCVN 4513",
                    "title_vi": "Cấp nước bên trong — Tiêu chuẩn thiết kế",
                    "title_en": "Internal water supply — Design standard",
                    "scope_vi": "Thủy lực",
                    "scope_en": "Hydraulics",
                    "clauses_vi": "Điều 4.1 — Tính toán lưu lượng",
                    "clauses_en": "Clause 4.1 — Flow calculation",
                }
            ],
            "glossary": [
                {
                    "symbol": "Q",
                    "meaning_vi": "Tổng lưu lượng thiết kế",
                    "unit": "L/s",
                    "meaning_en": "Total design flow rate",
                }
            ],
            "technical_notes": [
                {
                    "code": "GC-01",
                    "note_vi": "Giá trị đầu vào phục vụ kiểm tra mẫu.",
                    "note_en": "Input values represent a generic verification sample.",
                }
            ],
        },
    }


def test_resolve_formula_and_yaml_helpers(tmp_path: Path) -> None:
    """Verify resolve_formula, YAML 1.1 False-key handling, and spec schema checks."""
    assert resolve_formula("=ROUND({a}*{b}, 2)", {"a": "D14", "b": "D15"}) == "=ROUND(D14*D15, 2)"
    with pytest.raises(ValueError, match="Unknown formula reference key"):
        resolve_formula("={missing_id}", {"a": "D14"})

    assert extract_item_no({"item_no": "1.1"}) == "1.1"
    assert extract_item_no({"no": "2"}) == "2"
    assert extract_item_no({False: "1.3"}) == "1.3"

    with pytest.raises(FileNotFoundError):
        load_calc_spec(tmp_path / "missing.yaml")

    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("document: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required calculation spec keys"):
        load_calc_spec(bad_yaml)


def test_calculation_sheet_builder_brand_v34_layout_and_safety(tmp_path: Path) -> None:
    """Verify 2-sheet generation, RULE-6.1 logo, live formulas, print contract, and formula guard."""
    spec = _sample_spec()
    # Inject potentially dangerous scalar metadata to verify RULE-5.13 formula neutralization
    refs = spec["references"]
    assert isinstance(refs, dict)
    glossary = refs["glossary"]
    assert isinstance(glossary, list)
    glossary[0]["meaning_en"] = "=CMD()"

    out_xlsx = tmp_path / "calc_out.xlsx"
    builder = CalculationSheetBuilder(theme=CCBAExcelTheme())
    saved = builder.build(spec, out_xlsx)
    assert saved == out_xlsx.resolve()
    assert saved.is_file()

    wb = openpyxl.load_workbook(saved, data_only=False)
    try:
        assert wb.sheetnames == ["01-Calculation", "02-References"]
        ws1 = wb["01-Calculation"]
        ws2 = wb["02-References"]

        # Verify A4 Portrait pagination invariants and repeat header contract
        assert str(ws1.page_setup.paperSize) == str(ws1.PAPERSIZE_A4)
        assert ws1.page_setup.orientation == ws1.ORIENTATION_PORTRAIT
        assert ws1.page_setup.fitToWidth == 1
        assert ws1.page_setup.fitToHeight == 0
        assert ws1.print_title_rows in ("1:5", "$1:$5")
        assert len(ws1.row_breaks.brk) >= 1

        # Verify Brand v3.4 header banner color and bundled logo image embedding
        assert "363883" in str(ws1["A6"].fill.start_color.rgb)
        assert len(ws1._images) == 1

        # Verify live formulas were bound to symbolic cell references
        formula_cells = [
            cell.value
            for row in ws1.iter_rows(min_col=4, max_col=4)
            for cell in row
            if isinstance(cell.value, str) and cell.value.startswith("=ROUND(")
        ]
        assert formula_cells == ["=ROUND(D15*D16, 2)", "=ROUND(D22*3.6*D17, 2)"]

        # Verify generalized discipline scope, technical notes, and formula neutralization on Sheet 2
        sheet2_values = [
            str(cell.value) for row in ws2.iter_rows() for cell in row if cell.value is not None
        ]
        sheet2_texts = "\n".join(sheet2_values)
        assert "Hydraulics" in sheet2_texts
        assert "PCCC" not in sheet2_texts
        assert "GC-01" in sheet2_texts
        assert "'=CMD()" in sheet2_values
        assert len(ws2.row_breaks.brk) >= 1
    finally:
        wb.close()


def test_build_calc_sheet_from_yaml_and_cli(tmp_path: Path) -> None:
    """Verify build_calc_sheet_from_yaml and CLI calc-sheet JSON report execution."""
    cfg_path = tmp_path / "calc_spec.yaml"
    cfg_path.write_text(yaml.safe_dump(_sample_spec(), allow_unicode=True), encoding="utf-8")

    out_xlsx = tmp_path / "from_yaml.xlsx"
    res = build_calc_sheet_from_yaml(cfg_path, out_xlsx, recalculate=False, check_errors=True)
    assert res["success"] is True
    assert res["formulas_evaluated"] is False
    assert res["formula_errors"] == []
    assert Path(res["xlsx_path"]).is_file()

    cli_out = tmp_path / "cli_out.xlsx"
    report_json = tmp_path / "cli_report.json"
    argv = [
        "ccba-ooxml",
        "calc-sheet",
        str(cfg_path),
        "-o",
        str(cli_out),
        "--check-errors",
        "--output",
        str(report_json),
    ]
    with patch.object(sys, "argv", argv):
        ooxml_cli_main()

    assert cli_out.is_file()
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert Path(payload["xlsx_path"]) == cli_out.resolve()


def test_theme_hash_colors_footer_ampersand_and_custom_logo_aspect(tmp_path: Path) -> None:
    """Verify #-prefixed theme/KPI colors, escaped footer '&', and dynamic logo aspect ratio."""
    spec = _sample_spec()
    doc = spec["document"]
    assert isinstance(doc, dict)
    doc["consultant"] = "IBST & CCBA"
    kpis = spec["summary_kpis"]
    assert isinstance(kpis, list)
    for kpi in kpis:
        assert isinstance(kpi, dict)
        kpi["accent"] = f"#{str(kpi['accent']).lstrip('#')}"

    logo_path = tmp_path / "custom_logo.png"
    PILImage.new("RGB", (200, 100), color=(54, 56, 131)).save(logo_path)

    out_xlsx = tmp_path / "custom_theme.xlsx"
    theme = CCBAExcelTheme(dark_blue="#363883", ibst_red="#DA251C", bim_blue="#0093DD")
    CalculationSheetBuilder(theme=theme, logo_path=logo_path).build(spec, out_xlsx)

    wb = openpyxl.load_workbook(out_xlsx, data_only=False)
    try:
        ws1 = wb["01-Calculation"]
        assert "IBST && CCBA" in (ws1.oddFooter.center.text or "")
        assert len(ws1._images) == 1
        img = ws1._images[0]
        assert img.anchor.ext.cx == pixels_to_EMU(132)
        assert img.anchor.ext.cy == pixels_to_EMU(66)
    finally:
        wb.close()
