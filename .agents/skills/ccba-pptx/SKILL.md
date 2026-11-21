---
name: ccba-pptx
description: Công cụ tạo và chỉnh sửa file trình chiếu PowerPoint (.pptx) nâng cao
  bằng HTML conversion hoặc OOXML.
role: sub_skill
master_skill: ccba-xu-ly-van-phong
disable-model-invocation: true
user-invocable: true
command: /ccba-pptx
when_to_use: Invoke for presentation deck creation, edits, or extraction.
category: multimedia
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
keywords:
- ccba-pptx
- powerpoint
- slides
- office
license: Proprietary. LICENSE.txt has complete terms
metadata:
  author: CCBA
  version: 1.1.0
bundle: _core
scope: universal
posture: seam-exempt
tier: kernel
triggers:
- ccba-pptx
- powerpoint
- slides
- office
- slide
- create slide
- html2pptx
- slide layout
---
# PPTX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .pptx file. A .pptx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

---

## Reading and analyzing content

### Text extraction
If you just need to read the text contents of a presentation, you should convert the document to markdown:

```bash
# Convert document to markdown
python -m markitdown path-to-file.pptx
```

### Raw XML access
You need raw XML access for: comments, speaker notes, slide layouts, animations, design elements, and complex formatting. For any of these features, you'll need to unpack a presentation and read its raw XML contents.

#### Unpacking a file
`python -m ccba_ooxml unpack <office_file> <output_dir>`

**Note**: Unpacking is provided by the `ccba-ooxml` package via `python -m ccba_ooxml unpack`.

#### Key file structures
* `ppt/presentation.xml` - Main presentation metadata and slide references
* `ppt/slides/slide{N}.xml` - Individual slide contents (slide1.xml, slide2.xml, etc.)
* `ppt/notesSlides/notesSlide{N}.xml` - Speaker notes for each slide
* `ppt/comments/modernComment_*.xml` - Comments for specific slides
* `ppt/slideLayouts/` - Layout templates for slides
* `ppt/slideMasters/` - Master slide templates
* `ppt/theme/` - Theme and styling information
* `ppt/media/` - Images and other media files

#### Typography and color extraction
**When given an example design to emulate**: Always analyze the presentation's typography and colors first using the methods below:
1. **Read theme file**: Check `ppt/theme/theme1.xml` for colors (`<a:clrScheme>`) and fonts (`<a:fontScheme>`)
2. **Sample slide content**: Examine `ppt/slides/slide1.xml` for actual font usage (`<a:rPr>`) and colors
3. **Search for patterns**: Use Select-String (PowerShell) or git grep to find color (`<a:solidFill>`, `<a:srgbClr>`) and font references across all XML files

## Creating a new PowerPoint presentation **without a template**

When creating a new PowerPoint presentation from scratch, use the **html2pptx** workflow to convert HTML slides to PowerPoint with accurate positioning.

### Design Principles

**CRITICAL**: Before creating any presentation, analyze the content and choose appropriate design elements:
1. **Consider the subject matter**: What is this presentation about? What tone, industry, or mood does it suggest?
2. **Check for branding**: If the user mentions a company/organization, consider their brand colors and identity
3. **Match palette to content**: Select colors that reflect the subject
4. **State your approach**: Explain your design choices before writing code

**Requirements & Layout Rules**:
- State your content-informed design approach before writing code; pick 3-5 topic-matched colors with high contrast and use web-safe fonts only (`Arial`, `Helvetica`, `Times New Roman`, `Georgia`, `Courier New`, `Verdana`, `Tahoma`, `Trebuchet MS`, `Impact`).
- For charts/tables, use a full-slide layout or a two-column layout (`40%/60%`); never vertically stack charts/tables under text in a single column. See `references/design_palettes_and_templates.md` for 18 curated palettes and styling options.

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`html2pptx.md`](references/html2pptx.md) completely from start to finish with no range limits before presentation creation.
   **Completion Criterion:** Việc đọc toàn bộ file `html2pptx.md` được ghi nhận rõ ràng trong nhật ký suy nghĩ (thought trace) của Agent.
2. Create an HTML file per slide (`720pt × 405pt` for 16:9) using `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`, `class="placeholder"` for chart/table slots, and Sharp-rasterized PNGs for gradients/icons.
   **Completion Criterion:** Các file HTML slide được ghi xuống đĩa thành công và chứa đúng cấu trúc thẻ quy định.
3. Convert slides with [`html2pptx.js`](scripts/html2pptx.js), add PptxGenJS charts/tables into placeholders, and save via `pptx.writeFile()`.
   **Completion Criterion:** Script chạy thành công và tạo ra file `.pptx` tại đường dẫn chỉ định.
4. **Visual validation**: Run `python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4` and inspect thumbnails for text cutoff, overlap, margin issues, or contrast bugs; iterate until clean.
   **Completion Criterion:** File hình ảnh lưới thumbnail (`thumbnails.jpg`) được tạo thành công và Agent xác nhận không có lỗi hiển thị (overlap, cutoff, contrast).

## Editing an existing PowerPoint presentation

Use OOXML directly when modifying existing decks:
1. **MANDATORY - READ ENTIRE FILE**: Read [`ooxml.md`](references/ooxml.md) completely without range limits before editing.
   **Completion Criterion:** Việc đọc toàn bộ file `ooxml.md` được ghi nhận rõ ràng trong nhật ký suy nghĩ (thought trace) của Agent.
2. Unpack: `python -m ccba_ooxml unpack <office_file> <output_dir>`
   **Completion Criterion:** Thư mục `<output_dir>` được tạo và chứa các tệp tin XML của slide (ví dụ `ppt/slides/slide1.xml`).
3. Edit slide/related XML (`ppt/slides/slide{N}.xml`).
   **Completion Criterion:** Các sửa đổi XML được lưu lại thành công và đúng thẻ cú pháp OOXML.
4. Validate after every edit: `python -m ccba_ooxml validate <dir> --original <file>`
   **Completion Criterion:** Lệnh validate chạy thành công và không phát hiện lỗi cấu trúc XML.
5. Repack: `python -m ccba_ooxml pack <input_directory> <office_file>`
   **Completion Criterion:** File `.pptx` được đóng gói lại thành công từ thư mục tạm và không bị lỗi định dạng khi mở.

## Creating a new PowerPoint presentation **using a template**

### Workflow
1. Extract text (`python -m markitdown template.pptx > template-content.md`, read in full) and generate thumbnails (`python scripts/thumbnail.py template.pptx`).
   **Completion Criterion:** File văn bản `template-content.md` và tệp hình ảnh lưới thumbnail (`thumbnails.jpg`) được tạo thành công.
2. Visually analyze thumbnails and write a 0-indexed `template-inventory.md` listing every slide layout and image placeholder.
   **Completion Criterion:** File phân tích `template-inventory.md` được lưu trữ thành công và chứa đầy đủ danh mục slide 0-indexed.
3. Author `outline.md` with exact content-to-placeholder mapping (`1/2/3`-column layouts match exact item count; quote layouts only for real quotes; `template_mapping` indices within bounds).
   **Completion Criterion:** File dàn ý `outline.md` được tạo chứa bản đồ ánh xạ `template_mapping` hợp lệ (chỉ số nằm trong dải slides khả dụng).
4. Duplicate/reorder/delete slides via `python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52`.
   **Completion Criterion:** Lệnh rearrange tạo ra file `working.pptx` thành công với số slide và thứ tự khớp với bản đồ ánh xạ.
5. Extract all shapes via `python scripts/inventory.py working.pptx text-inventory.json` and read the entire JSON file without range limits.
   **Completion Criterion:** File dữ liệu `text-inventory.json` được trích xuất thành công và chứa đầy đủ cấu trúc của slide đích.
6. Author `replacement-text.json` with valid `"paragraphs"` objects (any inventory shape without `"paragraphs"` is cleared; `"bullet": true` requires `"level": 0+` without literal bullet chars or `"alignment"` — schema details in `references/design_palettes_and_templates.md`).
   **Completion Criterion:** File cấu hình thay thế `replacement-text.json` được tạo thành công và chứa đúng định dạng `paragraphs`.
7. Apply and verify overflow/shape errors: `python scripts/replace.py working.pptx replacement-text.json output.pptx`.
   **Completion Criterion:** File `output.pptx` được ghi thành công, Agent chạy xác minh không có lỗi XML hay lỗi tràn ô (overflow).

## Thumbnails, Image Conversion & Dependencies

- **Thumbnails & Slide-to-Image:** `python scripts/thumbnail.py template.pptx [prefix] --cols 4` (3-6 cols) or `soffice --headless --convert-to pdf template.pptx && pdftoppm -jpeg -r 150 template.pdf slide`.
- **Code Style:** Write concise PPTX scripts without verbose variables or debug print noise.
- **Dependencies:** `markitdown[pptx]`, `pptxgenjs`, `playwright`, `react-icons`, `sharp`, `LibreOffice`, `Poppler` (`pdftoppm`), `defusedxml`.

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/html2pptx.md` | Quy trình chuyển đổi HTML/CSS sang PPTX qua pptxgenjs và playwright |
| `references/ooxml.md` | Cấu trúc định dạng OpenXML (.pptx) và chỉnh sửa trực tiếp XML của slide |
| `references/design_palettes_and_templates.md` | Bộ 18 bảng màu thiết kế, chi tiết styling hình khối/chart, lược đồ `text-inventory.json` & `replacement-text.json`, và tùy chọn thumbnail/PDF |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
