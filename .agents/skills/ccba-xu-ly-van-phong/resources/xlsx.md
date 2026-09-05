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

<!-- NDT-0904004920 -->
