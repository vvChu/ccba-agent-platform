---
description: Chuẩn bị nội dung cho buổi seminar/thảo luận nội bộ CCBA
---

# Workflow: Prepare Seminar

Quy trình end-to-end chuẩn bị nội dung trước mỗi buổi seminar/thảo luận nội bộ CCBA.
Thường chạy **1-2 ngày trước** buổi seminar.

## Bước 1: Thu thập thông tin

Hỏi user các thông tin sau:

1. **Ngày, giờ** tổ chức
2. **Chủ đề chính** (liệt kê 1-3 topics)
3. **Đường dẫn tài liệu nguồn** (mặc định: `06 BIM RD and International Coo\04_ĐÀO_TẠO_NỘI_BỘ\04_Cập_nhật_kiến_thức\BIM_VBPL`)
4. **Có cần recap tháng không?** (thường là có nếu đây là buổi cuối tháng)
5. **Thời lượng dự kiến** (mặc định 90 phút)

## Bước 2: Đọc skill hướng dẫn

Đọc SKILL.md của skill `seminar-builder` để nắm templates và cách sử dụng:
```
.agent/skills/seminar-builder/SKILL.md
```

## Bước 3: Tạo Recap tháng (nếu cần)

Nếu user yêu cầu recap:

1. Đọc template `seminar-builder/templates/monthly_recap.md`
2. Tìm các file seminar của tháng hiện tại trong thư mục tài liệu nguồn
3. Extract nội dung từng buổi (đọc PDF/PPTX titles, nếu không đọc được thì hỏi user tóm tắt)
4. Tổng hợp key takeaways, action items
5. Xuất file recap vào thư mục tài liệu nguồn

## Bước 4: Kiểm tra cập nhật VBPL

1. Đọc skill `legal-document-tracker` SKILL.md
2. Đọc `legal-document-tracker/registry/legal_registry.yaml`
3. Kiểm tra mục `monitoring` — có VBPL nào mới cần cập nhật?
4. Nếu có topic liên quan đến VBPL → tìm kiếm web cho thông tin mới nhất trên moc.gov.vn
5. Nếu tìm thấy VBPL mới → gợi ý chạy workflow `/update-legal-registry`

## Bước 5: Tạo Agenda

1. Đọc template `seminar-builder/templates/agenda.md`
2. Điền thông tin từ Bước 1
3. Phân bổ thời gian hợp lý cho từng topic
4. Liệt kê tài liệu cần chuẩn bị trước
5. Xuất Markdown vào thư mục tài liệu nguồn

## Bước 6: Chuẩn bị tài liệu hỗ trợ

Tùy theo chủ đề, có thể cần:

- **Nếu topic về VBPL**: Tạo bảng so sánh (skill `legal-document-tracker`, template `comparison_table.md`)
- **Nếu topic về hồ sơ hoàn thành**: Tạo checklist (skill `completion-checklist`, template `checklist_by_project.md`)
- **Nếu topic về NotebookLM**: Chuẩn bị prompt mẫu (skill `legal-document-tracker`, template `notebooklm_prompts.md`)

## Bước 7: Xuất file tổng hợp

1. Tạo file Markdown tổng hợp tất cả nội dung chuẩn bị
2. Nếu user yêu cầu Word → xuất .docx
3. Lưu vào thư mục tài liệu nguồn theo naming convention:
   ```
   CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.md
   ```
4. Thông báo cho user các file đã tạo

## Bước 8: Tạo thông báo (tùy chọn)

Nếu user yêu cầu (VD: thay đổi lịch, thông báo nội dung):
1. Đọc template `seminar-builder/templates/notification.md`
2. Điền thông tin
3. Xuất format phù hợp cho email/Zalo
