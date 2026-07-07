# Văn Xuôi — Prose Format

**Module:** check/prose-format
**Mục đích:** Kiểm tra format văn xuôi tự nhiên: cấm bullet trong thân văn, inline enumeration, đa dạng ký hiệu nối, độ dài đoạn biến thiên.

---

## 1. Cấm bullet points trong thân văn

```
❌ Luật mới quy định:
  - 30% lợi ích thuộc nhà khoa học
  - 100% quyền sở hữu trí tuệ

✅ Nhà khoa học được hưởng tối thiểu 30% lợi ích từ kết quả nghiên cứu.
   Tổ chức chủ trì được giao 100% quyền sở hữu trí tuệ.
```

**Bullet CHỈ dùng cho:** Technical docs, business reports, checklists, how-to guides.

**Ngoại lệ — bài profile/bio:** Cho phép trộn format: văn xuôi giới thiệu + bullet liệt kê dịch vụ.

---

## 2. Inline Enumeration

Khi liệt kê ≥ 3 items trong văn xuôi, KHÔNG dùng bullet.

| Số items | Kỹ thuật | Ví dụ |
|----------|----------|-------|
| 3-4 items | "Một là... Hai là..." | "Một là rủi ro tập trung. Hai là mất kiến thức." |
| ≥ 5 items | (1), (2), (3) | "...thiết kế (1) tiêu chuẩn, (2) kiến trúc và (3) nguyên tắc..." |

---

## 3. Đa dạng ký hiệu nối câu

Không dùng cùng một kiểu nối quá 2-3 lần liên tiếp. Luân phiên:

| Kỹ thuật | Khi dùng |
|----------|----------|
| Dấu phẩy `,` | Bổ sung thông tin ngắn |
| Ngoặc đơn `()` | Giải thích, con số phụ |
| Ngoặc kép `""` | Thuật ngữ, trích dẫn |
| Ngắt câu mới `.` | Ý tách biệt, tạo nhịp |
| Từ nối | `mà, để, nơi, với, rằng, vì, nhưng` |

---

## 4. Độ dài đoạn văn biến thiên

Mỗi đoạn từ 1 đến 6 câu, xen kẽ ngẫu nhiên. Tuyệt đối tránh tất cả đoạn cùng độ dài.

---

## 5. Cấm headers trong storytelling/blog

```
❌ ## Giới thiệu → ## Phần 1 → ## Kết luận
✅ Viết liền mạch, dùng câu chuyển ý tự nhiên
```

---

## Grep Patterns

| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Bullet in prose | `^- ` hoặc `^\* ` trong file không phải checklist/spec | Nghi vi phạm — kiểm tra context |
| Headers in blog | `^## ` trong file storytelling | Nghi vi phạm |

## Checklist

- [ ] Không dùng bullet trong thân văn giải thích
- [ ] Inline enumeration đúng cách
- [ ] Ký hiệu nối câu đa dạng
- [ ] Độ dài đoạn biến thiên
- [ ] Không dùng headers trong storytelling
