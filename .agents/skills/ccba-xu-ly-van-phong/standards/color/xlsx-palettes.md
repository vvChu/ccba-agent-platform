# Bộ màu Bảng tính (XLSX Color Palettes)

Các bộ phối màu dành riêng cho bảng tính Excel.

---

## Palette X1 — Professional Dark (Header tối)

Dùng cho bảng kỹ thuật, dự toán, data block.

| Vai trò | Mã HEX | Mô tả |
|---|---|---|
| Header fill | `#2C3E50` | Charcoal navy |
| Header text | `#FFFFFF` | Trắng |
| Row Chương/Section | `#FFF2CC` | Vàng rất nhạt |
| Row Hạng mục/CTAC | `#D6EAF8` | Xanh dương nhạt |
| Row Chi tiết | `#F9F9F9` | Xám rất nhạt |
| Text chi tiết | `#666666` | Xám |
| Dòng tổng text | `#FF0000` | Đỏ bold |

---

## Palette X2 — Corporate Green (Kế hoạch)

Dùng cho bảng kế hoạch 5W1H, roadmap, tracking tiến độ.

| Vai trò | Mã HEX | Mô tả |
|---|---|---|
| Header fill | `#375623` | Xanh lá đậm |
| Header text | `#FFFFFF` | Trắng |
| Row nhóm/giai đoạn | `#E2EFDA` | Xanh lá rất nhạt |
| Row chi tiết | Trắng | Không fill |
| Title text | `#375623` | Xanh lá đậm, 14pt bold |

---

## Palette X3 — Blue Corporate

Dùng cho bảng tổng hợp, phiếu khảo sát, dashboard.

| Vai trò | Mã HEX | Mô tả |
|---|---|---|
| Header fill | `#4472C4` | Xanh dương corporate |
| Header text | `#FFFFFF` | Trắng |
| Zebra row lẻ | `#D9E2F3` | Xanh rất nhạt |
| Zebra row chẵn | `#FFFFFF` | Trắng |
| Dòng tổng | Bold, không fill | |

---

## Palette X4 — CCBA Brand Identity v3.4 (Bảng tính Kỹ thuật Song ngữ & RULE-6.1)

Dùng mặc định cho các bảng tính kỹ thuật song ngữ Việt – Anh phát hành dưới danh nghĩa `IBST - CCBA` (kết hợp `ccba_ooxml:CCBAExcelTheme` và font thống nhất `Segoe UI`).

| Vai trò | Mã HEX | Mô tả |
|---|---|---|
| Dark Navy Primary (Header / Banner / Viền khung) | `#363883` | Xanh tím đậm CCBA Brand v3.4 |
| Accent Red (Đường gạch Header / Grand Total / KPI) | `#DA251C` | Đỏ cờ IBST chuẩn Brand v3.4 |
| Bright Cyan Blue (KPI Accent / Slogan *Better*) | `#0093DD` | Xanh sáng BIM Brand v3.4 |
| Input Text / Font xanh nhập liệu | `#005A9C` | Xanh dương phân biệt ô nhập tay |
| Input Cell Fill | `#F0F6FC` | Xanh rất nhạt đánh dấu ô sửa được |
| Section Banner Fill | `#E8EAF6` | Tím xanh rất nhạt cho tiêu đề mục lớn |
| Sub-banner Fill | `#F1F5F9` | Xám xanh nhẹ cho nhóm tính toán con |
| Subtotal Fill | `#EBF5FB` | Xanh nhạt cho kết quả trung gian (`subtotal`) |
| Key Result Fill | `#E6F4FA` | Xanh nhấn nhẹ cho kết quả nhánh (`key_result`) |
| Grand Total Fill / Note Code Fill | `#FEF9E7` | Vàng nhạt nhấn mạnh kết quả chi phối (`grand_total`) |
| Metadata / Sign-off Header Fill | `#F8FAFC` | Nền trung tính sạch cho ma trận dự án |
| Body Text Dark / Muted | `#1A202C` / `#595959` | Tiếng Việt chính / phụ đề tiếng Anh nghiêng |
| Grid Border Light | `#CBD5E1` | Đường kẻ mảnh dễ đọc cả màn hình và bản in |

> **Slogan footer 3 màu:** `Smarter` (`#363883`) `Faster` (`#DA251C`) `Better` (`#0093DD`) kèm dòng ghi nhận `IBST - CCBA`.

---

## Traffic Light (dùng chung cho mọi palette)

| Mức | Fill | Text/Icon | Dùng cho |
|---|---|---|---|
| OK / Pass | `#D5F5E3` (xanh nhạt) | ✅ | Xác nhận, đạt chuẩn |
| Warning | `#FDEBD0` (cam nhạt) | ⚠️ | Cảnh báo, cần kiểm tra |
| Error / Fail | `#FADBD8` (đỏ nhạt) | ❌ | Lỗi, vượt ngưỡng |
| Info | `#D4E6F1` (xanh nhạt) | ℹ️ | Thông tin tham khảo |

---

## Conditional Formatting

Áp dụng trực tiếp trong Excel (không fill tay):

```python
# xu-ly-van-phong (c) Nguyen Duy Tung
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import PatternFill

green_fill = PatternFill(bgColor="D5F5E3")
orange_fill = PatternFill(bgColor="FDEBD0")
red_fill = PatternFill(bgColor="FADBD8")

ws.conditional_formatting.add('H2:H100',
    CellIsRule(operator='greaterThanOrEqual', formula=['0.9'], fill=green_fill))
ws.conditional_formatting.add('H2:H100',
    CellIsRule(operator='between', formula=['0.7', '0.89'], fill=orange_fill))
ws.conditional_formatting.add('H2:H100',
    CellIsRule(operator='lessThan', formula=['0.7'], fill=red_fill))
```

<!-- NDT-0904004920 -->

