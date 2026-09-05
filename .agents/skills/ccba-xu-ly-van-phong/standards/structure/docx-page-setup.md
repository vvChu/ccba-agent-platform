# Thiết lập Trang (Page Setup)

Quy chuẩn khổ giấy, lề và line spacing cho các loại văn bản.

---

## Khổ giấy

Mọi văn bản dùng **A4** (210 × 297 mm / 595 × 842 pt / 11906 × 16838 DXA).

---

## Margin theo loại văn bản

| Loại | Top | Bottom | Left | Right | Ghi chú |
|---|---|---|---|---|---|
| VB ngắn/trung bình (đề xuất, báo cáo) | 2 cm | 2 cm | **3 cm** | 2 cm | Left 3 cm để đóng gáy |
| VB dài (thuyết minh, nghiên cứu) | 2 cm | 2 cm | **3 cm** | **1.5 cm** | Right hẹp vì in 1 mặt |
| VB hành chính NĐ 30 | 2 cm | 2 cm | **3 cm** | 2 cm | Theo NĐ 30/2020 |
| Slide PPTX | — | — | — | — | Không áp dụng page margin |

**Quy đổi DXA:** 1 cm = 567 DXA. Ví dụ: 3 cm = 1701 DXA, 2 cm = 1134 DXA.

**Chiều rộng nội dung (Content Width):** Lấy Page Width trừ Left trừ Right.
- VB ngắn: `11906 − 1701 − 1134 = 9071 DXA`
- VB dài: `11906 − 1701 − 851 = 9354 DXA`

---

## Line spacing

| Loại đoạn | VB ngắn | VB dài | Lý do khác biệt |
|---|---|---|---|
| Body paragraph | **1.4** (340 twentieths) | **1.2** | VB dài tiết kiệm giấy (giảm 15-20% trang) |
| Heading | 1.33 | 1.2 | |
| Title doc | 1.0 | 1.0 | |
| Bảng caption | 1.15 | 1.15 | |
| Code block / ASCII art | 1.0 | 1.0 | Bắt buộc không giãn |

**Nguyên tắc:** Dưới 1.2 là bí (chỉ VB dài mới dùng). Trên 1.7 là loãng. Khoảng 1.4 là chuẩn cho đọc thoải mái.

---

## Paragraph spacing

| Loại đoạn | Space before | Space after |
|---|---|---|
| Body paragraph | 0 | 6-7pt |
| List item | 2pt | 4pt |
| Heading cấp 1 | 18pt | 8pt |
| Heading cấp 2 | 12pt | 6pt |
| Title doc | 0 | 6pt |
| Caption dưới bảng | 0 | 12pt |

---

## First line indent

| Loại | Indent | Ghi chú |
|---|---|---|
| VB ngắn | Không thụt | Phong cách hiện đại, dùng spacing giữa đoạn |
| VB dài / kỹ thuật | **1 cm** (360045 EMU) | Chuẩn văn bản học thuật và hành chính VN |
| VB hành chính NĐ 30 | **1 cm** | Bắt buộc |

---

## Header và Footer distance

| Thông số | Giá trị |
|---|---|
| Header distance from top | 0.8 cm (22.7pt) |
| Footer distance from bottom | 1.3 cm (36pt) |

<!-- NDT-0904004920 -->
