# Ticket 05: Đóng Gói Bản Vá Post-Merge PR #286, PR Creation Label Fallback & Stderr Logging

- **Type:** Task (AFK / Code Implementation)
- **Status:** closed
- **Assignee:** Antigravity AI Agent
- **PR:** [#293](https://github.com/vvChu/ccba-agent-platform/pull/293)
- **Target Seam:** `scripts/eval/nightly_tuner_daemon.py`, `scripts/eval/doc_refactor_daemon.py`, `packages/ccba-harness/src/ccba_harness/evals/tuner.py`, `scripts/cron/run_nightly_tuner.sh`
- **Reference:** Sự cố Nightly Tuner ngày 19/09/2026 & Phản hồi Copilot Review PR #286

---

## 🎯 Mục Tiêu
Khắc phục triệt để sự cố lệnh `gh pr create` thất bại do tham số `--label` không tồn tại (`triage:auto-tuned` / `triage:doc-refactor`) và lỗi nuốt chửng mã lỗi/stderr trong `_create_pull_request`. Đồng thời hoàn thiện toàn bộ các khuyến nghị tồn đọng từ đợt review của Copilot trên PR #286:
1. Chuẩn hóa so sánh ngày `b_date.date() < cutoff_date` trong `_cleanup_old_empty_branches`.
2. Bổ sung `cwd=str(self.root)`, `encoding="utf-8"`, `errors="replace"` (RULE-2.5) cho tất cả lời gọi subprocess.
3. Chuẩn hóa kiểu dữ liệu `budget_ceiling` của `TokenUsageTracker` và trả về `str(res.content)` cho strict mypy.
4. Gỡ bỏ `2>/dev/null || true` tại lệnh checkout worktree trong `run_nightly_tuner.sh`.

---

## 📋 Đặc Tả Kỹ Thuật Chi Tiết

### 1. `scripts/eval/nightly_tuner_daemon.py`:
- [x] Đổi `--label triage:auto-tuned` thành nhãn chuẩn `needs-triage` (có sẵn trên GitHub).
- [x] Bổ sung cờ `--head branch_name`, `cwd=str(self.root)`, `encoding="utf-8"`, `errors="replace"`.
- [x] Bổ sung ghi log chi tiết `err_msg = res.stderr.strip() or f"exit code {res.returncode}"`.
- [x] Bổ sung cơ chế tự phục hồi (Self-healing Fallback): Thử lại lệnh `gh pr create` không kèm `--label` nếu lệnh đầu thất bại.
- [x] Chuẩn hóa so sánh ngày `cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).date()` và `b_date.date() < cutoff_date`.

### 2. `scripts/eval/doc_refactor_daemon.py`:
- [x] Đổi `--label triage:doc-refactor` thành nhãn chuẩn `documentation`.
- [x] Bổ sung `--head branch_name`, fallback retry không kèm `--label`, và logging stderr.
- [x] Bổ sung `encoding="utf-8"`, `errors="replace"`, `check=False` cho các lệnh git rev-parse, git commit, git push, git branch -D.

### 3. `packages/ccba-harness/src/ccba_harness/evals/tuner.py`:
- [x] Gán `budget = config.token_budget if config.token_budget is not None else 5_000_000` trước khi khởi tạo `TokenUsageTracker`.
- [x] Ép kiểu `return str(res.content)` tại `llm_eval_task` để vượt qua strict mypy check `[no-any-return]`.

### 4. `scripts/cron/run_nightly_tuner.sh`:
- [x] Xóa `2>/dev/null || true` tại dòng 180 để bộc lộ lỗi checkout worktree qua ERR trap.

---

## ✅ Tiêu Chí Nghiệm Thu (Acceptance Criteria)
- [x] 1. Kiểm thử hồi quy đơn vị `test_create_pull_request_logs_error_and_retries_without_bad_label` và `test_doc_refactor_pr_creation_logs_error_and_retries_without_bad_label` đạt 100% PASS.
- [x] 2. Toàn bộ 36 tests trong `scripts/tests/test_nightly_tuner_daemon.py`, `scripts/tests/test_doc_refactor_daemon.py`, và `packages/ccba-harness/tests/test_evals_engine.py` đạt 100% PASS.
- [x] 3. `ruff check` đạt 0 lỗi, `mypy` trên `tuner.py` đạt Success: no issues found.
- [x] 4. `python -m ccba_harness verify-patch --preset code` đạt PASS (exit code 0).
- [ ] 5. Mở Pull Request lên GitHub từ branch `fix/nightly-tuner-pr-creation-and-copilot-feedback`.
