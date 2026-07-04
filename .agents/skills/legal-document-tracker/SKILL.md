---
name: legal-document-tracker
description: Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam. Duy trì registry, tạo bảng so sánh, báo cáo tác động và tích hợp NotebookLM.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_consulting"
---

# Legal Document Tracker

Skill hỗ trợ theo dõi, phân tích và so sánh các Văn bản Pháp luật (VBPL) liên quan đến quản lý chất lượng công trình xây dựng tại Việt Nam.

## When to Use

- Cần **cập nhật danh mục VBPL** đang theo dõi (thêm mới, thay đổi trạng thái)
- Cần **so sánh VBPL cũ ↔ mới** (VD: NĐ 06/2021 vs dự thảo NĐ QLCL 2026)
- Cần **đánh giá tác động** của VBPL mới lên quy trình CCBA
- Cần **hướng dẫn NotebookLM** để đọc nhanh VBPL hoặc soạn thảo công văn
- User nói: "cập nhật VBPL", "so sánh nghị định", "tác động luật mới", "tổng hợp pháp luật"

## Key Files

| File | Mô tả |
|------|--------|
| `resources/legal_registry.yaml` | Danh mục VBPL đang theo dõi kèm metadata |
| `resources/comparison_table.md` | Template bảng so sánh VBPL cũ ↔ mới |
| `resources/impact_report.md` | Template báo cáo tác động thay đổi lên CCBA |
| `resources/notebooklm_prompts.md` | Prompt mẫu cho NotebookLM theo use case |

## How to Use

### 1. Cập nhật Registry VBPL

Đọc file `resources/legal_registry.yaml` to nắm danh mục hiện tại. Khi cần cập nhật:

1. **Thêm VBPL mới**: Thêm entry mới vào `documents` với đầy đủ metadata
2. **Thay đổi trạng thái**: Cập nhật `status` (draft → enacted → superseded)
3. **Đánh dấu thay thế**: Set `replaces` và `replaced_by` khi có VBPL mới thay thế

Các status hợp lệ:
- `draft` — Đang dự thảo, lấy ý kiến
- `enacted` — Đã ban hành, có hiệu lực
- `current` — Đang áp dụng
- `superseded` — Đã bị thay thế bởi VBPL mới
- `expired` — Hết hiệu lực

### 2. Tạo bảng so sánh VBPL

Khi có VBPL mới thay thế VBPL cũ:

1. Đọc template `resources/comparison_table.md`
2. Đọc nội dung VBPL cũ và VBPL mới (từ markdown files hoặc PDF)
3. Điền bảng so sánh theo từng chương/điều/khoản
4. Highlight các thay đổi quan trọng ảnh hưởng đến QLCL
5. Xuất file vào thư mục tài liệu nguồn của user

### 3. Tạo Impact Report

Khi cần đánh giá tác động:

1. Đọc template `resources/impact_report.md`
2. Xác định các quy trình CCBA bị ảnh hưởng
3. Phân loại tác động: Cao / Trung bình / Thấp
4. Đề xuất hành động cần thiết (cập nhật quy trình, đào tạo, v.v.)
5. Xuất file Markdown và Word (.docx)

### 4. Hướng dẫn NotebookLM

Đọc `resources/notebooklm_prompts.md` để lấy prompt mẫu cho các use case:
- Đọc nhanh VBPL → trích xuất điểm chính
- Soạn thảo công văn dựa trên VBPL
- Soạn thư kỹ thuật (technical letter)
- So sánh 2 văn bản trong cùng notebook

## Source Documents

Tài liệu nguồn được lưu tại:
```
D:\OneDrive - IBST BIM\00 CCBA\03 PMO Documents\
  06 BIM RD and International Coo\
    04_ĐÀO_TẠO_NỘI_BỘ\04_Cập_nhật_kiến_thức\BIM_VBPL\
```

Cấu trúc:
- `BIM_VBPL/2026/` — Tài liệu năm 2026
  - `Dự thảo NĐQLCL2026 lấy ý kiến/` — Dự thảo NĐ QLCL mới
  - `CCBA_RD_SEMINAR_003_*` — Tài liệu seminar

## Dependencies

- `python-docx` (cho xuất Word)
- Web search (cho cập nhật VBPL mới từ moc.gov.vn)

## ⚠️ Disclaimer

Skill này tạo **tài liệu phân tích VBPL**, KHÔNG phải tư vấn pháp lý.
Luôn cần chuyên gia pháp lý xác nhận trước khi áp dụng vào dự án thực.
