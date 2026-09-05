# Typography (Font & Cỡ chữ)

Quy chuẩn font family, cỡ chữ và weight theo loại văn bản.

---

## Font family theo loại văn bản

| Loại | Font body | Font heading | Font code/số | Ghi chú |
|---|---|---|---|---|
| VB hành chính NĐ 30 | Times New Roman 13-14pt | Times New Roman bold | — | Chuẩn NĐ 30/2020 |
| VB dài / kỹ thuật | Times New Roman 13pt | Times New Roman bold | Consolas 10pt | Chuẩn học thuật VN |
| VB ngắn formal | Times New Roman 13pt | Times New Roman bold | Calibri 11pt | Gửi cấp chiến lược |
| VB ngắn modern | Arial 12pt | Arial bold | Consolas 10pt | Doanh nghiệp SME |
| VB ngắn editorial | Arial 11pt | Arial 14pt bold | Arial 10pt | Review, phản biện |
| Excel | Calibri 9-10pt | Calibri 15-16pt bold | Calibri 12-13pt | |

**Quy tắc tuyệt đối:** Một tài liệu chỉ dùng **một font body**, không trộn Times với Arial trong cùng văn bản.

---

## Cấp bậc cỡ chữ

### VB ngắn / trung bình

| Vai trò | Size | Weight | Align |
|---|---|---|---|
| Title doc (trang bìa) | 24pt | Bold | Center |
| Heading 1 (I, II, III) | 14pt | Bold | Left |
| Heading 2 (1.1, 1.2) | 13pt | Bold | Left |
| Heading 3 (a, b, c) | 12pt | Bold | Left |
| Body | 11-12pt | Regular | Justify |
| Caption / note | 10-11pt | Italic | Center hoặc Left |
| Header / footer | 9pt | Italic | |

### VB dài / kỹ thuật

| Vai trò | Size | Weight | Align |
|---|---|---|---|
| CHƯƠNG | 13-14pt | Bold | Left |
| Mục (1. 2. 3.) | 13pt | Bold | Left |
| Tiểu mục (1.1.) | 13pt | Bold | Left |
| Body | 13pt | Regular | Justify |
| Bảng số liệu | 11pt | Regular | Center |
| Caption bảng/hình | 12pt | Bold italic | Center |
| Ghi chú, nguồn | 12pt | Italic | |

**Lưu ý:** VB dài không dùng size tăng dần theo cấp heading. Tất cả heading cùng 13pt, phân cấp bằng **màu và numbering** (xem `standards/color/`).

---

## Đơn vị quy đổi (cho lập trình)

| Đơn vị | Quy đổi |
|---|---|
| pt → half-points (docx-js) | 1pt = 2 half-points. Ví dụ: 12pt = 24 |
| pt → DXA (spacing) | 1pt = 20 DXA. Ví dụ: 6pt = 120 DXA |
| cm → DXA | 1cm = 567 DXA |
| cm → EMU | 1cm = 360000 EMU |
