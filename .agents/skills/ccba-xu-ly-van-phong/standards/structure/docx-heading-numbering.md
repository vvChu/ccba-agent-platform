# Heading & Numbering

Hệ thống phân cấp heading và đánh số cho các loại văn bản.

---

## Hệ 5 cấp — VB ngắn / trung bình

Dùng cho đề xuất, báo cáo, whitepaper, tài liệu đào tạo (5-30 trang).

| Cấp | Ký hiệu | Ví dụ | Dùng cho |
|---|---|---|---|
| Cấp 1 | Số La Mã hoặc Ả Rập | `I. Mục tiêu` hoặc `1. Bối cảnh` | Section chính |
| Cấp 2 | Số chấm số | `1.1.` `1.2.` | Sub-section |
| Cấp 3 | Số chấm số chấm số | `1.1.1.` | Khi cần phân cấp sâu (ít dùng) |
| Cấp 4 | Chữ cái thường | `a.` `b.` `c.` | Hạng mục con |
| Cấp 5 | Số trong ngoặc | `(1)` `(2)` `(3)` | Mệnh đề nhỏ, tham chiếu inline |

### Ví dụ:

```
I. Mục tiêu

1.1. Mục tiêu chung
1.2. Mục tiêu cụ thể

1.2.1. Ngắn hạn
   a. Hoàn thành khảo sát hiện trạng
   b. Xây dựng bản thử mẫu

Các tiêu chí đánh giá gồm: (1) chất lượng đầu ra; (2) thời gian xử lý; (3) mức độ tự vận hành.
```

---

## Hệ 9 cấp — VB dài / kỹ thuật

Dùng cho thuyết minh, nghiên cứu khả thi, báo cáo kỹ thuật (50-200 trang).

| Level | Định dạng | Ký tự dẫn | Dùng cho |
|---|---|---|---|
| 0 | Số La Mã hoa | `CHƯƠNG I.` | Chương |
| 1 | Số Ả Rập | `1.` `2.` | Mục lớn trong chương |
| 2 | Số chấm số | `1.1.` `1.2.` | Tiểu mục |
| 3 | Ba cấp số | `1.1.1.` | Cấp 4 (ít dùng) |
| 4 | Dấu gạch | `-` | Bullet list thường |
| 5 | Dấu cộng | `+` | Sub-bullet |
| 6 | Chữ cái thường | `a)` `b)` `c)` | Liệt kê có thứ tự |
| 7 | Hình số | `Hình 1.1.` | Caption hình |
| 8 | Bảng số | `Bảng 1.1.` | Caption bảng |

### Ví dụ:

```
CHƯƠNG II. ĐIỀU KIỆN TỰ NHIÊN                          ← Level 0

2. Đặc điểm điều kiện tự nhiên                          ← Level 1

2.1. Đặc điểm khí tượng                                 ← Level 2

2.1.1. Bão và áp thấp nhiệt đới                         ← Level 3

    - Tần suất bão đổ bộ chiếm 33,7%                    ← Level 4
      + Bão có gió cấp 6-7: 29 cơn                      ← Level 5

    a) Ngập úng do nước dâng                             ← Level 6
    b) Thiệt hại công trình do gió mạnh                 ← Level 6

Bảng 2.1. Vận tốc gió trung bình tháng và năm           ← Level 8
Hình 2.3. Đường tần suất mực nước                        ← Level 7
```

---

## Nguyên tắc chung

- Cấp 1 và 2 bắt buộc cho tài liệu từ 5 trang trở lên.
- Cấp 4 dùng chữ cái `a.` để mắt đọc nhận ra ngay là cấp thấp, không nhầm với cấp 1.
- Không đánh quá 4 cấp số (`1.1.1.1.`) vì mất khả năng đọc — thay bằng bullet.
- Không trộn `i. ii. iii.` với `a. b. c.` — cả hai đều cấp thấp, dễ nhầm.
- VB dài bắt buộc dùng multilevel list của Word để tự động cập nhật khi thêm/xóa mục.
