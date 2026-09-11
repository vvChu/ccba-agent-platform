---
name: ccba-xu-ly-van-phong
description: Tạo, sửa, chuyển đổi file văn phòng (Word, Excel, Slide, PDF) theo tiêu
  chuẩn cấu trúc & phối màu chuyên nghiệp hoặc Nghị định 30.
role: master_skill
package_path: packages/ccba-ooxml
sub_skills:
- ccba-pptx
- ccba-markdown-document-processing
disable-model-invocation: true
bundle: _software
tier: kernel
user-invocable: true
command: /ccba-xu-ly-van-phong
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- ccba-xu-ly-van-phong
- xử lý văn phòng
- word
- excel
- ccba-pptx
- pdf
- pdf to docx
- office
- ccba-docx
- docx
---

# Xử lý Văn phòng

Skill xử lý mọi thao tác với file văn phòng. Được tổ chức theo kiến trúc **composable 4 tầng**:

```
Output = Structure × Color (optional)
```

Mặc định mọi văn bản xuất ra đen trắng. Khi cần trình bày đẹp, gắn thêm bộ phối màu từ Tầng 2.

---

## Tầng 1 — Kỹ năng phổ quát (`resources/`)

Cách dùng tool, thư viện, quy trình kỹ thuật. Đọc file phù hợp với loại file cần xử lý:

| File | Dùng cho |
|---|---|
| `resources/docx.md` | Tạo/sửa DOCX bằng python-docx hoặc docx-js |
| `resources/xlsx.md` | Tạo/sửa Excel bằng openpyxl. Nguyên tắc: Live Formula, không hardcode |
| `resources/pptx.md` | Tạo/sửa Slide bằng pptxgenjs. Nguyên tắc: không slide thuần text |
| `resources/pdf.md` | Xử lý PDF cục bộ. Phân biệt PDF digital vs PDF scan |
| `resources/office-xml.md` | Kỹ thuật Unpack/Pack XML — giữ nguyên format file mẫu, chỉ thay nội dung |
| `resources/convert.md` | Pipeline chuyển đổi: MD→DOCX, PDF→DOCX, DOCX→PDF |

---

## Tầng 2 — Tiêu chuẩn trình bày (`standards/`)

### Cấu trúc (`standards/structure/`)

Quy chuẩn bố cục, đen trắng mặc định. Đọc theo nhu cầu:

| File | Nội dung |
|---|---|
| `structure/docx-page-setup.md` | Khổ giấy, margin, line spacing theo loại VB |
| `structure/docx-typography.md` | Font family, cỡ chữ, weight |
| `structure/docx-heading-numbering.md` | Hệ 5 cấp (VB ngắn) và 9 cấp (VB dài) |
| `structure/docx-list-bullet.md` | Bullet, numbered list, indent, điều cấm |
| `structure/docx-table.md` | 5 mẫu bảng: lộ trình, traffic light, zebra, matrix, số liệu |
| `structure/docx-cover-page.md` | Trang bìa: VB ngắn vs VB dài |
| `structure/docx-header-footer.md` | Header/footer, đánh số trang, header 2 cột NĐ 30 |
| `structure/docx-caption-reference.md` | Caption bảng/hình, trích dẫn nguồn (chủ yếu VB dài) |
| `structure/docx-special-blocks.md` | Code block, callout, divider, signature, công thức toán |
| `structure/xlsx-structure.md` | Bố cục bảng tính: multi-sheet, phân cấp row, column width, dòng tổng |
| `structure/pptx-structure.md` | Bố cục slide: layout patterns, font pairing, phân cấp thông tin |

### Phối màu (`standards/color/`) — optional

Gắn thêm khi cần trình bày đẹp. Mỗi bộ là một "skin" độc lập:

| File | Tông | Dùng cho |
|---|---|---|
| `color/docx-formal-navy.md` | Trang trọng | DOCX đề xuất cấp chiến lược, tập đoàn |
| `color/docx-modern-blue.md` | Hiện đại | DOCX startup, SME |
| `color/docx-editorial-burgundy.md` | Editorial | DOCX review, phản biện |
| `color/docx-technical-multicolor.md` | Kỹ thuật | DOCX dài, heading phân cấp bằng màu |
| `color/xlsx-palettes.md` | 3 bộ XLSX | Bảng tính: Dark, Green, Blue + Traffic Light |
| `color/pptx-palettes.md` | 10 bộ PPTX | Slide thuyết trình |

### NĐ 30 (`standards/nd30.md`)

Quy chuẩn quốc gia cho văn bản hành chính. Bao gồm cả cấu trúc lẫn format — là trường hợp đặc biệt không tách.

---

## Tầng 3 — Scripts (`scripts/`)

| Thư mục | Nội dung |
|---|---|
| `scripts/office/` | Toolkit XML: unpack, pack, clone_text, validate, soffice, helpers |
| `scripts/convert/` | convert_md_to_docx.py, convert_pdf_to_docx.py |
| `scripts/format/` | format_docx.py (post-process DOCX sau Pandoc) |

---

## Tầng 4 — Templates & Examples

Templates (mẫu khung nội dung) và Examples (file output tham chiếu) dùng prefix để nhận diện format:

| File | Mô tả |
|---|---|
| `templates/docx-hanh-chinh-*.md` | 9 mẫu VB hành chính NĐ 30 (công văn, quyết định, tờ trình...) |
| `templates/docx-de-xuat-*.md` | Mẫu đề xuất/báo cáo |
| `examples/docx-bao-cao-formal-navy.docx` | DOCX báo cáo — palette Formal Navy |
| `examples/docx-cong-van-nd30.docx` | DOCX công văn — chuẩn NĐ 30 |
| `examples/xlsx-bao-cao-tien-do.xlsx` | Excel tracking — palette X2 Corporate Green |
| `examples/xlsx-data-block.xlsx` | Excel data block — palette X1 Professional Dark |

---

## Bảng composable — Agent chọn file theo tình huống

| Tình huống | Structure | Color | Kỹ năng |
|---|---|---|---|
| Công văn NĐ 30 | `nd30.md` | Không (đen trắng) | `docx.md` |
| Đề xuất sang trọng | `page-setup` + `heading` + `table` + `cover-page` | `formal-navy.md` | `docx.md` |
| Thuyết minh kỹ thuật | `page-setup` + `heading` (9 cấp) + `caption-reference` | `technical-multicolor.md` | `docx.md` |
| Báo cáo nội bộ nhanh | `page-setup` + `heading` + `table` | Không (đen trắng) | `docx.md` |
| Bảng tính tracking | `table.md` | Không hoặc tùy chọn | `xlsx.md` |
| Slide pitch deck | — | `slide-palettes.md` | `pptx.md` |
| PDF scan → DOCX | Phân tích cấu trúc gốc | Phân tích màu gốc | `pdf.md` + `docx.md` |
| PDF digital → DOCX | — | — | `convert.md` |
| Giữ format file mẫu | — | — | `office-xml.md` |

---

## Nguyên tắc tuân thủ

- **Về format:** Đọc `standards/` trước khi tạo file. Không tự ý chọn font, cỡ chữ, spacing.
- **Về Excel:** Mọi ô tính toán phải dùng công thức sống.
- **Về Slide:** Không chấp nhận slide chỉ text trắng nền trắng.
- **Về màu sắc:** Mọi tổ hợp text/background phải đạt contrast WCAG.
- **Về Word khi user không nói rõ:** Hỏi trước — sự khác biệt giữa NĐ 30 và đề xuất doanh nghiệp là rất lớn.

## Không được phép

- Không tạo file mà không tham khảo standards.
- Không hardcode kết quả tính toán vào Excel.
- Không upload PDF lên cloud.
- Không dùng python-docx khi user muốn giữ format file mẫu — dùng Unpack/Pack XML.
- Không trộn format NĐ 30 với format đề xuất doanh nghiệp.

---

## Tác giả

**Nguyễn Duy Tùng**
Tư vấn xây dựng Song sinh số Doanh nghiệp (EDT) & Lực lượng Lao động AI (AI Workforce)
Liên hệ: 0904.004.920


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/docx_engine_guide.md` | Hướng dẫn chi tiết chèn nhận xét (comments) và theo dõi thay đổi (tracked changes) trong tài liệu Word |

