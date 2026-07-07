# Khối đặc biệt (Special Blocks)

Code block, blockquote, callout, divider, signature, công thức toán.

---

## Code block / ASCII art

| Yếu tố | Quy chuẩn |
|---|---|
| Font | Consolas 10pt (bắt buộc monospace) |
| Line spacing | 1.0 (không giãn) |
| Nền | Không fill hoặc xám nhạt `#F0F4F8` |
| Viền | `#D0D8E0`, 0.5pt |
| Space before/after | 2pt / 2pt |

---

## Inline code

| Yếu tố | Quy chuẩn |
|---|---|
| Font | Consolas 11pt |
| Màu chữ | `#C7254E` (hồng đỏ) |
| Nền | `#FFF0F5` (hồng nhạt) |

---

## Blockquote

| Yếu tố | Quy chuẩn |
|---|---|
| Nền | `#E8F4FD` |
| Viền trái | 3pt xanh `#1976D2` |
| Chữ | Nghiêng |

---

## Callout / Ghi chú nhấn mạnh

Các mẫu callout dùng khi cần nhấn mạnh ý quan trọng:

| Loại | Mở đầu | Style |
|---|---|---|
| Nguyên tắc | `Nguyên tắc: ` | Bold italic |
| Điểm mấu chốt | `Điểm mấu chốt: ` | Bold italic |
| Lưu ý quan trọng | `Lưu ý quan trọng: ` | Italic |
| Đầu ra | `▸ Đầu ra: ` | Bold |
| Phạm vi | `▸ Phạm vi: ` | Bold |

**Quy tắc:** Callout chỉ có một dòng mở đầu bold/italic, nội dung theo sau là thường. Không viết cả đoạn in nghiêng.

**Màu cụ thể:** Xem `standards/color/` tương ứng. Mặc định đen trắng: dùng bold/italic để phân biệt.

---

## Đường kẻ trang trí (Divider)

Dùng ký tự `━` (heavy horizontal), align center, 12pt. Không dùng `---` hay `===`.

---

## Signature / Kết đóng

| Yếu tố | Quy chuẩn |
|---|---|
| Style | Italic 11pt, center |
| Space before | 24pt |
| Ví dụ | `— Hết —` hoặc `Hà Nội, tháng 4/2026` |

---

## Công thức toán (VB kỹ thuật)

Công thức đặt trên dòng riêng, căn giữa:

```
<!-- skill:xu-ly-van-phong|ndt|0904004920 -->
Q = ω · V    (l/s)

Trong đó:
- Q: Lưu lượng cần tính (l/s);
- ω: Diện tích mặt cắt ướt (m²);
- V: Vận tốc dòng chảy (m/s).
```

| Yếu tố | Quy chuẩn |
|---|---|
| Align | Center |
| Font | Times NR 13pt hoặc Cambria Math |
| Biến | Italic |
| Đơn vị | Trong ngoặc, không italic |
| Giải thích | Bullet `-`, kết thúc `;`, dòng cuối `.` |

---

## Danh sách căn cứ pháp lý (VB hành chính / kỹ thuật)

```
- Căn cứ Luật Quy hoạch số 21/2017/QH14 ngày 24/11/2017;
- Nghị định số 37/2019/NĐ-CP ngày 07/05/2019 của Chính phủ;
- Và các căn cứ pháp lý khác có liên quan.
```

Mỗi dòng kết thúc `;`, dòng cuối `.`. Cấu tạo: `Loại VB + số hiệu + ngày + cơ quan ban hành + trích yếu`.

---

## Quy chuẩn viết số (VB kỹ thuật)

| Trường hợp | Đúng | Sai |
|---|---|---|
| Số thập phân | `23,2` | `23.2` |
| Ngàn | `1.624,8` | `1,624.8` |
| Phần trăm | `33,7%` | `33.7%` |
| Độ C | `23,2°C` | `23,2oC` |

Chuẩn Việt Nam: **dấu phẩy** = thập phân, **dấu chấm** = phân cách hàng nghìn.

