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

## CCBA Deep Seam (`ccba-ooxml`) & 5 Rào chắn Thực chiến

Tuân thủ **ADR-0061 (`TID251`)**: bên ngoài `packages/ccba-ooxml`, không tự viết wrapper `import docx` thô mà định tuyến qua các Deep Seam công khai của `ccba_ooxml`:

| Nhu cầu | Deep Seam `ccba_ooxml` chuẩn | Ghi chú |
|---|---|---|
| Dựng báo cáo đánh giá kỹ thuật chuẩn Brand v3.4 + RULE-6.1 | `TechnicalReportBuilder`, `build_tech_report_from_yaml`, `CCBADocxTheme` | CLI: `ccba-ooxml tech-report <spec.yaml>` |
| Điền form Word bảo toàn bố cục & chống vỡ trang | `WordFormFiller`, `FormFillConfig`, `TableRule` | Dual-Engine Word COM / LibreOffice |
| Thao tác DOM / comments / tracked changes & format NĐ 30 | `DocxDocument`, `CommentEngine`, `format_docx`, `convert_md_to_docx` | Giữ nguyên cấu trúc XML gốc khi cần |
| Xuất Vector PDF trên Windows / Linux | `docx_to_pdf` (`convert_to_pdf`) | Tự động tuyến `.docx` sang `Word.Application` trên `win32` |

### 5 Rào Chắn Biên Tập & Bố Cục Thực Chiến

1. **Tiêu đề tóm tắt tiếng Việt tự nhiên:** Dùng `TÓM TẮT BÁO CÁO / EXECUTIVE SUMMARY` (hoặc `TÓM TẮT ĐÁNH GIÁ`); tránh cụm dịch máy `"TÓM TẮT ĐIỀU HÀNH"`.
2. **Khối ký đối xứng nguyên tử (`4535 + 4536 = 9071 DXA`, `<w:cantSplit/>`):** Không lặp `contact_email` hay tên cơ quan vào ô chữ ký (email chỉ đặt tại Page 1 Document Control Matrix và Footer chạy trang); mỗi ô ký chỉ gồm Role Header VI/EN, `(Ký, ghi rõ họ tên)`, khoảng trống ký tươi, Họ tên, và Chức danh (`Giám đốc / Director`). Dòng tiêu đề phía trên bảng ký là tùy chọn (có thể bỏ qua nếu khách hàng ưa trình bày tối giản ngay dưới mục kết luận).
3. **Tuân thủ `RULE-6.1` & WCAG 2.1 (`#005A9C` vs `#0093DD`):** Header trang bìa tối đa 2 cấp (cấm `"Bộ Xây dựng"`, cấm đuôi `(IBST)`/`(CCBA)` trên dòng tiếng Việt), ghi `IBST - CCBA` không dùng dấu gạch chéo; dùng `#005A9C` cho chữ metric trên nền sáng thay cho cyan `#0093DD`.
4. **Visual QA Gate bắt buộc:** Xuất PDF qua `ccba_ooxml.docx_to_pdf`, render từng trang sang PNG và kiểm định trực quan: Page 1 không tràn sang trang 2, running header trang 2+ gọn 1 dòng, 0 heading mồ côi, khối ký không bị cắt đôi.
5. **Kiểm định hậu chỉnh tay Microsoft Word (Post-Manual-Word-Edit Hygiene):** Khi tệp `.docx` sinh tự động bị chỉnh sửa thủ công trên Word qua các lần hiệu đính (`Rev. N`), ưu tiên đồng bộ ngược nội dung vào YAML IR rồi tái sinh qua `TechnicalReportBuilder` (hoặc kiểm tra XML bắt buộc trước phát hành) để loại bỏ 4 thoái hóa thường gặp do Word lưu đè: (i) lệch phiên bản ở `word/header*.xml` so với Trang bìa; (ii) Word gỡ bỏ `<w:tblLayout w:val="fixed"/>` khiến bảng xô lệch độ rộng cột; (iii) hàng bảng thêm tay bị mất màu zebra xen kẽ; (iv) sót tên thư viện gốc trong `docProps/core.xml`. *Tiêu chí hoàn thành:* `word/header*.xml` khớp `Rev.` trên Trang bìa, 100% bảng giữ `<w:tblLayout w:val="fixed"/>` với tổng `gridCol = 9071 DXA` và `<w:cantSplit/>`, và `docProps/core.xml` ghi nhận tác giả `IBST - CCBA`.

---

## Dependencies

```
pip install python-docx
npm install docx
```

<!-- NDT-0904004920 -->

