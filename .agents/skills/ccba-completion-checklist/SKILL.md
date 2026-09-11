---
name: ccba-completion-checklist
description: Tạo và duy trì Danh Mục Hồ Sơ Hoàn Thành Công Trình theo VBPL hiện hành.
  Hỗ trợ xuất Markdown và Word (.docx).
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _consulting
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

## When to Use

- Cần **tạo checklist hồ sơ hoàn thành** cho một dự án/công trình cụ thể
- Cần **cập nhật checklist** khi VBPL thay đổi (kết hợp với skill `legal-document-tracker`)
- Cần **tài liệu tập huấn** cho kỹ sư giám sát về hồ sơ hoàn thành
- Cần **kiểm tra tính đầy đủ** của bộ hồ sơ hoàn thành một công trình
- User nói: "danh mục hồ sơ hoàn thành", "checklist", "hồ sơ nghiệm thu", "completion documents"

## Key Files

| File | Mô tả |
|------|--------|
| `resources/checklist_master.yaml` | Danh mục hồ sơ master theo NĐ 06/2021 Phụ lục VIb |
| `resources/checklist_by_project.md` | Template checklist theo loại công trình |
| `resources/training_handout.md` | Template tài liệu tập huấn cho kỹ sư giám sát |

## How to Use

### 1. Tạo Checklist cho dự án cụ thể

1. Đọc `resources/checklist_master.yaml` để nắm cấu trúc master
2. Hỏi user các thông tin dự án:
   - Tên dự án / công trình
   - Loại công trình (dân dụng / công nghiệp / hạ tầng kỹ thuật)
   - Cấp công trình (đặc biệt / I / II / III / IV)
   - Chủ đầu tư
3. Đọc template `resources/checklist_by_project.md`
4. Tạo checklist phù hợp, bỏ các mục không áp dụng (đánh dấu N/A)
5. Xuất ra Markdown và Word (.docx)
   - **Tiêu chí hoàn thành:** Đã tạo checklist đầy đủ theo thông tin dự án, xuất đủ 2 định dạng (.md và .docx) và vượt qua cổng kiểm định máy tính:
     ```bash
     python -m ccba_harness verify-patch --preset doc --target <tệp_markdown_checklist> --min-bytes 500
     ```
     Lệnh kiểm định trả về **Exit Code 0**. Theo quy tắc Khóa Cứng (ADR-0058): Cấm tuyệt đối Agent tuyên bố hoàn tất nếu tệp chưa được ghi ra đĩa hoặc rỗng.

### 2. Cập nhật khi VBPL thay đổi

1. Kiểm tra `legal_registry.yaml` (skill `legal-document-tracker`) xem có văn bản nào liên quan đến nghiệm thu hoàn công thay đổi trạng thái sang `superseded` (hết hiệu lực) và có văn bản thay thế mới (`current`).
   - Nếu không có thay đổi: Dùng trực tiếp static templates (`checklist_master.yaml`) để tiết kiệm token và thời gian.
   - Nếu có thay đổi: Đề xuất người dùng sử dụng `/ccba-research` để spawn subagent nghiên cứu sâu cấu trúc phụ lục nghiệm thu mới và tự động cập nhật lại master checklist.
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
4. Xuất ra Word (.docx) cho phát tay trong buổi seminar
   - **Tiêu chí hoàn thành:** Đã tạo tài liệu tập huấn hoàn chỉnh dạng Word (.docx) sẵn sàng phát hành.

## Legal Basis

Checklist master được phân định căn cứ pháp lý theo mốc thời gian nghiệm thu công trình:

### 1. Áp dụng chính thức hiện hành (Công trình nghiệm thu từ 01/07/2026 trở đi):
- **Nghị định 207/2026/NĐ-CP** (Có hiệu lực từ 01/07/2026) — Quản lý chất lượng thi công xây dựng và bảo trì công trình (**Chính thức thay thế Nghị định 06/2021/NĐ-CP**). Trích dẫn Danh mục hồ sơ hoàn thành công trình theo Phụ lục tương ứng của NĐ 207/2026/NĐ-CP.
- **Luật Xây dựng 2025 (135/2025/QH15)** (Có hiệu lực từ 01/07/2026) — Quy định chung về công tác quản lý chất lượng và nghiệm thu công trình.
- **Nghị định 217/2026/NĐ-CP** (Có hiệu lực từ 01/07/2026) — Quản lý hoạt động xây dựng.
- **Thông tư 34/2026/TT-BXD** (Có hiệu lực từ 01/07/2026) — Quy định về phân cấp công trình xây dựng.

### 2. Áp dụng tra cứu chuyển tiếp (Công trình hoàn thành / nghiệm thu trước 01/07/2026):
- **Văn bản hợp nhất 19/VBHN-BXD (25/03/2026)** — Phụ lục VIb: Danh mục hồ sơ hoàn thành công trình (kế thừa Nghị định 105/2025/NĐ-CP).

## Output Formats

- **Markdown** (.md) — Cho review và lưu trữ trong knowledge base.
- **Word** (.docx) — Cho in ấn và phát hành chính thức, sử dụng thư viện `python-docx` để xuất bản tự động.

## Dependencies

- `python-docx` (cho xuất Word)
- `pyyaml` (cho đọc YAML)
- Skill `legal-document-tracker` (cho cập nhật theo VBPL)
