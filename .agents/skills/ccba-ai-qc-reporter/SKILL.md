---
name: ccba-ai-qc-reporter
description: Tổng hợp dữ liệu từ quá trình Discovery và Audit thành báo cáo kỹ thuật chính quy.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Reporter Skill

## Vai trò
Skill này đóng vai trò "người thư ký chuyên nghiệp", giúp chuyển đổi các kết quả Audit thô từ AI (JSON/Markdown lẻ) thành một báo cáo Đường găng Kỹ thuật (Technical Critical Path Report) hoàn chỉnh, sẵn sàng cho công tác quản trị.

## Cách sử dụng

### Các Trigger
- "Đóng gói báo cáo kỹ thuật"
- "Tổng hợp kết quả QC"
- "Tạo Technical Report"
- "Báo cáo đường găng"

## Chức năng chính
1. Tổng hợp Ma trận Backbone từ Discovery.
2. Thống kê Heatmap rủi ro (High/Medium/Low) từ Audit.
3. Liên kết hình ảnh minh chứng.
4. Đề xuất kiến nghị chiến lược.

## Danh mục Script
- `scripts/reporter_engine.py`: Logic tổng hợp dữ liệu thành báo cáo Markdown/Docx-ready.
