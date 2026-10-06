---
name: ccba-completion-checklist
description: Tạo và duy trì Danh Mục Hồ Sơ Hoàn Thành Công Trình theo VBPL hiện hành.
  Hỗ trợ xuất Markdown và Word (.docx).
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _consulting
tier: kernel
command: /ccba-completion-checklist
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 4.0
  p: 1.0
triggers:
- hồ sơ hoàn thành
- HSHT
- completion
- checklist
- danh mục hồ sơ
- nghiệm thu
- hoàn công
---
# Completion Checklist Generator

Skill hỗ trợ tạo và duy trì **Danh Mục Hồ Sơ Hoàn Thành Công Trình** (Construction Completion Document Checklist) theo quy định VBPL hiện hành, phục vụ kỹ sư giám sát tại CCBA.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`compose-existing`**, hợp thành từ các Seam và engine quản trị nền tảng:
* **Căn Cứ Pháp Lý & Tra Cứu:** Trích xuất và đối soát căn cứ nghiệm thu qua Deep Seam `LegalKnowledgeEngine` (CLI `python -m ccba_legal query`). Tệp `resources/checklist_master.yaml` giữ vai trò khung hạng mục phân loại, mọi căn cứ quy phạm trích dẫn bắt buộc phải kiểm định qua predicate SSOT tại Mục 5.
* **Xuất Bản Văn Bản (.docx):** Bắt buộc sử dụng Seam `ooxml_processor.v1` (`from ccba_ooxml import DocxDocument`). Tuyệt đối cấm sử dụng trực tiếp thư viện `python-docx` không qua Seam cách ly. Trường hợp Seam chưa hỗ trợ mẫu checklist phức tạp, Agent xuất định dạng Markdown chuẩn và dừng lại.

---

## When to Use

- Cần **tạo checklist hồ sơ hoàn thành** cho một dự án/công trình cụ thể
- Cần **cập nhật checklist** khi VBPL thay đổi (kết hợp với skill `legal-document-tracker`)
- Cần **tài liệu tập huấn** cho kỹ sư giám sát về hồ sơ hoàn thành
- Cần **kiểm tra tính đầy đủ** của bộ hồ sơ hoàn thành một công trình
- User nói: "danh mục hồ sơ hoàn thành", "checklist", "hồ sơ nghiệm thu", "completion documents"

## Key Files

| File | Mô tả |
|------|--------|
| `resources/checklist_master.yaml` | Danh mục hồ sơ master — Khung hạng mục hồ sơ hoàn thành |
| `resources/checklist_by_project.md` | Template checklist theo loại công trình |
| `resources/training_handout.md` | Template tài liệu tập huấn cho kỹ sư giám sát |

## How to Use

### 1. Tạo Checklist cho dự án cụ thể

1. Đọc `resources/checklist_master.yaml` để nắm khung cấu trúc master
2. Hỏi user các thông tin dự án:
   - Tên dự án / công trình
   - Loại công trình (dân dụng / công nghiệp / hạ tầng kỹ thuật)
   - Cấp công trình (đặc biệt / I / II / III / IV)
   - Chủ đầu tư
3. Đọc template `resources/checklist_by_project.md`
4. Tạo checklist phù hợp, bỏ các mục không áp dụng (đánh dấu N/A)
5. Xuất ra Markdown (và Docx khi phát hành qua `ccba_ooxml:DocxDocument`)
   - **Tiêu chí hoàn thành:** Đã tạo tệp checklist Markdown đầy đủ theo thông tin dự án và vượt qua cổng kiểm định máy tính:
     ```bash
     python -m ccba_harness verify-patch --preset doc --target <tệp_markdown_checklist> --min-bytes 500
     ```
     Lệnh kiểm định trả về **Exit Code 0**. Theo quy tắc Khóa Cứng (ADR-0058): Cấm tuyệt đối Agent tuyên bố hoàn tất nếu tệp chưa được ghi ra đĩa hoặc rỗng.

### 2. Cập nhật khi VBPL thay đổi

1. Tra cứu đối soát qua Seam `python -m ccba_legal query` và `ccba_legal.registry` theo đúng nguyên tắc kiểm định SSOT tại Mục 5.
   - Nếu không có văn bản thay thế mới: Sử dụng khung hạng mục tĩnh (`checklist_master.yaml`) kết hợp đối chiếu căn cứ pháp lý hiện hành.
   - Nếu có văn bản thay thế đạt trạng thái `ACTIVE`: Cập nhật lại khung master theo quy định mới nhất.
2. So sánh nội dung Phụ lục hồ sơ hoàn thành cũ vs mới
3. Cập nhật `checklist_master.yaml`:
   - Thêm mục mới
   - Sửa đổi mục hiện có
   - Đánh dấu mục bãi bỏ
4. Ghi log thay đổi trong `changelog` section
   - **Tiêu chí hoàn thành:** Đã cập nhật file `checklist_master.yaml` và lưu vết thay đổi trong changelog.

### 3. Tạo tài liệu tập huấn

1. Đọc template `resources/training_handout.md`
2. Điền nội dung dựa trên checklist master
3. Thêm ví dụ thực tế và lưu ý từ kinh nghiệm CCBA
4. Xuất ra Markdown hoặc Word (.docx qua `ccba_ooxml:DocxDocument`) cho phát tay trong buổi seminar
   - **Tiêu chí hoàn thành:** Đã tạo tài liệu tập huấn hoàn chỉnh dạng Markdown/Word sẵn sàng phát hành.

## Legal Basis & Verification

Mọi căn cứ pháp lý của checklist bắt buộc phải được đối soát động qua Seam `python -m ccba_legal query` hoặc `ccba_legal.registry` theo đúng nguyên tắc SSOT tại Mục 5 (trạng thái `ACTIVE`, không bị thay thế). Tuyệt đối không suy đoán hiệu lực từ danh mục tĩnh.

## Output Formats

- **Markdown** (.md) — Cho review và lưu trữ trong knowledge base.
- **Word** (.docx) — Cho in ấn và phát hành chính thức, sử dụng Deep Seam `ooxml_processor.v1` (`DocxDocument`).

## Dependencies

- Seam `ooxml_processor.v1` (`packages/ccba-ooxml`)
- `pyyaml` (cho đọc YAML)
- Skill `ccba-legal-document-tracker` / CLI `ccba_legal query` (cho cập nhật theo VBPL)

---

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế.
* Mọi văn bản trích dẫn bắt buộc phải được đối soát qua lệnh SSOT `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry`, đảm bảo đạt trạng thái hiệu lực chuẩn hóa `ACTIVE` (bao gồm `current`/`active` qua hàm `normalize_doc_status`) và không bị thay thế bởi văn bản khác (các trường bị thay thế `superseded_by`, `replaced_by`, `replaced_by_docs` trống và mã văn bản không nằm trong danh sách thay thế của bất kỳ văn bản kế nhiệm nào). Các văn bản kế nhiệm sở hữu quan hệ thay thế (`supersedes`, `replaces`, `replaced_docs`, `relations.*`) đối với văn bản cũ vẫn hoàn toàn hợp lệ để trích dẫn.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
