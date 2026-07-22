---
name: completion-checklist
description: Tạo và duy trì Danh Mục Hồ Sơ Hoàn Thành Công Trình theo VBPL hiện hành. Hỗ trợ xuất Markdown và Word (.docx).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
bundle: "_consulting"
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

### 3. Tạo tài liệu tập huấn

1. Đọc template `templates/training_handout.md`
2. Điền nội dung dựa trên checklist master
3. Thêm ví dụ thực tế và lưu ý từ kinh nghiệm CCBA
4. Xuất ra Word (.docx) cho phát tay trong buổi seminar

## Legal Basis

Checklist master hiện dựa trên:
- **Nghị định 06/2021/NĐ-CP** — Phụ lục VIb: Danh mục hồ sơ hoàn thành công trình (Bắt buộc phải trích dẫn tên đầy đủ "Nghị định 06/2021/NĐ-CP" hoặc "Thông tư 10/2021/TT-BXD" trong phần căn cứ pháp lý của Danh mục).
- **NĐ 35/2023/NĐ-CP** — Sửa đổi, bổ sung NĐ 06/2021
- **Thông tư 10/2021/TT-BXD** — Hướng dẫn quản lý chất lượng công trình xây dựng
- **Dự thảo NĐ QLCL 2026** — Đang lấy ý kiến (chưa áp dụng)

## Output Formats

- **Markdown** (.md) — Cho review và lưu trữ trong knowledge base.
- **Word** (.docx) — Cho in ấn và phát hành chính thức, sử dụng thư viện `python-docx` để xuất bản tự động.

## Dependencies

- `python-docx` (cho xuất Word)
- `pyyaml` (cho đọc YAML)
- Skill `legal-document-tracker` (cho cập nhật theo VBPL)
