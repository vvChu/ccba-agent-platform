# Format Sách — Book

**Module:** publish/book
**Mục đích:** Format nội dung cho xuất bản dạng sách / tài liệu đào tạo dài.

---

## Heading Hierarchy

```
# Chương X. [Tên chương]              ← H1 (1 per chương)
## X.Y [Tên section]                  ← H2 (3-5 per chương)
**Tên mục con**                       ← Bold text (không dùng H3 trong thân văn)
```

**Quy tắc:**
- Viết hoa chữ đầu, KHÔNG Title Case
- X = số La Mã hoặc số Ả Rập (nhất quán toàn sách)
- Y = số thứ tự section trong chương

---

## Các khối format chuẩn

### Italic Summary (đầu chương)

```markdown
*[1-3 câu tóm tắt nội dung + bối cảnh chương. Luôn in nghiêng.]*
```

Vị trí: Ngay sau heading H1, trước nội dung chính.

### Disclaimer (tùy chọn)

```markdown
> *(Các sản phẩm được nhắc đến trong chương này nhằm minh họa cho
> [loại nội dung] tại thời điểm xuất bản ([thời điểm]). Tên sản phẩm
> có thể thay đổi nhưng [phương pháp/nguyên tắc] vẫn áp dụng.)*
```

Vị trí: Sau italic summary, trước section đầu tiên.

### Công thức hộp

```markdown
| 💡 **Công thức [Tên]:** |
| :--- |
| [Nội dung công thức] |
```

### RAC (cuối chương)

```markdown
---

**Recall – Apply – Create**

**(R)** [Câu hỏi nhớ lại]

**(A)** [Câu hỏi áp dụng]

**(C)** [Câu hỏi sáng tạo]
```

Vị trí: Cuối cùng của chương, sau dấu ngăn `---`.

### Lưu ý thuật ngữ (tùy chọn)

```markdown
> *Lưu ý về thuật ngữ: [giải thích quy ước thuật ngữ trong chương]*
```

---

## Section Break

- Giữa các section H2: **1 dòng trống** (không dùng `---`)
- Giữa các chương: **Page break** hoặc `---` + heading mới
- Trước RAC: luôn có `---`

---

## Checklist

- [ ] Heading hierarchy nhất quán (H1 → H2 → bold)?
- [ ] Italic summary đầu chương?
- [ ] Disclaimer đúng format (nếu có)?
- [ ] Công thức hộp đúng format (nếu có)?
- [ ] RAC cuối chương đúng format?
- [ ] Nội dung giữ nguyên 100% (chỉ format)?
