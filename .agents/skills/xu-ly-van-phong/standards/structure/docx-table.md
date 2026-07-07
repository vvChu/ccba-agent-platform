# Bảng (Table Patterns)

Các mẫu bảng chuẩn hóa cho DOCX và XLSX.

---

## Mẫu T1 — Bảng lộ trình / giai đoạn

Dùng cho roadmap, milestone, chương trình đào tạo.

| Yếu tố | Quy chuẩn |
|---|---|
| Header | Fill đậm + text trắng bold, center, vAlign center |
| Cột 1 (nhãn) | Bold, center, zebra fill |
| Cột nội dung | Regular, align left |
| Border | `thin` toàn bộ |
| Row height | Header ≥ 30pt, body ≥ 24pt |
| Cell padding | 0.1 cm top/bottom, 0.15 cm left/right |

---

## Mẫu T2 — Bảng phân loại 3 cấp (Traffic Light)

Dùng cho phân loại rủi ro, xếp hạng ưu tiên, đánh giá bảo mật.

| Row | Fill | Ý nghĩa |
|---|---|---|
| Header | Đậm + text trắng | Tiêu đề |
| Cấp 1 / Safe | Xanh lá nhạt | An toàn, được phép |
| Cấp 2 / Warn | Vàng nhạt | Cần thận trọng |
| Cấp 3 / Danger | Đỏ nhạt | Cấm hoặc nhạy cảm |

Text trong cell giữ màu đen, chỉ fill cell thay đổi để đảm bảo contrast.

---

## Mẫu T3 — Bảng zebra (xen kẽ màu)

Dùng cho bảng số liệu, so sánh, thống kê.

| Yếu tố | Quy chuẩn |
|---|---|
| Header | Fill đậm + text trắng bold center |
| Row lẻ | Fill xám nhạt |
| Row chẵn | Trắng |
| Cột text | Align left |
| Cột số | Align right hoặc center |
| Dòng tổng cuối | Bold |

---

## Mẫu T4 — Bảng ma trận so sánh (2 trục)

Dùng cho so sánh cũ/mới, module × thuộc tính.

| Yếu tố | Quy chuẩn |
|---|---|
| Header hàng đầu | Đậm, text trắng |
| Cột 1 (tiêu chí) | Bold, fill nhẹ |
| Các cột so sánh | Regular |

---

## Mẫu T5 — Bảng số liệu kỹ thuật (VB dài)

Dùng cho bảng dữ liệu quan trắc, thống kê theo tháng.

| Yếu tố | Quy chuẩn |
|---|---|
| Style | Normal Table mặc định |
| Border | Thin 0.5pt đen |
| Header | Bold 11pt center |
| Data | Regular 11pt |
| Fill | **Không fill** (bảng số liệu không dùng màu) |

---

## Quy tắc chung mọi bảng

- Không bao giờ dùng bảng 1 cột — đó là list, viết lại thành bullet.
- Header luôn bold + center + contrast cao.
- Cột số luôn align phải, cột text align trái, cột nhãn ngắn center.
- Bảng từ 5 dòng trở lên bắt buộc zebra row.
- Bảng dài trên 20 dòng phải có dòng tổng cuối.
- Không merge cell theo chiều dọc trong body — phá vỡ sort/filter.
- Mỗi bảng có caption ngắn phía trên (bold) mô tả ý đồ.
- **Màu cụ thể** cho header/zebra: xem `standards/color/` tương ứng. Mặc định (đen trắng): header fill xám đậm, zebra fill xám nhạt.
