# Kỹ thuật Office XML — Unpack / Pack / Clone

Kỹ thuật bóc tách file Office thành XML để sửa sâu cấu trúc mà thư viện Python không với tới.

---

## Khi nào dùng

- User đưa file mẫu và muốn **giữ nguyên format**, chỉ thay nội dung
- Cần sửa numbering, styles, hoặc cấu trúc phức tạp mà python-docx không hỗ trợ
- Cần xử lý Track Changes / Redlining

---

## Quy trình 3 bước

### 1. Unpack (giải nén thành XML)

```bash
python scripts/office/unpack.py path/to/file.docx unpacked_dir/
```

Kết quả: `unpacked_dir/word/document.xml` (Word) hoặc `unpacked_dir/ppt/slides/slide1.xml` (Slide).

### 2. Sửa nội dung XML

Cấu trúc XML của Word:
- `<w:rPr>` — Định dạng (font, size, bold). **CẤM ĐỤNG CHẠM!**
- `<w:t>` — Văn bản thô. Chỉ thay nội dung text ở đây.

**Auto-Clone Script:**

```bash
python scripts/office/clone_text.py "unpacked_dir/word/document.xml" --map "mapping.json"
```

Trong đó `mapping.json` = `{ "Chữ Cũ": "Chữ Mới" }`.

### 3. Pack (đóng gói lại)

```bash
python scripts/office/pack.py unpacked_dir/ output.docx
```

---

## Validation

```bash
python scripts/office/validate.py output.docx
```

Kiểm tra XML hợp lệ trước khi đóng gói. Schemas XSD nằm tại `scripts/office/schemas/`.

---

## Cảnh báo

- Không dùng RegEx để xóa bừa bãi XML. Chỉ replace text thực tế nhìn thấy.
- Không sửa thẻ `<w:rPr>` — sẽ phá vỡ format gốc.
- Ký tự đặc biệt trong XML: dùng `&#x201C;` thay cho ngoặc kép.

---

## Công cụ bổ sung

| Script | Mục đích |
|---|---|
| `scripts/office/soffice.py` | Chuyển đổi format qua LibreOffice headless |
| `scripts/office/helpers/merge_runs.py` | Gộp runs bị tách trong XML |
| `scripts/office/helpers/simplify_redlines.py` | Đơn giản hóa Track Changes |
| `scripts/office/validators/` | Validate DOCX, PPTX, Redlining |

<!-- NDT-0904004920 -->
