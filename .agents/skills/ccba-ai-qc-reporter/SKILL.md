---
name: ccba-ai-qc-reporter
description: Tổng hợp kết quả Audit đa bộ môn thành báo cáo Heat Map kỹ thuật (Pha 3 của QCAuditPipeline).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Reporter

Reporter chịu trách nhiệm tổng hợp các kết quả Audit thô từ AI Vision thành một báo cáo Đường găng Kỹ thuật (Technical Critical Path Report) kèm Heat Map rủi ro hoàn chỉnh phục vụ quản trị dự án. Đây là **Pha 3** trong Deep Seam **`QCAuditPipeline`** ([`packages/ccba-ai`](../../packages/ccba-ai)).

---

## Tiêu chí hoàn thành (Completion Criteria)

Tác vụ sinh báo cáo được coi là hoàn thành khi và chỉ khi:
- [ ] Đã sinh tệp báo cáo tổng hợp Markdown tại:
  `[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md` (hoặc `qc_audit_report.md`)
- [ ] Tệp báo cáo chứa đầy đủ các phân đoạn chính quy: bảng Heat Map rủi ro tổng hợp (High/Medium/Low), danh sách chi tiết lỗi đụng độ kỹ thuật có liên kết ảnh minh chứng, và các đề xuất/kiến nghị hành động.

---

## Công cụ thực thi

Pha này tự động thực thi ở cuối quy trình `QCAuditPipeline.run_audit()`. Khi cần chạy độc lập:
```bash
python .agents/skills/ccba-ai-qc-reporter/scripts/reporter_engine.py
```
