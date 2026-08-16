# 📊 Progressive Reference: Pha 3 — Tổng Hợp Báo Cáo Kỹ Thuật & Heat Map (Reporter)

> Thuộc Master Skill [`ccba-ai-qc`](../SKILL.md).

Module Reporter chịu trách nhiệm tổng hợp các kết quả Audit thô từ AI Vision thành một báo cáo Đường găng Kỹ thuật (Technical Critical Path Report) kèm Heat Map rủi ro hoàn chỉnh phục vụ quản trị dự án.

---

## 1. Tiêu Chí Hoàn Thành (Completion Criteria)

Tác vụ sinh báo cáo được coi là hoàn thành khi và chỉ khi:
- [x] Đã sinh tệp báo cáo tổng hợp Markdown tại:
  `[target_project]/.md/extracts/audit_batch/BATCH_QC_Report_Auto.md` (hoặc `qc_audit_report.md`)
- [x] Tệp báo cáo chứa đầy đủ các phân đoạn chính quy: bảng Heat Map rủi ro tổng hợp (High/Medium/Low), danh sách chi tiết lỗi đụng độ kỹ thuật có liên kết ảnh minh chứng, và các đề xuất/kiến nghị hành động.

---

## 2. Công Cụ Thực Thi

Khi cần chạy độc lập module Reporter:
```powershell
python .agents/skills/ccba-ai-qc/scripts/reporter_engine.py
```
