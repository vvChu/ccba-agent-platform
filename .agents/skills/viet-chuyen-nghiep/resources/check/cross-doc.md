# Kiểm Tra Nhất Quán Liên Tài Liệu — Cross-Doc

**Module:** check/cross-doc
**Mục đích:** Đảm bảo nhất quán giữa nhiều chương/file trong cùng dự án.

---

## Khi nào kích hoạt

- Review tài liệu ≥ 2 file/chương liên quan
- Review sách (nhiều chương)
- Kiểm tra nhất quán toàn bộ dự án viết

---

## 6 Tiêu chí kiểm tra

### 1. Thuật ngữ (Terminology Consistency)

Cùng khái niệm → cùng từ tiếng Việt, cùng (*English*).

```
Công cụ: Lập bảng glossary, grep_search tìm biến thể
Ví dụ lỗi:
  Ch.III: "tác vụ" | Ch.VII: "nhiệm vụ" | Ch.IX: "công việc"
  → Chọn 1 từ, sửa toàn bộ
```

**Quy tắc giới thiệu thuật ngữ:**
- Lần đầu: Tiếng Việt (*English*) — giải thích ngắn
- Các lần sau: Tiếng Việt hoặc acronym đã giới thiệu
- KHÔNG đổi cách gọi giữa các chương

### 2. Tham chiếu chéo (Cross-Reference)

Mỗi "Chương X đã..." hoặc "(Chương Y)" → verify đúng nội dung.

```
Công cụ: Tìm pattern "Chương [IVX]" hoặc "chương [0-9]" → đọc chương được tham chiếu
Ví dụ lỗi:
  Ch.VII viết "Chương V đã giới thiệu KWSR" → thực tế KWSR ở Ch.III
```

### 3. Case Study / Nhân vật (Character Consistency)

Tên, chức vụ, bối cảnh doanh nghiệp nhất quán xuyên suốt.

```
Công cụ: grep_search tên nhân vật → kiểm tra
Ví dụ lỗi:
  Ch.V: "Minh, phó phòng kinh doanh" | Ch.VIII: "Minh, trưởng phòng"
  → Sửa cho nhất quán
```

### 4. Format (Pattern Consistency)

Các pattern lặp lại phải đồng dạng xuyên suốt.

| Pattern | Kiểm tra |
|---------|----------|
| Công thức hộp | `💡 **Công thức [Tên]:**` — cùng format bảng? |
| Disclaimer | Blockquote italic — cùng cấu trúc câu? |
| RAC | `**(R)** ... **(A)** ... **(C)**` — cùng format? |
| Heading | `## X.Y Tên` — X = số chương, Y = số section? |

### 5. Tone (Tonal Consistency)

Cho phép biến thiên nhẹ giữa các chương nhưng không nhảy cực đoan.

```
Chấp nhận: Ch.I lý luận lạnh → Ch.X ẩn dụ nhiều hơn
Không chấp nhận: Ch.V chuyên nghiệp → Ch.VI bỗng dùng "bạn ơi 😊"
```

### 6. Heading / Đánh số (Numbering Consistency)

```
Chuẩn: ## 4.1, ## 4.2, ## 4.3 (chapter.section)
Lỗi phổ biến: ## 4.1 → ## 4.3 (nhảy số), hoặc ## Bốn-Một (không nhất quán)
```

---

## Workflow

1. **Lập glossary (10 phút):** Liệt kê thuật ngữ chính → kiểm tra nhất quán
2. **Grep tham chiếu (5 phút):** Tìm "Chương" → verify từng cái
3. **Grep nhân vật (5 phút):** Tìm tên riêng → kiểm tra nhất quán
4. **Kiểm tra format (10 phút):** So sánh pattern giữa các chương
5. **Đọc lướt tone (5 phút):** Đọc đoạn mở + đoạn kết mỗi chương

---

## Checklist

- [ ] Thuật ngữ nhất quán toàn bộ (glossary kiểm tra)?
- [ ] Tham chiếu chéo đúng (Chương X → verify)?
- [ ] Nhân vật / case study nhất quán?
- [ ] Format công thức hộp / disclaimer / RAC đồng dạng?
- [ ] Tone không nhảy cực đoan giữa các chương?
- [ ] Heading đánh số tuần tự, không nhảy?
