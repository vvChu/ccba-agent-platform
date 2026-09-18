---
proposal_id: "2026-09-18_nightly-tuner-evolution"
type: "infrastructure"
name: "nightly-tuner-evolution"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_by_archetype: "core_framework"
proposed_date: "2026-09-18"
applies_to:
  - "Phần mềm"
  - "Tác vụ Admin"
  - "Đánh giá & Tối ưu prompt"
---

# RFC Proposal: Hiện Đại Hóa Nightly Auto-Tuner Daemon, Real LLM Adapter & Multi-Domain Evals

- **Tác giả đề xuất:** CCBA Core & Eval Maintainers
- **Ngày lập:** 2026-09-18
- **Trạng thái:** Đang thẩm định (In Review / PR #286)
- **Căn cứ kiến trúc & pháp lý:** ADR-0023, ADR-0045, ADR-0047, ADR-0057, ADR-0058

---

### 1. Bối cảnh & Mục Tiêu Nghiệp Vụ (Context & Business Objectives)

1. **Khắc phục các điểm nghẽn của Nightly Auto-Tuner (Wayfinder Ticket 01):**
   - Loại bỏ xung đột luồng điều khiển fall-through trong `mock_agent_task` bằng thang `if-elif` hợp nhất.
   - Giải quyết bế tắc tam hợp (*Conjunctive Deadlock*) miền BIM trong `GitRatchetOptimizer.propose_mutation` bằng cách bổ sung bất biến *Trí Nhớ Số (Digital Memory)* song hành cùng Uniclass 200 và ISO 12006-2.
   - Chuẩn hóa điều hướng dataset cho `ccba-ai-qc` (`eval_pccc_audit_redteam.json`) và bổ sung từ khóa Luật 135/2025 vào fallback pháp lý.

2. **An toàn Git, Khóa tiến trình & Dọn dẹp nhánh rác (Wayfinder Ticket 02):**
   - Đảm bảo tính độc quyền thông qua cơ chế khóa tiến trình `flock -n 200` tại `/tmp/ccba_nightly_runner.lock` trong `run_nightly_tuner.sh`.
   - Thiết lập môi trường Git Worktree biệt lập (`.worktrees/nightly-*`), ngắt trạng thái HEAD sạch giữa các daemon.
   - Bổ sung rào chắn Empty Push Guard tại `doc_refactor_daemon.py` và cơ chế dọn dẹp nhánh rỗng tự động qua `git cherry` kết hợp kiểm tra an toàn mã thoát.

3. **Tích hợp Real LLM Adapter & Quản trị Ngân sách Token (Wayfinder Ticket 03):**
   - Cung cấp `LLMTaskAdapter` kết nối `GitRatchetOptimizer` với `ccba_ai.client.AIClient.chat_with_metadata()`.
   - Ghi nhận vi đo lường (telemetry) chi tiết qua `TokenUsageTracker`: `prompt_tokens`, `completion_tokens`, `total_tokens`, `total_calls`, và `avg_latency_s`.
   - Cưỡng chế trần ngân sách phiên (mặc định 5,000,000 tokens), cảnh báo sớm ở 90% và dừng an toàn qua `TokenBudgetExceededError`.
   - Cơ chế ngắt mạch Fast-Fail `CircuitBreakerOpenError` khi gặp chuỗi lỗi 429/503.

4. **Bộ dữ liệu chuyên biệt BIM V2 & Bộ chấm điểm Điều phối (Wayfinder Ticket 04):**
   - Xây dựng dataset chuyên biệt `.agents/skills/ccba-eval-gate/test_cases/eval_bigbim_risk.json` gồm 12 ca kiểm thử miền BIM V2 (xung đột Level 2 Space Gap, thuộc tính BBP, Unique ID drift).
   - Bổ sung các Scorer điều phối đa tác tử: `SingleWriterInvariantScorer`, `ProgressiveDisclosureScorer`, `HandoffProtocolScorer` trong `packages/ccba-harness`.

---

### 2. Đánh Giá Giá Trị × Độ Phức Tạp × Rủi Ro (Evaluation Matrix)

| Tiêu Chí | Đánh Giá | Chi Tiết |
| :--- | :--- | :--- |
| **Giá trị Vận hành** | Cực kỳ cao | Biến Nightly Tuner thành cỗ máy tự tối ưu hóa an toàn, không rò rỉ nhánh, đo lường chi phí LLM chính xác |
| **Độ Phức tạp** | Trung bình | Tích hợp sâu vào harness, verifier và cron shell script |
| **Rủi ro Cô lập** | 0% | Ephemeral Worktree và flock ngăn chặn xung đột hoàn toàn với môi trường làm việc chính |
| **Chất lượng Mã** | 100% Pass | Vượt qua toàn bộ bộ kiểm thử đơn vị (68 tests) và 3 preset của `verify-patch` |
