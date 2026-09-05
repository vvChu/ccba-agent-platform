# Kỹ năng PPTX — PowerPoint

Hướng dẫn đọc, tạo và kiểm tra slide.

---

## Đọc nội dung

```bash
python -m markitdown presentation.pptx     # Text extraction
python scripts/office/unpack.py presentation.pptx unpacked/  # Raw XML
```

---

## Tạo slide

| Tình huống | Dùng |
|---|---|
| Có template/file mẫu | Unpack → sửa XML → Pack (xem `office-xml.md`) |
| Tạo từ đầu | `pptxgenjs` (Node.js): `npm install -g pptxgenjs` |

---

## Nguyên tắc thiết kế

- **Mỗi slide cần ít nhất 1 yếu tố thị giác** (image, chart, icon, shape). Slide chỉ text là điều không chấp nhận.
- **Chọn font pairing có cá tính**, không default Arial:

| Header | Body |
|---|---|
| Georgia | Calibri |
| Arial Black | Arial |
| Cambria | Calibri |
| Impact | Arial |

- **Cỡ chữ:** Title 36-44pt, section 20-24pt, body 14-16pt, caption 10-12pt.
- **Margin tối thiểu 0.5"**, gap giữa content blocks 0.3-0.5".
- **Không lặp layout** — vary columns, cards, callouts qua các slide.
- **KHÔNG dùng accent line dưới title** — dấu hiệu slide AI tạo.

---

## Layout options

- Two-column (text + illustration)
- Icon + text rows (icon trong circle màu)
- 2x2 / 2x3 grid
- Half-bleed image + content overlay
- Large stat callouts (số lớn 60-72pt + label nhỏ)
- Timeline / process flow

---

## QA bắt buộc

```bash
# Content check
python -m markitdown output.pptx

# Visual check - convert to images
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

Kiểm tra: overlap, text overflow, contrast thấp, spacing không đều, placeholder text còn sót.

**Verification loop:** Generate → Convert → Inspect → Fix → Re-verify. Không declare success trước khi hoàn thành ít nhất 1 fix-and-verify cycle.

---

## Bảng màu

Xem `standards/color/slide-palettes.md` cho 10 bộ màu gợi ý.

---

## Dependencies

```
pip install "markitdown[pptx]" Pillow
npm install -g pptxgenjs
```
