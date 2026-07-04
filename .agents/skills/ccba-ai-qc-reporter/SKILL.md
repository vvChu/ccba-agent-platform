---
name: ccba-ai-qc-reporter
description: Tổng hợp dữ liệu từ quá trình Discovery và Audit thành báo cáo kỹ thuật chính quy.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Reporter

Reporter chịu trách nhiệm tổng hợp các kết quả Audit thô từ AI (JSON/Markdown lẻ) thành một báo cáo Đường găng Kỹ thuật (Technical Critical Path Report) hoàn chỉnh phục vụ quản trị dự án.

---

## Tiêu chí hoàn thành (Completion Criteria)

Tác vụ sinh báo cáo được coi là hoàn thành thành công khi và chỉ khi:
- [ ] Đã sinh tệp báo cáo tổng hợp Markdown tại:
  `[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md`
- [ ] Tệp báo cáo chứa đầy đủ các phân đoạn chính quy: bảng Heat Map rủi ro tổng hợp (High/Medium/Low), danh sách chi tiết lỗi đụng độ kỹ thuật có liên kết ảnh minh chứng, và các đề xuất/kiến nghị hành động.

---

## Công cụ thực thi

Quy trình biên tập và tổng hợp báo cáo được xử lý qua script:
```text
.agents/skills/ccba-ai-qc-reporter/scripts/reporter_engine.py
```
