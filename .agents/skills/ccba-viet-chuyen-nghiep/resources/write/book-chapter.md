# Viết Chương Sách — Book Chapter

**Module:** write/book-chapter
**Mục đích:** Viết nội dung dài >5.000 từ (chương sách, whitepaper, tài liệu đào tạo).
**Thay thế:** story-core.md + rhythm.md — KHÔNG dùng chung.

---

## 1. Kiến trúc chương

Mỗi chương sách tuân theo cấu trúc 5 phần:

```
┌─ Italic summary (1-3 câu, tóm tắt + bối cảnh)
├─ Disclaimer (nếu có sản phẩm/số liệu thay đổi)
├─ 3-5 section chính (H2: ## X.Y Tên section)
│   └── Mỗi section: mở → phát triển → ví dụ/tình huống → chuyển tiếp
├─ Bridge (đoạn cuối: tóm tắt + dẫn sang chương tiếp)
└─ RAC (Recall-Apply-Create: 3 câu hỏi cuối chương)
```

**Italic summary:**
```
*Khi đã có ngôn ngữ chung và mô hình tổng thể, doanh nghiệp cần một bản
đồ thực thi rõ ràng. Chương này vạch ra ba giai đoạn phát triển...*
```

**Anti-Obsolescence Disclaimer:**
```
> *(Các sản phẩm được nhắc đến trong chương này nhằm minh họa cho xu hướng
> tại thời điểm xuất bản (quý 1 năm 2026). Tên sản phẩm có thể thay đổi
> nhưng [phương pháp/kiến trúc/tiêu chuẩn] vẫn áp dụng.)*
```

**RAC cuối chương:**
```
**Recall – Apply – Create**

**(R)** [Câu hỏi nhớ lại khái niệm chính]

**(A)** [Câu hỏi áp dụng vào tình huống người đọc]

**(C)** [Câu hỏi sáng tạo/thiết kế dựa trên nội dung chương]
```

---

## 2. Mạch logic liên chương

### Recap-Build-Bridge

```
Chương N:
  Mở: Recap chương N-1 (1-2 câu, tự nhiên, không "Ở chương trước...")
  Thân: Build — nội dung mới
  Kết: Bridge sang chương N+1 (tóm tắt + "Chương tiếp theo sẽ...")
```

**Ví dụ recap:**
```
❌ "Ở chương trước, chúng ta đã tìm hiểu về IPO."
✅ "Phương pháp đã có, cách tổ chức đã có — nhưng phương pháp hay đến
    đâu cũng không tự chạy."
```

### Thuật ngữ nhất quán

Khái niệm định nghĩa ở chương nào → dùng đúng từ đó xuyên suốt. Khi tham chiếu:
```
✅ "Kiến trúc ba tầng (Chương V) xác định..."
✅ "...theo nguyên tắc module hóa đã trình bày."
```

---

## 3. Running Case Study

Dùng 1 nhân vật giả định xuyên suốt phần thực hành (nhiều chương liên tiếp).

```
Quy tắc:
  - Giới thiệu 1 lần: tên, chức vụ, bối cảnh doanh nghiệp
  - Mỗi chương: nhân vật thực hiện nội dung chương đó
  - Chỉ mô tả HÀNH ĐỘNG, không mô tả cảm xúc/suy nghĩ
  - Tên nhất quán (không "Minh" rồi "anh Minh" rồi "bạn Minh")
```

**Cấm:**
- Blockquote cảm xúc ("Minh thở phào nhẹ nhõm...")
- Internal monologue ("Minh tự hỏi liệu...")
- Khen ngợi nhân vật ("Minh rất thông minh khi...")

---

## 4. Cold Pedagogical Narrative

Giọng văn chuyên biệt cho sách giáo khoa/tài liệu đào tạo:

| Đặc điểm | Mô tả |
|-----------|-------|
| Tự tin | Khẳng định, không "có lẽ", "có thể" khi nói về phương pháp |
| Khách quan | Không xu nịnh người đọc, không "bạn thật tuyệt khi..." |
| Có narrative | Không khô khan — có ẩn dụ, có tình huống, có nhân vật |
| Cold | Không dùng dấu chấm than, không cảm thán, không blockquote cảm xúc |
| Hành động | Nhân vật chỉ qua hành động: "Minh mở Google Workspace..." |

**Khác với technical.md:**
- technical.md = academic, không narrative, không nhân vật
- book-chapter.md = cold nhưng compelling — CÓ narrative, CÓ nhân vật, CÓ ẩn dụ

---

## 5. Công thức hộp

→ Format chi tiết: xem `write/formula-box.md`

---

## 6. Kỹ thuật duy trì nhịp đọc

Chương dài >5.000 từ cần biến thiên nhịp:

```
Xen kẽ: Lý thuyết ↔ Ví dụ ↔ Tình huống nhân vật
Đoạn "thở": Câu đơn gãy gọn sau đoạn dài (1-2 câu, ngắt nhịp)
Question Bridge: Câu hỏi tu từ chuyển section thay vì heading cứng
  → "Vậy thiếu gì? Để trả lời câu hỏi này..."
In-line enumeration: "Một là... Hai là..." thay bullet points
  → ≥5 items hoặc inline ngắn: dùng (1), (2), (3)
```

---

## Workflow

1. **Lập outline (20 phút):** 3-5 section H2, mỗi section 2-3 ý chính
2. **Viết italic summary (5 phút):** 1-3 câu tóm tắt chương
3. **Viết từng section (30-45 phút/section):** mở → phát triển → ví dụ → chuyển
4. **Viết bridge + RAC (10 phút):** Tóm tắt + dẫn chương sau + 3 câu hỏi
5. **Review nhịp (15 phút):** Đọc lướt toàn chương, kiểm tra biến thiên

---

## Checklist

- [ ] Có italic summary đầu chương?
- [ ] Có disclaimer (nếu nội dung công nghệ)?
- [ ] 3-5 section H2 rõ ràng?
- [ ] Mạch logic liên chương: recap → build → bridge?
- [ ] Có RAC cuối chương?
- [ ] Running Case Study nhất quán (nếu có)?
- [ ] Giọng Cold Pedagogical — không cảm thán, không blockquote cảm xúc?
- [ ] Công thức hộp đúng format (nếu có)?
- [ ] Nhịp đọc biến thiên — không đều đặn?
