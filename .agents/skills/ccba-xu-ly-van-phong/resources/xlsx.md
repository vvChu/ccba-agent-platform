# Kỹ năng XLSX — Excel

Hướng dẫn tạo và thao tác bảng tính Excel chuyên nghiệp.

---

## Nguyên tắc tối thượng: Live Formula

Tuyệt đối cấm hardcode kết quả tính toán vào cell. Excel phải "sống" — tính toán lại khi đổi đầu vào.

```python
# ❌ SAI
total = df['Sales'].sum()
sheet['B10'] = total

# ✅ ĐÚNG
sheet['B10'] = '=SUM(B2:B9)'
sheet['C5'] = '=(C4-C2)/C2'
```

---

## Công cụ

| Công cụ | Dùng cho |
|---|---|
| `openpyxl` | Tạo file đẹp, format corporate, conditional formatting |
| `pandas` | Làm sạch dữ liệu lớn, data cleaning |

---

## Formatting corporate chuẩn

```python
from openpyxl.styles import Border, Side, Alignment, PatternFill, Font

THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
```

### Column width chuẩn

| Loại cột | Width | Align |
|---|---|---|
| STT | 4-7 | Center |
| Tên / nội dung | 28-48 | Left, wrap |
| Trạng thái | 14-17 | Center |
| Ngày | 12-14 | Center |
| Phần trăm | 10-12 | Center |
| Ghi chú | 25-32 | Left, wrap |

---

## Zero Error Policy

Cấm tuyệt đối khi mở file:
- `#REF!` — cell trỏ vùng không tồn tại
- `#DIV/0!` — chia cho 0 chưa catch `IF`
- `#VALUE!` — lộn data type

---

## Dependencies

```
pip install openpyxl pandas
```

---

## CCBA Deep Seam (`ccba-ooxml`) & 5 Rào chắn Thực chiến

Tuân thủ **ADR-0061 (`TID251`)**: bên ngoài `packages/ccba-ooxml`, tuyệt đối không tự viết wrapper `import openpyxl` rời rạc mà sử dụng thống nhất các Deep Seam công khai của `ccba_ooxml`:

| Nhu cầu | Deep Seam `ccba_ooxml` chuẩn | Ghi chú |
|---|---|---|
| Dựng bảng tính kỹ thuật song ngữ chuẩn Brand v3.4 + RULE-6.1 | `CalculationSheetBuilder`, `build_calc_sheet_from_yaml`, `CCBAExcelTheme` | CLI: `ccba-ooxml calc-sheet <spec.yaml>` |
| Tạo workbook bảng dữ liệu mới / điền template / đọc an toàn | `XlsxWorkbookWriter`, `XlsxTemplateFiller`, `XlsxReader`, `sanitize_xlsx_value` | Tích hợp kiểm tra ZIP an toàn `RULE-5.13` |
| Tính lại công thức & kiểm tra 0 lỗi | `recalc_xlsx`, `audit_xlsx_formula_errors` | Ưu tiên Excel COM trên Windows, fallback LibreOffice |
| Xuất PDF từ Excel trên Windows / Linux | `xlsx_to_pdf` (`convert_to_pdf`) | Tự động tuyến `.xlsx` sang `Excel.Application` trên `win32` |

### 5 Bẫy Thực Chiến Đã Được Đúc Rút

1. **Bẫy `no:` của YAML 1.1:** PyYAML `safe_load` tự chuyển khóa `no:` không có dấu ngoặc kép thành boolean `False`. Schema bảng tính kỹ thuật bắt buộc dùng khóa **`item_no:`** (bộ dựng có dự phòng đọc fallback nhưng YAML chuẩn phải tránh `no:`).
2. **Bẫy `fitToHeight > 0` đè mất ngắt trang `Break`:** Đặt `fitToHeight >= 1` khiến Microsoft Excel bỏ qua toàn bộ `Break` ngang thủ công, gây mồ côi tiêu đề mục ở cuối trang 1. Luôn giữ **`fitToHeight = 0`**, `fitToWidth = 1`, `print_title_rows = "1:5"` kết hợp `Break` tường minh.
3. **Bẫy cột hẹp ở Ma trận Kiểm soát Dự án:** Không đặt nhãn tiếng Việt dài trong cột `STT` (`width = 4..7`); luôn gộp ngang (`A:C`, `D:F`) bằng `CellRichText` nhãn đậm + giá trị.
4. **Song ngữ xếp dọc (`CellRichText`):** Cơ chế `CellRichText` + `InlineFont` (đóng gói sẵn trong `CalculationSheetBuilder`, dòng Việt + dòng Anh nghiêng `#595959`) giúp bảng in vừa gọn **A4 Portrait** thay vì mở rộng gấp đôi số cột.
5. **Đối soát pháp lý & kiểm định ảnh PDF→PNG (`ADR-0059`):** Mọi bảng tính kỹ thuật có viện dẫn QCVN/TCVN phải đối soát điều khoản thực tế qua `ccba-legal-intel` (hoặc thu thập nguyên văn bằng `ccba-legal-ingest` nếu kho tri thức chưa có), sau đó chạy `recalc_xlsx(..., check_errors=True)` và chuyển PDF sang PNG kiểm tra trực quan 100% trang trước khi phát hành.

<!-- NDT-0904004920 -->
