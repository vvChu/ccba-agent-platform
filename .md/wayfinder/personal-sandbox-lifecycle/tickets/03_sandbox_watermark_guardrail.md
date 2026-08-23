# Ticket 03: Rào Chắn Thủy Ấn Draft & QC Level 1 Cap Guardrail

- **Type:** Task (AFK / Code Implementation)
- **Status:** open
- **Assignee:** Unassigned
- **Target Seam:** scripts/governance/sandbox_auditor.py, scripts/doc_auditor.py
- **Reference:** ADR 0046 (Mục 3: Sandbox Watermarking & QC Level Cap)

## Mục Tiêu
Xây dựng rào chắn kiểm định tự động bảo đảm:
1. **Kiểm tra Thủy ấn Draft:** Mọi tài liệu/báo cáo thẩm tra phát sinh trong workspace có sandbox_mode: true bắt buộc phải có thủy ấn [CCBA SANDBOX DRAFT — BẢN THẢO NGHIÊN CỨU NỘI BỘ — CHƯA PHÁT HÀNH CHÍNH THỨC].
2. **Khóa Cứng Cấp Phê Duyệt:** Báo lỗi nếu phát hiện cấu hình hoặc metadata gán thẩm quyền $> 1$ (Level 2-5) trong môi trường sandbox cá nhân.
3. **Chặn Đẩy Lên CdeDocuments:** IDOPBridge từ chối thực hiện lệnh publish trực tiếp vào CdeDocuments nếu workspace là personal_sandbox.

## Tiêu Chí Chấp Nhận (Acceptance Criteria)
- [ ] Bổ sung SandboxAuditor vào bộ điều phối DocAuditor.
- [ ] Tích hợp kiểm tra vào python scripts/validate_docs.py.
- [ ] Viết unit test kiểm thử rào chắn trong 	ests/test_sandbox_auditor.py.
