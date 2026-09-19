# 🗺️ Wayfinder Map: Tiến Hóa & Hiện Đại Hóa Nightly Tuner Daemon (Nightly Tuner Evolution)

## 🎯 Điểm Đích (Destination)
Hệ thống tự động hóa tối ưu kỹ năng ban đêm (`Nightly Tuner Daemon` & `Doc-Auto-Evolution`) vận hành 100% tự chủ, ổn định 24/7 trên máy chủ Spark (:8090), đạt chuẩn **ADR-0023**, **ADR-0043**, **ADR-0058** và **ADR-0059**, bao gồm:
1. **100% Đánh Giá Chuẩn Xác & Không Điểm Liệt Giả Lập:** Toàn bộ 73 kỹ năng trong catalog được định tuyến đúng bộ đề thi chuyên biệt, triệt tiêu 100% hiện tượng fallthrough luồng điều khiển và conjunctive deadlock (`bigbim-risk`, `ccba-ai-qc`, Legal skills). *(Giai đoạn 1 đã hoàn thành)*.
2. **Hạ Tầng Git Độc Lập, Khóa Cứng & Tự Dọn Dẹp:** Quản trị vòng đời nhánh Git trơn tru qua Ephemeral Git Worktree, khóa đơn nhiệm `flock`, cách ly giữa các daemons, chặn đứng việc xả nhánh rỗng lên remote và dọn dẹp triệt để nhánh rác mồ côi > 7 ngày. *(Giai đoạn 1 đã hoàn thành)*.
3. **Mở Pull Request Tự Động 100% (Zero-Swallowed Error & Label Self-Healing):** Cơ chế tự động mở PR không bị lỗi khi thiếu nhãn GitHub, có fallback retry không nhãn, ghi log chi tiết mã lỗi stderr và chuẩn hóa UTF-8 subprocess trên Windows/Linux. *(Giai đoạn 2 - Đã hoàn thành)*.
4. **Sẵn Sàng Vận Hành Real LLM Với Token Budget Governance trên Spark (:8090):** Kết nối an toàn với AI Gateway LiteLLM trên máy chủ Spark, kiểm soát trần ngân sách token hàng đêm, circuit breaker ngắt an toàn và đo lường latency/throughput thực tế. *(Giai đoạn 2 - Đã hoàn thành)*.

---

## 📝 Ghi Chú (Notes)
- **Tài liệu tham chiếu & bối cảnh:**
  - `.md/knowledge/issues/nightly-tuner-dirty-tree-crash/DECISION_LOG.md` (Phiên Grilling chốt kiến trúc Ephemeral Worktree)
  - `.agents/proposals/2026-09-18_nightly-tuner-evolution.md` (RFC Proposal PR #286)
  - Phản hồi review từ Copilot trên PR #286 ngày 18/09/2026.
  - Sự cố Nightly Tuner không mở được PR tự động ngày 19/09/2026.
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
- [x] **[T-04 / REC-07] Bộ Đề Thi & Scorer Chuyên Biệt Coordination V2 & Orchestration:** Thiết kế `eval_bigbim_risk.json` (12 câu tình huống Mâu thuẫn thông tin V2, clearance $\ge 900\text{mm}$, $\ge 150\text{mm}$, BBP logic, Unique ID drift); xây dựng bộ `OrchestrationScorers` (`SingleWriterInvariantScorer`, `ProgressiveDisclosureScorer`, `HandoffProtocolScorer`); tích hợp chấm miền tự động trong `get_default_domain_scorers` và định tuyến daemon `bigbim-risk`.
- [x] **[T-05 / Bugfix-20260919] Vá Lỗi Mở PR Tự Động & Hậu Kiểm Copilot Review:** Chuyển đổi nhãn mặc định sang `needs-triage` / `documentation`, bổ sung fallback retry không kèm nhãn, ghi log chi tiết stderr, chuẩn hóa UTF-8 subprocess và so sánh ngày cho branch age cutoff (Merged qua PR #293).
- [x] **[T-06 / Auto-Tune-20260919] Tối Ưu Hóa Kỹ Năng Pháp Lý:** Bổ sung Hard Floor Invariant (NĐ 105/2025/NĐ-CP, QCVN 06:2022/BXD SĐ 1:2023), đưa `ccba-legal-ingest` đạt 100.0% (Merged qua PR #294).
- [x] **[T-07 / Spark-Eval] Khảo Sát Spark LiteLLM Gateway (:8090):** Đánh giá 22 models, chọn `qwen-local-primary` ($0 chi phí, 45.24 tps, không giới hạn rate limit) làm mô hình mặc định cho Nightly Tuner.
- [x] **[T-08 / CI-Fix] Khắc Phục CI GitHub Pages:** Bổ sung `PYTHONPATH: .` và `sys.path` injection cho kiểm thử tính toàn vẹn tài liệu kỹ năng.
- [x] **[T-10 / ADR-0035/0057] Đóng Gói Deep Seam Cho Daemons & Adaptive Rate Limiter:** Đóng gói toàn bộ logic `NightlyTunerDaemon`, `DocAutoEvolutionEngine`, `CodeGroundingEngine`, `PillarBalanceAuditor`, `send_telegram_alert` vào monorepo package `ccba-harness` (`ccba_harness.evals.daemon` và `ccba_harness.docs.daemon`), cắt giảm > 1,200 dòng bloat từ `scripts/eval/` thành Thin CLI Facades < 80 dòng. Triển khai `AdaptiveRateLimiter` (token-bucket + latency backoff) bảo vệ gateway LiteLLM trên Spark (:8090).

---

## 🎫 Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

### Giai Đoạn 1: Cốt Lõi Hạ Tầng & Tối Ưu Hóa (Đã Hoàn Thành)
- [x] **[T-01: Vá Lỗi Đánh Giá, Tháo Gỡ Deadlock BIM & Khắc Phục Lệch Đề Thi](tickets/01_evaluation_logic_and_deadlock_quickfix.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-02: Gia Cố Vận Hành Git, Khóa An Toàn Flock & Dọn Dẹp Nhánh Rác Remote](tickets/02_git_safety_and_remote_branch_lifecycle.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-03: Cầu Nối Adapter Real LLM, Token Budget Ceiling & Circuit Breaker](tickets/03_real_llm_adapter_and_token_governance.md)** `[Research / Task [AFK]]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-04: Xây Dựng Bộ Đề Thi & Scorer Chuyên Biệt Cho Coordination V2 & Orchestration](tickets/04_specialized_domain_datasets_and_scorers.md)** `[Research [AFK] / Prototype [HITL]]` *(ĐÃ HOÀN THÀNH)*

### Giai Đoạn 2: Vận Hành Thực Chiến & Khắc Phục Lỗi Hệ Thống (Đã Hoàn Thành)
- [x] **[T-05: Đóng Gói Bản Vá Post-Merge PR #286, PR Creation Label Fallback & Stderr Logging](tickets/05_pr_creation_label_fallback_and_copilot_review_resolution.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH - [PR #293](https://github.com/vvChu/ccba-agent-platform/pull/293) MERGED)*
- [x] **[T-06: Nghiệm Thu & Chốt Kết Quả Auto-Tune Đêm 19/09 Cho Kỹ Năng ccba-legal-ingest](tickets/06_verify_and_merge_ccba_legal_ingest_nightly_optimization.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH - [PR #294](https://github.com/vvChu/ccba-agent-platform/pull/294) MERGED)*
- [x] **[T-07: Khảo Sát & Đánh Giá Cấu Hình Real LLM trên Máy Chủ Spark (:8090) Cho Nightly Tuner](tickets/07_spark_litellm_real_llm_benchmark_and_deployment.md)** `[Research [AFK]]` *(ĐÃ HOÀN THÀNH - [Báo Cáo Nghiên Cứu](../../knowledge/reports/spark_litellm_nightly_tuner_evaluation.md))*
- [x] **[T-08: Sửa Lỗi CI Deploy Skills Docs to GitHub Pages Đang Thất Bại Trên main](tickets/08_fix_deploy_skills_docs_ci_pipeline.md)** `[Task (AFK)]` *(ĐÃ HOÀN THÀNH)*
- [x] **[T-09: Tối Ưu Hóa Đề Thi Chuyên Biệt, Red-Team Hardening & Thiết Lập Real LLM Cron](tickets/)** `[Task [AFK]]` *(ĐÃ HOÀN THÀNH)*: Khởi tạo `eval_grilling.json` (5 cases, baseline 93.0% trên Qwen Local), `eval_adr_lifecycle.json` (5 cases), `eval_bigbim_risk_redteam.json` (5 cases); bổ sung domain scorers & routers; cập nhật crontab hệ thống với `--use-real-llm --model qwen-local-primary`.
- [x] **[T-10: Đóng Gói Deep Seam Cho Daemons (ADR-0035/0057) & Triển Khai Adaptive Rate Limiter](tickets/)** `[Task [AFK]]` *(ĐÃ HOÀN THÀNH)*: Đóng gói `ccba_harness.evals.daemon` và `ccba_harness.docs.daemon`, refactor `scripts/eval/*.py` thành Thin CLI Facades < 80 dòng; bổ sung `AdaptiveRateLimiter` cho `LLMTaskAdapter`.

---

## 🌫️ Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not yet specified)
- **Tiêu Chí Đánh Giá Chất Lượng Prompt Khi Dùng Real LLM vs Mock Task:** Thiết lập ma trận so sánh điểm số và tính hữu ích thực tế của prompt được tối ưu bằng mô hình thật so với prompt sinh ra từ mô phỏng ngữ nghĩa tĩnh.

---

## 🚫 Ngoài Phạm Vi (Out of scope)
- Thay đổi cấu trúc cơ sở dữ liệu IDOP hoặc các bảng thực thể trong `IDOP-CCBA-WAY`.
- Sửa đổi nội dung hiến chương cốt lõi trong `bigbim-governance` ngoài phạm vi bổ sung từ khóa Uniclass.
- Nâng cấp phần cứng GPU vật lý trên cụm máy chủ Spark (:8090).
