---
proposal_id: "2026-10-17_anti-lossy-compression-retrospective"
type: "skill"
name: "anti-lossy-compression-retrospective"
status: "open"
priority: "Trung bình"
proposed_by_project: "dgx-spark-toolkit"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-10-17"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
---

# RFC Proposal: Rào Chắn Chống Nén Mất Ngữ Cảnh (Anti-Lossy-Compression) & Kiểm Toán Phản Biện Peer Review Trong `ccba-session-retrospective`

- **Tác giả đề xuất:** Antigravity (Pair Architect & Builder)
- **Ngày lập:** 2026-10-17
- **Căn cứ pháp lý nền tảng:** [ADR-0030](../../docs/adr/0030-tiered-memory-model.md), [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0057](../../docs/adr/0057-two-stage-skill-governance-and-gpi.md), [ADR-0060](../../docs/adr/0060-single-user-multi-device-decoupling.md).

---

### 1. Bối cảnh & Nỗi đau Thực tế (Context & Motivation)
1. **Nỗi đau thực tế tại Spoke `dgx-spark-toolkit`:**
   - Khi thực thi nén bộ nhớ làm việc `session_learnings.md` để duy trì dưới ngưỡng trần (`<= 10.0 KB` trên Hub hoặc `< 115 dòng` tại Spoke), quá trình rút gọn câu chữ đã vô tình cắt bỏ **điều kiện biên / phạm vi áp dụng (Scope Qualifier)**.
   - Cụ thể: Quy tắc gốc `RULE-4.5` trong `session_learnings_history.md` chỉ rõ trình phân tích cú pháp `--deny "Read(...)"` của Grok CLI coi ký tự `~` là literal nên phải truyền đường dẫn tuyệt đối vào cờ `--deny`. Khi nén vào `session_learnings.md`, cụm `"trong --deny"` bị lược bỏ thành *"Grok CLI không mở rộng `~` — luôn dùng đường dẫn tuyệt đối"*.
   - Hệ quả: Trong vòng Peer Review tiếp theo, Reviewer đọc quy tắc bị nén mất ngữ cảnh và yêu cầu thay thế toàn bộ `~/...` bằng đường dẫn tuyệt đối `/home/vvc/...` trong tài liệu Markdown/Skill, trực tiếp vi phạm `ADR-0060` (Single-User Multi-Device & Machine-State Decoupling) và làm gãy bộ kiểm tra vệ sinh `check_spoke_cleanliness.py --strict`.
2. **Giải pháp đã kiểm chứng:**
   - Bổ sung **Bất biến Bảo toàn Điều kiện Biên (Scope Qualifier Preservation / Anti-Lossy-Compression Guardrail)** vào Bước 2 của `ccba-session-retrospective/SKILL.md`: Khi rút gọn `RULE-X.Y`, bắt buộc giữ nguyên phạm vi áp dụng cụ thể (cờ CLI, module, OS) và đối chiếu chéo với `session_learnings_history.md`.
   - Bổ sung **Kiểm toán Phản biện Đánh giá Đồng đẳng (Adversarial Audit of Peer Reviewer Claims)** vào Bước 1 của `ccba-session-retrospective/SKILL.md`: Đối chiếu ngược các điều kiện `CONDITIONAL_ACCEPT`/`REJECT` từ Peer Reviewer với mã nguồn thực thi và lịch sử `session_learnings_history.md` trước khi luật hóa.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Cao | Ngăn chặn hiện tượng Over-Generalization gây xung đột giữa `session_learnings.md` và các ADR nền tảng trên toàn bộ mạng lưới Spoke |
| **Độ Phức tạp (Complexity)** | Tối thiểu (KISS) | Cập nhật 2 điểm rào chắn trực tiếp trong `ccba-session-retrospective/SKILL.md` (`v1.5.0` -> `v1.5.1`) |
| **Rủi ro Hỏng hóc (Risk)** | Bằng 0 | Không thay đổi cấu trúc CLI hay schema dữ liệu |
