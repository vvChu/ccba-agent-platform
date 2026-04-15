---
description: Cập nhật registry VBPL và kiểm tra tác động lên danh mục hồ sơ hoàn thành
---

# Workflow: Update Legal Registry

Quy trình cập nhật danh mục VBPL và đánh giá tác động lên quy trình CCBA.
Chạy **hàng tuần** hoặc **khi phát hiện VBPL mới**.

> **Cross-workspace note**: Tất cả paths trong workflow này relative to Hub root
> (`D:\GitHubProjects\ccba-agent-platform`). Khi chạy từ workspace khác,
> resolve bằng cách prepend Hub path. Output lưu về workspace hiện tại.

## Bước 1: Đọc Registry hiện tại

// turbo

1. Đọc skill SKILL.md:
   ```
   .agent/skills/legal-document-tracker/SKILL.md
   ```

2. Đọc registry hiện tại:
   ```
   .agent/skills/legal-document-tracker/registry/legal_registry.yaml
   ```

3. Xác định danh mục `monitoring` — VBPL nào đang theo dõi?

## Bước 2: Tìm kiếm VBPL mới

Sử dụng web search để kiểm tra:

1. **Trang chính thức Bộ Xây dựng**: Tìm kiếm "nghị định quản lý chất lượng 2026" trên moc.gov.vn
2. **Cổng TTĐT Chính phủ**: Tìm kiếm "luật xây dựng 2025 nghị định hướng dẫn" trên vanban.chinhphu.vn
3. **Tìm kiếm tổng quát**: Các từ khóa liên quan đến VBPL xây dựng mới ban hành

Với mỗi kết quả, ghi nhận:
- Số hiệu văn bản
- Ngày ban hành / dự kiến ban hành
- Trạng thái (dự thảo / đã ban hành)
- Link nguồn

## Bước 3: Cập nhật Registry

Nếu tìm thấy VBPL mới:

1. **Thêm entry mới** vào section phù hợp (laws / decrees / standards)
2. **Cập nhật trạng thái** VBPL hiện có nếu cần (VD: draft → enacted)
3. **Cập nhật `replaces` / `replaced_by`** nếu có VBPL thay thế
4. **Cập nhật `monitoring` section** — đánh dấu items đã fulfilled
5. **Cập nhật `metadata.last_updated`**

## Bước 4: Tạo Impact Report (nếu có VBPL quan trọng)

Nếu phát hiện VBPL quan trọng (NĐ mới, sửa đổi lớn):

1. Đọc template:
   ```
   .agent/skills/legal-document-tracker/templates/impact_report.md
   ```
2. Phân tích tác động lên quy trình CCBA
3. Xuất báo cáo Markdown + Word
4. Lưu vào thư mục tài liệu nguồn

## Bước 5: Cập nhật Completion Checklist (nếu ảnh hưởng)

Nếu VBPL mới ảnh hưởng đến hồ sơ hoàn thành:

1. Đọc skill:
   ```
   .agent/skills/completion-checklist/SKILL.md
   ```
2. Đọc checklist master:
   ```
   .agent/skills/completion-checklist/data/checklist_master.yaml
   ```
3. Xác định mục cần thêm/sửa/bỏ
4. Cập nhật `checklist_master.yaml`
5. Ghi changelog entry

## Bước 6: Báo cáo

Tổng hợp kết quả cho user:

```markdown
## 📋 Legal Registry Update Report

**Ngày cập nhật**: [date]

### VBPL mới phát hiện
- [ ] [Tên VBPL] — [trạng thái] — [link]

### Registry đã cập nhật
- [x] Thêm N entry mới
- [x] Cập nhật N trạng thái

### Impact Assessment
- [Mức tác động] — [Lĩnh vực]

### Checklist cập nhật
- [x/☐] Có/Không cần cập nhật checklist

### Hành động tiếp theo
1. [Action item]
```
