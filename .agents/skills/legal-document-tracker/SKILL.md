---
name: legal-document-tracker
description: Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam với VBHNEngine
  và Registry.
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _consulting
triggers:
- VBPL
- pháp luật
- legal
- registry
- nghị định
- thông tư
- văn bản pháp luật
- luật xây dựng
---
# Legal Document Tracker

Skill hỗ trợ theo dõi, phân tích và so sánh các Văn bản Pháp luật (VBPL) liên quan đến quản lý chất lượng công trình xây dựng tại Việt Nam kết hợp Deep Seam **`VBHNEngine`** ([`packages/ccba-legal-intel`](../../packages/ccba-legal-intel)).

---

## When to Use

- Cần **cập nhật danh mục VBPL** đang theo dõi (thêm mới, thay đổi trạng thái)
- Cần **so sánh VBPL cũ ↔ mới** (VD: NĐ 06/2021 vs dự thảo NĐ QLCL 2026) qua AST diff tự động
- Cần **hợp nhất văn bản pháp luật** (Luật gốc + các Nghị định sửa đổi bổ sung)
- Cần **đánh giá tác động** của VBPL mới lên quy trình CCBA
- Cần **hướng dẫn NotebookLM** để đọc nhanh VBPL hoặc soạn thảo công văn

---

## Key Files

| File | Mô tả |
|------|--------|
| `resources/legal_registry.yaml` | Danh mục VBPL đang theo dõi kèm metadata |
| `resources/comparison_table.md` | Template bảng so sánh VBPL cũ ↔ mới |
| `resources/impact_report.md` | Template báo cáo tác động thay đổi lên CCBA |
| `resources/notebooklm_prompts.md` | Prompt mẫu cho NotebookLM theo use case |

---

## How to Use

### 1. Cập nhật Registry VBPL

Đọc file `resources/legal_registry.yaml` để nắm danh mục hiện tại. Khi cần cập nhật:
1. **Thêm VBPL mới**: Thêm entry mới vào `documents` với đầy đủ metadata
2. **Thay đổi trạng thái**: Cập nhật `status` (`draft` $\rightarrow$ `enacted` $\rightarrow$ `current` $\rightarrow$ `superseded` $\rightarrow$ `expired`)
3. **Đánh dấu thay thế**: Set `replaces` và `replaced_by` khi có VBPL mới thay thế

### 2. Tạo Bảng So Sánh & Hợp Nhất VBPL (`VBHNEngine`)

Khi có VBPL mới sửa đổi, thay thế VBPL cũ:

1. Kích hoạt Deep Seam `VBHNEngine` để phân tích cây AST và tạo bảng so sánh Điều/Khoản tự động:
   ```python
   from ccba_legal import VBHNEngine

   engine = VBHNEngine()
   # So sánh và xuất diff tự động giữa 2 phiên bản
   diff_report = engine.generate_diff(
       base_doc_path="path/to/old_doc.md",
       amending_doc_path="path/to/new_doc.md"
   )
   # Hoặc hợp nhất văn bản thành VBHN hoàn chỉnh:
   # vbhn_result = engine.consolidate(base_ast, [patch1, patch2])
   ```
2. Đọc kết quả diff được chuẩn hóa theo từng chương/điều/khoản (tự động so khớp `D1` $\leftrightarrow$ `dieu-1`).
3. Điền các đánh giá chuyên môn vào template `resources/comparison_table.md`.
4. Xuất file vào thư mục tài liệu đích của dự án.

### 3. Tạo Impact Report

Khi cần đánh giá tác động:
1. Đọc template `resources/impact_report.md`.
2. Xác định các quy trình CCBA bị ảnh hưởng.
3. Phân loại tác động: Cao / Trung bình / Thấp.
4. Đề xuất hành động cần thiết (cập nhật quy trình, đào tạo).
5. Xuất file Markdown và Word (.docx).

### 4. Hướng dẫn NotebookLM

Đọc `resources/notebooklm_prompts.md` để lấy prompt mẫu cho các use case:
- Đọc nhanh VBPL $\rightarrow$ trích xuất điểm chính
- Soạn thảo công văn dựa trên VBPL
- So sánh 2 văn bản trong cùng notebook

---

## ⚠️ Disclaimer

Skill này tạo **tài liệu phân tích VBPL**, KHÔNG phải tư vấn pháp lý. Luôn cần chuyên gia pháp lý xác nhận trước khi áp dụng vào dự án thực.
