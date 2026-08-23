# Ticket 03: Rào Chắn Thủy Ấn Draft & QC Level 1 Cap Guardrail

- **Type:** Task (AFK / Code Implementation)
- **Status:** closed
- **Assignee:** Antigravity AI Agent
- **Target Seam:** `scripts/governance/sandbox_auditor.py`, `scripts/doc_auditor.py`
- **Reference:** ADR 0046 (Mục 3: Sandbox Watermarking & QC Level Cap)

## Mục Tiêu
Xây dựng rào chắn kiểm định tự động bảo đảm:
1. **Kiểm tra Thủy ấn Draft:** Mọi tài liệu/báo cáo thẩm tra phát sinh trong workspace có `sandbox_mode: true` bắt buộc phải có thủy ấn `[CCBA SANDBOX DRAFT — BẢN THẢO NGHIÊN CỨU NỘI BỘ — CHƯA PHÁT HÀNH CHÍNH THỨC]`.
2. **Khóa Cứng Cấp Phê Duyệt:** Báo lỗi nếu phát hiện cấu hình hoặc metadata gán thẩm quyền $> 1$ (Level 2-5) trong môi trường sandbox cá nhân.
3. **Chặn Đẩy Lên CdeDocuments:** `IDOPBridge` từ chối thực hiện lệnh publish trực tiếp vào `CdeDocuments` nếu workspace là `personal_sandbox`.

## Kết Quả Thực Hiện (Resolution Summary)
- [x] Xây dựng class `SandboxAuditor` kế thừa `BaseAuditor` trong `scripts/governance/sandbox_auditor.py`.
- [x] Kiểm soát trần phê duyệt Cấp 1 (`LEVEL_1_TECHNICAL_CHECK`) và phát hiện vi phạm nếu gán Level 2-5 hoặc phê duyệt ISO trong sandbox.
- [x] Rà soát và bắt buộc có thủy ấn `WATERMARK_HEADER` trên toàn bộ tệp báo cáo bản nháp trong `output/`, `deliverables/`, `reports/`.
- [x] Bộ test `tests/test_sandbox_auditor.py` đạt 4/4 passed (100%).\n