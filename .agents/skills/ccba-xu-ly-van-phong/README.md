# 📎 xu-ly-van-phong — Skill xử lý văn phòng cho Antigravity / Claude

**Tạo file Word, Excel, Slide, PDF chuyên nghiệp — có sẵn tiêu chuẩn trình bày và bộ phối màu.**

> Thay vì để AI tự ý chọn font, cỡ chữ, spacing mỗi lần khác nhau, skill này cung cấp một bộ quy chuẩn trình bày nhất quán. AI Agent đọc tiêu chuẩn trước khi tạo file → mọi output đều đồng nhất và chuyên nghiệp.

---

## Tại sao cần skill này?

Khi bạn yêu cầu AI "tạo file Word", kết quả thường:
- Font tùy hứng (lúc Arial, lúc Calibri)
- Heading không nhất quán
- Bảng trắng toàn text, không phối màu
- Excel không có công thức sống
- Slide chỉ text trắng nền trắng

**xu-ly-van-phong** giải quyết bằng kiến trúc **composable**:

```
Output = Cấu trúc (bắt buộc) × Phối màu (tùy chọn)
```

Mặc định xuất đen trắng chuẩn. Khi cần đẹp, gắn thêm 1 bộ phối màu — tách biệt hoàn toàn.

---

## Tính năng chính

### 📄 Word (DOCX)
- 9 tiêu chuẩn cấu trúc: khổ giấy, typography, heading, bullet, bảng, bìa, header/footer, caption, khối đặc biệt
- 4 bộ phối màu: Formal Navy, Modern Blue, Editorial Burgundy, Technical Multicolor
- 9 mẫu văn bản hành chính NĐ 30: công văn, quyết định, tờ trình, báo cáo...
- Kỹ thuật Unpack/Pack XML: giữ nguyên format file mẫu, chỉ thay nội dung

### 📊 Excel (XLSX)
- Cấu trúc multi-sheet chuẩn: README → Data → Metadata → Nhật ký
- Phân cấp dữ liệu bằng fill + font + bold (không dùng indent)
- 3 bộ phối màu: Professional Dark, Corporate Green, Blue Corporate
- Traffic Light: OK (xanh) / Warning (cam) / Error (đỏ)

### 📽️ PowerPoint (PPTX)
- 7 layout patterns: Two-column, Icon grid, Stat callout, Timeline...
- 10 bộ phối màu slide
- Font pairing gợi ý

### 📑 PDF
- Phân biệt PDF digital (script tự động) vs PDF scan (AI Vision)
- Pipeline: PDF → DOCX, MD → DOCX → PDF

### 🔧 Kỹ thuật nâng cao
- Unpack/Pack XML: bóc file Office ra XML, sửa, đóng lại — giữ 100% format gốc
- Pandoc convert: MD → DOCX với post-processing tự động
- LibreOffice headless: chuyển đổi hàng loạt

---

## Cài đặt

### Bước 1: Tải skill

Tải về và giải nén vào thư mục skills của Antigravity:

```
C:\Users\<username>\.gemini\antigravity\skills\xu-ly-van-phong\
```

Hoặc trên macOS/Linux:
```
~/.gemini/antigravity/skills/xu-ly-van-phong/
```

### Bước 2: Cài dependencies

```bash
pip install python-docx openpyxl pypdf pdfplumber pdf2docx
```

Pandoc (tùy chọn, cho convert MD → DOCX):
```bash
# Windows
choco install pandoc
# macOS
brew install pandoc
```

LibreOffice (tùy chọn, cho convert DOCX → PDF):
```bash
# Windows: tải từ libreoffice.org
# macOS
brew install --cask libreoffice
```

### Bước 3: Xác nhận

Hỏi Claude/Antigravity: *"Tạo file word báo cáo tiến độ dự án"* — nếu AI trả lời có tham chiếu đến tiêu chuẩn trình bày, skill đã hoạt động.

---

## Cách sử dụng

### Prompt cơ bản

| Bạn nói | AI làm gì |
|---|---|
| *"Soạn công văn gửi Sở Xây dựng"* | Đọc `nd30.md` + template `docx-hanh-chinh-cong-van.md` → xuất DOCX chuẩn NĐ 30 |
| *"Tạo file Excel theo dõi tiến độ dự án"* | Đọc `xlsx-structure.md` + palette X2 → xuất XLSX multi-sheet |
| *"Làm đề xuất gửi Ban TGĐ"* | Đọc structure + `docx-formal-navy.md` → xuất DOCX có bìa, heading phối màu |
| *"Chuyển file MD này sang Word"* | Chạy Pandoc → post-process theo `docx-typography.md` |
| *"Bắt chước format file này, thay nội dung"* | Unpack XML → clone structure → thay text → Pack lại |
| *"Làm slide thuyết trình"* | Đọc `pptx-structure.md` + palette → xuất PPTX |

### Prompt nâng cao

```
Tạo bảng tính Excel dự toán xây dựng:
- Sheet 1: Danh mục công tác (phân cấp CHƯƠNG → CTAC → CHITIET)
- Sheet 2: Thống kê thép theo đường kính
- Sheet 3: Metadata dự án
- Dùng palette Professional Dark
```

```
Tạo đề xuất chiến lược triển khai AI cho doanh nghiệp:
- Format: Word, có trang bìa
- Palette: Formal Navy
- Nội dung: 4 chương (bối cảnh, giải pháp, ngân sách, kết luận)
- Có bảng so sánh trước/sau
```

---

## Cấu trúc thư mục

```
xu-ly-van-phong/
├── SKILL.md                          ← Entry point, AI đọc file này đầu tiên
├── resources/                        ← Tầng 1: Kỹ năng kỹ thuật
│   ├── docx.md                       ← Cách dùng python-docx / docx-js
│   ├── xlsx.md                       ← Cách dùng openpyxl
│   ├── pptx.md                       ← Cách dùng pptxgenjs
│   ├── pdf.md                        ← Xử lý PDF cục bộ
│   ├── office-xml.md                 ← Kỹ thuật Unpack/Pack XML
│   └── convert.md                    ← Pipeline chuyển đổi
├── standards/                        ← Tầng 2: Tiêu chuẩn trình bày
│   ├── structure/                    ← Cấu trúc (đen trắng mặc định)
│   │   ├── docx-page-setup.md
│   │   ├── docx-typography.md
│   │   ├── docx-heading-numbering.md
│   │   ├── docx-list-bullet.md
│   │   ├── docx-table.md
│   │   ├── docx-cover-page.md
│   │   ├── docx-header-footer.md
│   │   ├── docx-caption-reference.md
│   │   ├── docx-special-blocks.md
│   │   ├── xlsx-structure.md
│   │   └── pptx-structure.md
│   ├── color/                        ← Phối màu (optional)
│   │   ├── docx-formal-navy.md
│   │   ├── docx-modern-blue.md
│   │   ├── docx-editorial-burgundy.md
│   │   ├── docx-technical-multicolor.md
│   │   ├── xlsx-palettes.md
│   │   └── pptx-palettes.md
│   └── nd30.md                       ← Quy chuẩn VB hành chính
├── scripts/                          ← Tầng 3: Automation
│   ├── office/                       ← Unpack/Pack/Clone XML
│   ├── convert/                      ← MD→DOCX, PDF→DOCX
│   └── format/                       ← Post-process DOCX
├── templates/                        ← Tầng 4: Mẫu nội dung
│   ├── docx-hanh-chinh-*.md          ← 9 mẫu NĐ 30
│   └── docx-de-xuat-*.md             ← Mẫu đề xuất
└── examples/                         ← File output minh họa
    ├── docx-de-xuat-formal-navy.docx
    └── xlsx-ke-hoach-5w1h.xlsx
```

---

## Nguyên tắc thiết kế

1. **Composable**: Cấu trúc và màu sắc tách biệt hoàn toàn → dùng lại linh hoạt
2. **Default đen trắng**: Không ép màu khi không cần → phù hợp văn bản hành chính
3. **Prefix rõ ràng**: Tên file bắt đầu bằng `docx-`, `xlsx-`, `pptx-` → biết ngay dùng cho gì
4. **Live Formula**: Mọi ô tính toán trong Excel phải dùng công thức sống, không hardcode
5. **Xử lý cục bộ**: Không upload file lên cloud — tất cả chạy trên máy

---

## Tác giả

**Nguyễn Duy Tùng**
Tư vấn xây dựng Song sinh số Doanh nghiệp (EDT) & Lực lượng Lao động AI (AI Workforce)

📞 0904.004.920

---

*Skill này là thành phần của hệ sinh thái [Google Antigravity](https://cad2map.web.app) — bộ công cụ AI Agent dành cho doanh nghiệp Việt Nam.*
