---
proposal_id: "2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com"
type: "tool"
name: "ooxml-xlsx-calc-sheet-and-excel-com"
status: "open"
priority: "Cao"
related_issue: "#851"
proposed_by_project: "ccba-engineering-calc"
proposed_by_archetype: "project_delivery"
proposed_date: "2026-11-22"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
---

# Proposal: Bilingual XLSX Calculation Sheet Deep Seam & Windows Excel COM Engine

## 1. Bối cảnh & Vấn đề Cần Giải Quyết
- Trên Hub (`origin/main`), PR #848 đã bổ sung `XlsxTemplateFiller`, `XlsxWorkbookWriter` và `XlsxReader` cho Seam `ooxml_processor.v1`, nhưng vẫn còn 3 khoảng trống xác định tại Tầng 1 (`ADR-0057` Cổng 0):
  1. `converter.py` ở chế độ `"auto"` trên Windows đang mở mọi định dạng tệp (bao gồm `.xlsx`) bằng `Word.Application` thay vì `Excel.Application`.
  2. `calc.py` chưa có cơ chế tính lại công thức + xuất PDF qua Windows Excel COM và chưa có hàm kiểm tra lỗi công thức (`#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`).
  3. `ccba_ooxml.xlsx` chưa có Deep Seam dựng bảng tính kỹ thuật song ngữ chuẩn Brand Identity v3.4 (`#363883`, `Segoe UI`), RULE-6.1 (Header 2 cấp + logo động `logo_ccba_full.png`), `CellRichText` xếp dọc và cấu hình in A4 Portrait (`fitToHeight=0` + `print_title_rows="1:5"` + ngắt trang tường minh).

## 2. Giải Pháp Đề Xuất (Tier 1 — `packages/ccba-ooxml`)
- Nâng cấp `converter.py`: bổ sung `_convert_via_excel` (`Excel.Application`), phân tuyến theo phần mở rộng trong chế độ `auto`, xuất alias `xlsx_to_pdf`.
- Nâng cấp `calc.py`: thực thi kiểm định RULE-5.13 (`verify_xlsx_zip_safety`) ngay đầu hàm `recalc_xlsx`, bổ sung `_recalc_via_excel_com` và `audit_xlsx_formula_errors`.
- Bổ sung `_theme.py` (`CCBAExcelTheme`) và `_calc_sheet.py` (`CalculationSheetBuilder`, `build_calc_sheet_from_yaml`, `resolve_formula`) cùng lệnh CLI `ccba-ooxml calc-sheet`.
- Mở rộng Public Deep Seams `ccba_ooxml.__all__` (`72 -> 78`) và đồng bộ `seam-contracts.yaml`, `verify-ccba-ooxml`.
