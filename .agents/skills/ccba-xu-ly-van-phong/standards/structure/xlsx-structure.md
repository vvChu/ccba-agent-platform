# Cấu trúc Bảng tính (XLSX Structure)

Quy chuẩn bố cục, phân cấp dữ liệu, formatting cho file Excel.

---

## Kiến trúc multi-sheet chuẩn

Một workbook chuyên nghiệp gồm các nhóm sheet sau:

| Nhóm | Tên sheet | Vai trò |
|---|---|---|
| Chính | `00-HuongDan` hoặc `README` | Giải thích cách dùng, cảnh báo, disclaimer |
| Chính | `01-DuLieuChinh` | Bảng dữ liệu chính |
| Chính | `02-ChiTiet` | Bảng phụ / chi tiết |
| Phụ trợ | `98-Metadata` | Thông tin dự án: tên, ngày, phiên bản |
| Phụ trợ | `99-NhatKy` | Nhật ký cảnh báo, audit trail |

**Quy tắc đặt tên sheet:**
- Tiền tố số 2 chữ số (`01-`, `02-`, `98-`) để giữ thứ tự ổn định
- Tên PascalCase hoặc CamelCase tiếng Việt không dấu
- Không dùng ký tự đặc biệt: `/ \ ? * [ ]`

---

## Phân cấp dữ liệu trong sheet

Bảng tính phức tạp cần phân cấp row bằng **màu fill + cỡ chữ + bold**, không phải indent:

| Cấp | Loại | Font | Fill | Ví dụ |
|---|---|---|---|---|
| Header | Tiêu đề cột | 10pt bold, text trắng | Fill đậm | `STT`, `Nội dung`, `Khối lượng` |
| Cấp 0 | Chương / Section | 11pt bold | Fill nhẹ khác biệt | `I/ PHẦN ĐẤT VÀ MÓNG` |
| Cấp 1 | Công tác / Hạng mục | 10pt bold | Fill nhẹ | `Đào móng cột rộng >1m` |
| Cấp 2 | Chi tiết / Breakdown | 9pt regular, text xám | Fill rất nhạt hoặc trắng | `M1: 4 hố: 4×1.9×1.9×1.7` |

**Nguyên tắc:** Mắt nhìn phải phân biệt được cấp ngay lập tức bằng **cả 3 yếu tố**: cỡ chữ, độ đậm, và màu nền. Không dùng indent trong Excel vì khó select/filter.

---

## Dòng Header

| Yếu tố | Quy chuẩn |
|---|---|
| Font | 10pt bold, text trắng `#FFFFFF` |
| Fill | Màu đậm (xem `standards/color/`) |
| Align text | Center |
| Align vertical | Center |
| Wrap text | Bật |
| Row height | ≥ 30pt |
| Freeze | Freeze row 1 (hoặc row header cuối) |

---

## Column width chuẩn

| Loại cột | Width | Align |
|---|---|---|
| STT / # | 4-6 | Center |
| Mã code | 10-12 | Left |
| Tên / nội dung | 30-50 | Left, wrap |
| Đơn vị (ĐVT) | 6-8 | Center |
| Số lượng / khối lượng | 12-14 | Right |
| Trạng thái / Mức độ | 14-17 | Center |
| Ngày tháng | 12-14 | Center |
| Phần trăm | 10-12 | Center |
| Ghi chú / Nguồn | 20-30 | Left, wrap |

---

## Dòng tổng / Summary

| Yếu tố | Quy chuẩn |
|---|---|
| Font | 11pt bold |
| Fill | Không fill hoặc nhẹ |
| Border top | Double line (phân cách với data) |
| Công thức | `=SUM()` — bắt buộc Live Formula |
| Màu text số tổng | Đỏ bold nếu cần nhấn mạnh |

---

## Border

| Vùng | Border |
|---|---|
| Header | Thin all sides |
| Data rows | Thin all sides |
| Dòng tổng | Top double, others thin |
| Vùng ngoài bảng | Không border |

---

## Số và đơn vị

| Quy tắc | Ví dụ |
|---|---|
| Số thập phân ≤ 2 chữ số | `98.67` không phải `98.6700` |
| Đơn vị ghi riêng cột (không trong cell số) | Cột F: `m³`, cột G: `98.67` |
| Format number, không để General | Custom format: `#,##0.00` |
| Percentage | Format `0%` hoặc `0.0%` |

---

## Sheet README / Hướng dẫn

Sheet đầu tiên, cột A width 80, chứa:
- Dòng 1: Tiêu đề file (14pt bold)
- Dòng 3-5: Mô tả mục đích file
- Dòng 7+: Các cảnh báo / disclaimer (nếu có)
- Không format phức tạp, chỉ text thuần

---

## Sheet Metadata

Bảng 2 cột (Key-Value):

| A (25 width, bold) | B (40 width) |
|---|---|
| Tên công trình | [Tên] |
| Chủ đầu tư | [Tên] |
| Ngày xuất | [Ngày] |
| Phiên bản | v1 |
| Người lập | [Tên] |

---

## Sheet Nhật ký / Cảnh báo

Bảng 3 cột với traffic light:

| # | Mức độ | Nội dung |
|---|---|---|
| Fill cam `#FDEBD0` | ⚠️ WARNING | Mô tả cảnh báo |
| Fill xanh `#D5F5E3` | ✅ OK | Mô tả xác nhận |
| Fill đỏ `#FADBD8` | ❌ ERROR | Mô tả lỗi |

<!-- NDT-0904004920 -->
