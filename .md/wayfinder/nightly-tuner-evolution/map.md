# 🗺️ Wayfinder Map: Tiến Hóa & Hiện Đại Hóa Nightly Tuner Daemon (Nightly Tuner Evolution)

## 🎯 Điểm Đích (Destination)
Hệ thống tự động hóa tối ưu kỹ năng ban đêm (`Nightly Tuner Daemon` & `Doc-Auto-Evolution`) vận hành 100% tự chủ, ổn định 24/7 trên máy chủ Spark (:8090), đạt chuẩn **ADR-0023**, **ADR-0043**, **ADR-0058** và **ADR-0059**, bao gồm:
1. **100% Đánh Giá Chuẩn Xác & Không Điểm Liệt Giả Lập:** Toàn bộ 73 kỹ năng trong catalog được định tuyến đúng bộ đề thi chuyên biệt, triệt tiêu 100% hiện tượng fallthrough luồng điều khiển và conjunctive deadlock (`bigbim-risk`, `ccba-ai-qc`, Legal skills).
2. **Hạ Tầng Git Độc Lập, Khóa Cứng & Tự Dọn Dẹp:** Quản trị vòng đời nhánh Git trơn tru qua Ephemeral Git Worktree, khóa đơn nhiệm `flock`, cách ly giữa các daemons, chặn đứng việc xả nhánh rỗng lên remote và dọn dẹp triệt để nhánh rác mồ côi > 7 ngày.
3. **Sẵn Sàng Mở Rộng Real LLM Với Token Budget Governance:** Kiến trúc adapter thống nhất giữa `ccba_harness.evals.tuner` và `ccba_ai.eval_runner`, tích hợp trần ngân sách token hàng đêm và circuit breaker an toàn khi kết nối vLLM/LiteLLM server.
4. **Bộ Đề Thi & Scorers Đa Miền Chuyên Sâu:** Xây dựng bộ đề kiểm thử chuẩn tắc cho bài toán mâu thuẫn thông tin phi hình học BIM V2 và Scorer chuyên biệt cho các kỹ năng điều phối đa tác tử (Orchestration).

---

## 📝 Ghi Chú (Notes)
- **Tài liệu tham chiếu & bối cảnh:**
  - `.md/knowledge/issues/nightly-tuner-dirty-tree-crash/DECISION_LOG.md` (Phiên Grilling chốt kiến trúc Ephemeral Worktree)
  - `.md/knowledge/issues/nightly-tuner-dirty-tree-crash/issue_tree_analysis.md` (Issue Tree sự cố dirty working tree)
  - `.md/knowledge/issues/nightly-tuner-dataset-mismatch/issue_tree_analysis.md` (Issue Tree sự cố lệch đề thi và bộ chấm)
  - Báo cáo nghiên cứu `/boost` chuyên sâu ngày 18/09/2026.
- **Quy chuẩn thực thi:** Tuân thủ nguyên tắc *Plan, don't do* của Wayfinder; phân tách rạch ròi giữa các Ticket độc lập (~100K token/session), luôn xác minh bằng `python -m ccba_harness verify-patch` trước khi đóng ticket.

---

## ⚖️ Quyết Định Đã Chốt (Decisions so far)
- [x] **[ADR 0043 / Grill-20260918] Cô lập Ephemeral Git Worktree:** Tách biệt 100% runner sang `.worktrees/nightly-runner`, trang bị trap `cleanup_worktree EXIT` và trap `ERR` gọi `telegram_alert.py`.
- [x] **[Grill-20260918] Tham Số Hóa Target Ref:** Bổ sung cờ `--ref <target_ref>` trong `run_nightly_tuner.sh` cho phép điều hướng linh hoạt giữa `origin/main` và `HEAD`.
- [x] **[Grill-20260918] Khởi tạo Domain Archetype Router:** Bổ sung hàm `_resolve_dataset_file` trong `nightly_tuner_daemon.py` và hỗ trợ cặp khóa `dataset_file` / `eval_dataset_file`.
- [x] **[ADR 0058] Khắc phục Subprocess Exit 127:** Cấu hình `sys.executable` fallback trong `ccba_harness.verifier` khi môi trường Linux thiếu lệnh `python`.
- [x] **[T-01 / REC-01..03] Vá Lỗi Đánh Giá & Tháo Gỡ Deadlock:** Hợp nhất `if-elif` trong `mock_agent_task`, thu hẹp từ khóa BIM, bổ sung Trí Nhớ Số vào Strategy 1 BIM, bổ sung Luật 135/2025 vào legal fallback, điều hướng `ccba-ai-qc` sang redteam dataset; đưa `bigbim-risk`, `ccba-ai-qc`, `ccba-legal-intel` đạt 100.0%.
- [x] **[T-02 / REC-04..06] Khóa Đơn Nhiệm Flock & Quản Trị Vòng Đời Nhánh Git:** Bổ sung `flock -n 200` tại `/tmp/ccba_nightly_runner.lock`, Empty Push Guard trong `doc_refactor_daemon.py`, cách ly HEAD sạch giữa daemons, mở rộng `_cleanup_old_empty_branches` đối soát `origin/main` và dọn dẹp remote branch rỗng.
- [x] **[T-03 / REC-08] Cầu Nối Real LLM Adapter, Token Budget Ceiling & Circuit Breaker:** Xây dựng `TokenUsageTracker` và `LLMTaskAdapter` trong `tuner.py`, kết nối `AIClient.chat_with_metadata`, giới hạn trần ngân sách token hàng đêm (mặc định 5M tokens) với fail-safe early halt `TokenBudgetExceededError`, và ngắt an toàn với `CircuitBreakerOpenError`. Chuyển tiếp cấu hình `--use-real-llm`, `--token-budget`, `--model` qua daemon và shell runner.

---

## 🎫 Danh Sách Ticket Tại Biên Giới (Frontier Tickets)
- [x] **[T-01: Vá Lỗi Đánh Giá, Tháo Gỡ Deadlock BIM & Khắc Phục Lệch Đề Thi](tickets/01_evaluation_logic_and_deadlock_quickfix.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-02: Gia Cố Vận Hành Git, Khóa An Toàn Flock & Dọn Dẹp Nhánh Rác Remote](tickets/02_git_safety_and_remote_branch_lifecycle.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-03: Cầu Nối Adapter Real LLM, Token Budget Ceiling & Circuit Breaker](tickets/03_real_llm_adapter_and_token_governance.md)** `[Research / Task [AFK]]` *(ĐÃ HOÀN THÀNH)*
- [ ] **[T-04: Xây Dựng Bộ Đề Thi & Scorer Chuyên Biệt Cho Coordination V2 & Orchestration](tickets/04_specialized_domain_datasets_and_scorers.md)** `[Research [AFK] / Prototype [HITL]]` *(UNBLOCKED - Ưu tiên tiếp theo)*

---

## 🌫️ Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not yet specified)
- **Hạ Tầng vLLM / LiteLLM Spark (:8090):** Khi chuyển sang Real LLM, cần xác định mô hình tối ưu cho Evaluator (Gemini 3.7 Flash vs Qwen-2.5-72B local) và cơ chế batching chống quá tải GPU.
- **Chính Sách Quyền Token GitHub PAT:** Cần kiểm tra xem PAT chạy cron trên Server Spark có quyền `delete-branch` trên remote `origin` hay không để thực hiện dọn dẹp từ xa.
- **Tiêu Chí Chấm Điểm Cho Orchestration:** Định nghĩa rõ barem điểm đo lường tính toàn vẹn của Single-Writer Pattern và AST Link Integrity mà không dựa dẫm vào regex thô sơ.

---

## 🚫 Ngoài Phạm Vi (Out of scope)
- Thay đổi cấu trúc cơ sở dữ liệu IDOP hoặc các bảng thực thể trong `IDOP-CCBA-WAY`.
- Sửa đổi nội dung hiến chương cốt lõi trong `bigbim-governance` ngoài phạm vi bổ sung từ khóa Uniclass.
