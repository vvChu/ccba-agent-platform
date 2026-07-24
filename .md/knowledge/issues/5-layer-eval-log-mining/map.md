# Wayfinder Navigation Map: Triển Khai Tầng 5 (Production Log Mining & Auto-Tuning Evals)

**Mã vấn đề**: `issue-5-layer-eval-log-mining`  
**Tài liệu gốc**: [brainstorm_skills_eval_legal_guardrails.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/brainstorm_skills_eval_legal_guardrails.md)  
**Trạng thái bản đồ**: 🟡 **Đang thực hiện** — Đã phác thảo bản đồ đầu tiên  
**Khởi tạo**: 2026-07-24  

---

## 🎯 1. Điểm đích (Destination)
Xây dựng và hoàn thiện CLI tool `scripts/log_eval_miner.py` làm hạt nhân cho **Tầng 5 (Production Log Mining & Failure-Driven Auto-Tuning)** của hệ thống kiểm thử AI Skills. Tool tự động:
1. Đọc và bóc tách các câu hỏi thực tế của người dùng từ `transcript.jsonl` và system logs.
2. Áp dụng kỹ năng `maskara-privacy` để tự động che giấu (redact) thông tin nhạy cảm.
3. Nhận diện các lỗi router/disclaimer trong quá trình tương tác thực tế để tự động đóng gói thành các Negative/Happy Test Cases thực chiến mới.
4. Nạp bổ sung vào `.agents/skills/eval-gate/test_cases/eval_*.json` và kiểm tra 100% hợp lệ qua `eval_runner.py --dry-run`.

---

## 📝 2. Ghi chú (Notes)
- **Rào chắn Bảo mật**: Bắt buộc mọi chuỗi văn bản trích xuất từ log người dùng phải qua bộ lọc Redact của `maskara-privacy` trước khi ghi đĩa.
- **Rào chắn Scoped Tests**: Mọi unit tests viết cho miner phải chạy qua `python scripts/safe_pytest.py -f scripts/tests/test_log_eval_miner.py`.

---

## ✅ 3. Quyết định đã chốt (Decisions so far)
- [Tích hợp Noise Prompt Linter vào dry-run validator](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/scripts/eval_runner.py#L400-L420): Đã loại bỏ 100% prompt rác trong 11 skills evals.
- [Tích hợp Superseded Legal Doc Linter vào validate_docs.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validate_docs.py#L510-L530): Đã cưỡng chế tham chiếu Luật Xây dựng 2025 (135/2025/QH15) & NĐ 105/2025/NĐ-CP.
- [Giữ nguyên phân tách Single Responsibility Principle](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/brainstorm_skills_eval_legal_guardrails.md#L18-L22): Giữ `legal-document-tracker` và `bigbim-vbpl-digest` là 2 deep modules độc lập, dùng Cross-Skill Evaluation làm test case.

---

## 🚀 4. Vé Biên giới (Frontier Tickets)

- 🟢 [Ticket 5.1: Thiết kế Schema & Parser cho log_eval_miner.py](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-log-mining/tickets.md#ticket-log-miner-1) `Task [AFK]` — Đọc `transcript.jsonl` và tích hợp `maskara-privacy`.
- 🟡 [Ticket 5.2: Thuật toán nhận diện Router Failures & Disclaimer Mismatches](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-log-mining/tickets.md#ticket-log-miner-2) `Task [AFK]` — Bóc tách edge cases thực tế thành negative cases.
- 🟡 [Ticket 5.3: Tích hợp CLI Runner & Unit Tests cho Miner](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/5-layer-eval-log-mining/tickets.md#ticket-log-miner-3) `Task [AFK]` — Viết `test_log_eval_miner.py` và tích hợp flag `--mine-logs` vào `eval_runner.py`.

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- Cơ chế tự động đồng bộ telemetry log từ Server Spark (:8090) về Hub theo cron job tuần tự.

---

## ⛔ 6. Ngoài phạm vi (Out of scope)
- Thay đổi cấu trúc LiteLLM Proxy hoặc Server Spark deployment.
