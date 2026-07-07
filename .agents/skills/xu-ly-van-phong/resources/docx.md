# Kỹ năng DOCX — Word Document

Hướng dẫn tạo và thao tác file DOCX bằng Python và Node.js.

---

## Công cụ chính

| Công cụ | Ngôn ngữ | Dùng cho |
|---|---|---|
| `python-docx` | Python | Tạo DOCX từ đầu, format sau Pandoc |
| `docx` (docx-js) | Node.js | Tạo DOCX có thiết kế phức tạp (đề xuất, báo cáo) |
| Unpack/Pack XML | Python | Sửa sâu cấu trúc XML khi thư viện không đủ |

---

## Khi nào dùng gì

| Tình huống | Dùng |
|---|---|
| Tạo đề xuất / báo cáo đẹp | `docx-js` (Node.js) — kiểm soát pixel-perfect |
| Format sách sau Pandoc convert | `python-docx` — xem `scripts/format/` |
| Giữ nguyên format file mẫu, chỉ thay nội dung | Unpack/Pack XML — xem `office-xml.md` |
| Chuyển đổi MD → DOCX đơn giản | Pandoc — xem `convert.md` |

---

## python-docx: Các thao tác thường dùng

```python
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Page setup
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(3)
section.right_margin = Cm(2)

# Heading
doc.add_heading('Tiêu đề', level=1)

# Paragraph
p = doc.add_paragraph('Nội dung')
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Table
table = doc.add_table(rows=2, cols=3)
table.style = 'Light Grid Accent 1'

doc.save('output.docx')
```

---

## docx-js: Helpers chuẩn

```javascript
const { Document, Paragraph, TextRun, Table, TableRow, TableCell,
        WidthType, AlignmentType, BorderStyle, ShadingType,
        VerticalAlign, LevelFormat, PageNumber, Header, Footer,
        Packer } = require("docx");

// Helper functions
const run = (text, opts = {}) => new TextRun({
  text, font: opts.font || FONT, size: opts.size || SIZE_BODY,
  bold: opts.bold, italic: opts.italic, color: opts.color || COLOR_DARK,
});

const para = (text) => new Paragraph({
  children: [run(text)],
  spacing: { before: 0, after: 140, line: 340 },
  alignment: AlignmentType.JUSTIFIED,
});

const h1 = (num, title) => new Paragraph({
  children: [run(`${num}. ${title.toUpperCase()}`, {
    size: SIZE_H1, bold: true, color: COLOR_RED, caps: true
  })],
  spacing: { before: 360, after: 0, line: 320 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: COLOR_RED, space: 4 } },
});
```

**Hằng số chuẩn:** Xem bảng color tại `standards/color/`. Hằng số DXA:

```javascript
// xu-ly-van-phong skill (c) NDT-0904004920
const PAGE_WIDTH = 11906;   // A4
const PAGE_HEIGHT = 16838;
const MARGIN_LEFT = 1701;   // 3cm
const MARGIN_RIGHT = 1134;  // 2cm
const CONTENT_WIDTH = 9071; // PAGE_WIDTH - LEFT - RIGHT
```

---

## Quy tắc quan trọng

- **Bảng phải có `columnWidths`** và tổng = CONTENT_WIDTH. Cell `width` phải khớp.
- **Bullet dùng `LevelFormat.BULLET`**, không gõ tay ký tự `•`.
- **Font phải set trên mỗi TextRun** (hoặc default style) để tiếng Việt hiển thị đúng.
- **Tiêu chuẩn trình bày**: Đọc `standards/structure/` và `standards/color/` trước khi bắt tay code.

---

## Dependencies

```
pip install python-docx
npm install docx
```

<!-- NDT-0904004920 -->

