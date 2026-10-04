---
proposal_id: "2026-10-04_maskara-v120-hardening"
type: "packages"
name: "maskara-v120-hardening"
status: "proposed"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_by_archetype: "platform_tooling"
proposed_date: "2026-10-04"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
  - "Security & Privacy"
---

# RFC Proposal: Nâng Cấp ccba-maskara v1.2.0 (Lọc Template, Batch Staged Scanning & Init-Hooks)

- **Tác giả đề xuất:** Platform Architect / Security Lead
- **Ngày lập:** 2026-10-04
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý nền tảng:** [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0042](../../docs/adr/0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md), Session Learning #41.

---

### 1. Bối cảnh & Động lực Thực tế (Context & Motivation)
1. **Nỗi đau thực tế (Pain point):**
   - Các biến môi trường dạng mẫu `${...}` hoặc `{{...}}` thường xuyên kích hoạt false-positive trên rule `env-secret`.
   - Lệnh commit Git trên các Spoke chưa có cơ chế kiểm tra nhanh hàng loạt file staged dưới 0.1s trong một tiến trình duy nhất.
   - Việc thiết lập thủ công git hook trên các Spoke dễ bị thiếu sót hoặc lệch cấu hình `core.hooksPath`.
2. **Giải pháp v1.2.0:**
   - Bổ sung hàm lọc an toàn `is_safe_or_template()` riêng cho rule `env-secret`.
   - Bổ sung cờ `--staged` và `--files` cho `maskara scan`.
   - Cung cấp lệnh CLI `maskara init-hooks` để tự động hóa 100% cấu hình `.githooks/pre-commit` và `git config core.hooksPath .githooks`.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Bảo vệ bí mật trên toàn bộ Hub và mọi Spoke kết nối |
| **Độ Phức tạp (Complexity)** | Thấp (KISS) | Đóng gói gọn gàng trong package `ccba-maskara` |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100% | Đã kiểm chứng qua `check_spoke_leakage.py` |
| **Bảo tồn Nghiệp vụ (Charter)** | Tuân thủ 100% | Tương thích ngược hoàn toàn với v1.0.0 |
