# Walkthrough: PR #286 — Hiện Đại Hóa Nightly Auto-Tuner Daemon, Real LLM Adapter & Multi-Domain Evals

## 1. Tổng Quan PR #286
- **Branch:** `feat/nightly-tuner-worktree-and-dataset-router` $\rightarrow$ `main`
- **Tiêu đề:** `feat(tuner): modernize nightly auto-tuner daemon, real llm adapter, and domain evals`
- **PR liên quan:** [PR #286](https://github.com/vvChu/ccba-agent-platform/pull/286)
- **Commit hợp nhất:** `df311bb66cc53dc4f3888ada8b060a83a9fc2d57`
- **Thể chế & Kiến trúc:** ADR-0023, ADR-0045, ADR-0047, ADR-0057, ADR-0058, Wayfinder Roadmap `nightly-tuner-evolution`

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #286)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| Inline 1 | `packages/ccba-harness/src/ccba_harness/evals/tuner.py:113` | `LLMTaskAdapter` chuyển `circuit_breaker` sang `AIClient` nhưng không khởi tạo mặc định khi không truyền vào, khiến fast-fail `CircuitBreakerOpenError` không kích hoạt trong thực tế. | **ĐÃ KHẮC PHỤC**: Cập nhật `LLMTaskAdapter.__init__` tự động gán `self.circuit_breaker = circuit_breaker or (CircuitBreaker() if CircuitBreaker is not None else None)` và truyền xuống `AIClient`. |
| Inline 2 | `packages/ccba-harness/src/ccba_harness/evals/tuner.py:195` | `CCBA_TUNER_TOKEN_BUDGET` ghi đè vô điều kiện `RatchetConfig.token_budget` ngay cả khi người gọi đã truyền giá trị tường minh (e.g. `remaining_budget` từ daemon). | **ĐÃ KHẮC PHỤC**: Chuyển `token_budget` thành `int | None = None` và chỉ nạp từ biến môi trường nếu `self.token_budget is None`, bảo vệ toàn vẹn ngân sách token của daemon. |
| Inline 3 | `packages/ccba-harness/src/ccba_harness/evals/tuner.py:1275` | Rào chắn compaction guard chỉ loại bỏ dòng comment HTML `<!-- Ratchet Optimization Refinement ... -->` nhưng bỏ sót dòng bullet `- Cập nhật quy chuẩn...` dẫn đến tích tụ dòng thừa. | **ĐÃ KHẮC PHỤC**: Cập nhật bộ lọc compaction guard loại bỏ cả 2 dòng comment và dòng bullet tự sinh, ngăn ngừa phình to prompt vượt quá 300 dòng. |
| Inline 4 | `scripts/eval/nightly_tuner_daemon.py:236` | `NightlyTunerDaemon` nhận `early_stopping_patience` nhưng không truyền vào `RatchetConfig(patience=...)`, khiến tuner luôn dùng mặc định `patience=3`. | **ĐÃ KHẮC PHỤC**: Nối tham số `patience=self.early_stopping_patience` trực tiếp vào khởi tạo `RatchetConfig`. |
| Inline 5 | `scripts/eval/nightly_tuner_daemon.py:415, 445` | `_cleanup_old_empty_branches` xóa nhánh khi `git cherry` trả về rỗng nhưng không kiểm tra mã thoát; thiếu `encoding="utf-8", errors="replace"` cho Windows subprocess. | **ĐÃ KHẮC PHỤC**: Thêm `encoding="utf-8", errors="replace"` và kiểm tra chặt `diff_res.returncode == 0 and not diff_res.stdout.strip()` trước khi xóa nhánh. |
| Inline 6 | `scripts/cron/run_nightly_tuner.sh:172` | `PYTHONPATH` được thiết lập từ `$PROJECT_ROOT` trước khi `cd $WORKTREE_DIR`, khiến các tiến trình con có thể import mã từ thư mục chính thay vì worktree cô lập. | **ĐÃ KHẮC PHỤC**: `cd "$WORKTREE_DIR"` trước và thiết lập `PYTHONPATH` trỏ vào `$WORKTREE_DIR`, đảm bảo tính cô lập tuyệt đối của ephemeral worktree. |
| Inline 7 | `packages/ccba-harness/tests/test_evals_engine.py:355` | `test_llm_rubric_scorer_corrupted_db_fallback` đã loại bỏ các assertion gọi `score()`, không kiểm chứng được luồng fallback thực tế. | **ĐÃ KHẮC PHỤC**: Khôi phục gọi `scorer.score()` và assert `client.calls == 1`, `res.score == 1.0`, `res.raw_output == 5`. |
| Inline 8 | `scripts/tests/test_nightly_tuner_daemon.py:202` | `test_tuner_tiered_budget_and_early_stopping` chỉ kiểm tra gán `patience`, không chạy optimizer hoặc kiểm tra dừng sớm; trỏ vào tệp SKILL thật. | **ĐÃ KHẮC PHỤC**: Nâng cấp kiểm thử với môi trường cô lập `tmp_path`, mock dataset và mock task để kiểm chứng cả 2 hành vi: kẹp ngân sách 1 vòng khi baseline 100% và dừng sớm sau `effective_patience` vòng lặp. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)
1. **Wayfinder Ticket 01 (Evaluation Control Flow & Deadlock Resolution):**
   - Loại bỏ fall-through trong `mock_agent_task` bằng thang `if-elif`.
   - Tiêm bất biến *Trí Nhớ Số (Digital Memory)* vào Chiến lược 1 giải phóng deadlock tam hợp miền BIM.
   - Chuẩn hóa routing dataset cho `ccba-ai-qc` (`eval_pccc_audit_redteam.json`) và bổ sung từ khóa Luật 135/2025.
2. **Wayfinder Ticket 02 (Git Safety, Process Locking & Remote Branch Pruning):**
   - Khóa tiến trình `flock -n 200` tại `/tmp/ccba_nightly_runner.lock` trong cron runner.
   - Cô lập Git Worktree tạm thời (`.worktrees/nightly-*`), ngắt `detached HEAD` giữa các daemon.
   - Bổ sung Empty Push Guard tại `doc_refactor_daemon.py` và dọn dẹp remote branch an toàn.
3. **Wayfinder Ticket 03 (Unified Real LLM Adapter, Token Budget Ceiling & Circuit Breaker):**
   - Bộ điều hợp `LLMTaskAdapter` kết nối `GitRatchetOptimizer` với `ccba_ai.client.AIClient.chat_with_metadata()`.
   - Theo dõi tiêu thụ token phiên qua `TokenUsageTracker` và trần ngân sách 5M tokens.
   - Ngắt mạch tức thì `CircuitBreakerOpenError` khi gặp 3 lỗi 429/503 liên tiếp.
4. **Wayfinder Ticket 04 (Specialized BIM V2 Dataset & Orchestration Domain Scorers):**
   - Bộ dữ liệu `eval_bigbim_risk.json` (12 test cases) đánh giá xung đột phi hình học BIM V2.
   - Bộ 3 Scorers điều phối đa tác tử: `SingleWriterInvariantScorer`, `ProgressiveDisclosureScorer`, `HandoffProtocolScorer`.

---

# Walkthrough: PR #287 — Nâng Cấp ccba-issue-tree v1.1.0, Tra Cứu Tri Thức Liên-Spoke 3 Tầng & Đồng Bộ README

## 1. Tổng Quan PR #287
- **Branch:** `feat/issue-tree-and-hub-mediated-discovery` $\rightarrow$ `main`
- **Tiêu đề:** `feat(issue-tree,legal-intel): enhance ccba-issue-tree v1.1.0, hub-mediated discovery & sync parity`
- **PR liên quan:** [PR #287](https://github.com/vvChu/ccba-agent-platform/pull/287)
- **Thể chế & Kiến trúc:** ADR-0050 (Spoke Knowledge Sync), ADR-0051 (Virtual Hub Fallback), ADR-0057 (Two-Stage Governance & GPI), ADR-0058 (Hard Completion Lock), ADR-0059 (Verbatim Grounding & Acquisition First)

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #287)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4044184663` | `packages/ccba-notebooklm/src/ccba_notebooklm/_security.py` | `sanitize_prompt_for_query()` nuốt lỗi khi Maskara gặp exception bất ngờ (fail-open), làm rò rỉ prompt chưa làm sạch sang NotebookLM. | **ĐÃ KHẮC PHỤC**: Áp dụng nguyên tắc "Fail-Closed" tuyệt đối: khi phát hiện lỗi bất ngờ trong quá trình làm sạch prompt qua Maskara, lập tức raise `RuntimeError("Kiểm tra bảo mật Maskara Gate thất bại (Fail-Closed)")`. |
| `4044184708` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py` | `is_port_open()` có thể bị truyền tham số timeout lớn hơn 1.0s hoặc số âm/0 gây treo socket trên Windows. | **ĐÃ KHẮC PHỤC**: Cưỡng chế trần cứng `safe_timeout = max(0.05, min(float(timeout), 1.0))` ngay bên trong hàm để bảo vệ socket probe an toàn trên Windows. |
| `4044184735` | `.agents/skills/ccba-issue-tree/references/governed_lifecycle_guide.md` | Ví dụ chứng cứ mã băm dùng URI `file:///C:/...` vi phạm quy tắc cấm `file:///` trong tài liệu. | **ĐÃ KHẮC PHỤC**: Thay thế bằng placeholder đa nền tảng `<ABSOLUTE_LOG_PATH>/runner_deadlock_trace.log#L340-L385`. |
| `4044184756` | `.md/knowledge/research_and_studies/research-ccba-issue-tree-upgrade-proposals.md` | Tài liệu nghiên cứu dùng các liên kết tuyệt đối `file:///...` vi phạm quy tắc documentation parity. | **ĐÃ KHẮC PHỤC**: Thay thế 100% các link `file:///` thành repo-relative links (`../../../.agents/skills/...`). |
| `4044251104` | `packages/ccba-notebooklm/src/ccba_notebooklm/_security.py` | `sanitize_prompt_for_query()` trở thành silent no-op khi `ccba_maskara` không khả dụng (fail-open), khiến query chứa API key vẫn bị gửi đi. | **ĐÃ KHẮC PHỤC**: Bổ sung fallback regex scanner phát hiện các mẫu khóa nhạy cảm phổ biến (`sk-`, `ghp_`, `gho_`, `AIza`, `sk-ant-`) và chặn đứng với `ValueError` (Fail-Closed) kèm cảnh báo ra `sys.stderr` khi `ccba_maskara` vắng mặt; bổ sung unit test kiểm chứng. |
| `PRR_kwDOQzfV088AAAABOJzN7w` (Suppressed 1) | `packages/ccba-harness/tests/test_issue_tree_contract.py` | `lint_issue_tree_output()` chỉ kiểm tra có ít nhất một nhãn MECE (`found_any`), trong khi hợp đồng yêu cầu kiểm tra đầy đủ cả bộ nhãn chuẩn tắc. | **ĐÃ KHẮC PHỤC**: Sửa hàm linter yêu cầu có đầy đủ toàn bộ bộ 4 nhãn MECE chuẩn (`[ANALYSIS]`, `[DECISION]`, `[COMMITMENT]`, `[SYNTHESIS]`) khi phát hiện What-Tree/gói việc và báo rõ các nhãn bị thiếu; bổ sung test case kiểm chứng hợp đồng. |
| `PRR_kwDOQzfV088AAAABOJzN7w` (Suppressed 2) | `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py` | `find_local_knowledge_corpus()` nuốt toàn bộ lỗi (`except Exception: pass`) trong quá trình tìm kiếm qua Hub, có thể ẩn giấu lỗi IO/YAML thực tế. | **ĐÃ KHẮC PHỤC**: Thu hẹp ngoại lệ thành `except (OSError, yaml.YAMLError) as e:` kèm ghi log debug; xử lý an toàn `except OSError:` cho candidate paths và bổ sung test case kiểm thử. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)
1. **ccba-issue-tree (v1.1.0):** Tích hợp Adaptive Fast-Tree vs Full-Tree, OS & Shell Awareness Guard (bảo vệ Windows PowerShell), Cascading Branch Pruning, và bộ kiểm thử tự động `eval_ccba_issue_tree.json` (3/3 pass).
2. **Kiến trúc Tra cứu Tri thức Liên-Spoke 3 Tầng:** Tầng 1 Virtual Spoke Fallback qua AST/CLI nguyên tử (`get-clause`, $<500$ tokens), Tầng 2 AI Gateway Legal RAG trên Server Spark (:8090), Tầng 3 Cloud Fallback qua Google NotebookLM. Tự động khám phá qua `spoke_registry_decrypted.yaml` trên Hub.
3. **Cập nhật Pháp lý Hiện Hành:** Cập nhật Luật Xây dựng 2025 (`135/2025/QH15`), Nghị định 217/2026/NĐ-CP, và Nghị định 207/2026/NĐ-CP vào `ccba-completion-checklist`.
4. **Đồng bộ Tài liệu & Quick Start:** Chuẩn hóa 9 packages monorepo (`ccba-qc-core`), 73 skills trong `README.md` và bổ sung 3 slash commands hạt nhân (`/ccba-issue-tree`, `/ccba-create-pr`, `/ccba-legal-advisor`).
5. **Nén Bộ Nhớ Làm Việc (Tiered Memory Model):** Đạt chuẩn $9.99\text{ KB} \le 10.0\text{ KB}$ cho `session_learnings.md` (bảo toàn 14 invariants bắt buộc).

---

# Walkthrough: PR #284 — Giao Thức TRIHT (Release Cleanliness & Hermetic Teardown Gate)

## 1. Tổng Quan PR #284
- **Branch:** `feat/release-hermetic-cleanliness-gate` $\rightarrow$ `main`
- **Tiêu đề:** `feat(release): implement TRIHT protocol cleanliness gate and hermetic scoped teardown`
- **PR liên quan:** [PR #284](https://github.com/vvChu/ccba-agent-platform/pull/284)
- **Thể chế & Kiến trúc:** ADR-0058 (Hard Completion Lock), ADR-0057 (Two-Stage Governance), TRIHT Protocol

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #284)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4035452784` | `.agents/skills/ccba-release-feature/SKILL.md` | Lệnh `git checkout --no-pager main` không đúng cú pháp: `--no-pager` là global option của `git` và phải đứng sau `git` (`git --no-pager checkout main`). | **ĐÃ KHẮC PHỤC**: Đã cập nhật cú pháp chuẩn: `git --no-pager checkout main && git pull origin main` tại dòng 146 của `SKILL.md`. |
| `4035452828` | `scripts/validation/check_release_cleanliness.py` | Nếu `git status` thất bại hàm đang `return []` (fail-open), khiến release gate hiểu nhầm repo sạch. | **ĐÃ KHẮC PHỤC**: Chuyển sang cơ chế "Fail-Closed" tuyệt đối: khi gặp `CalledProcessError` hoặc `FileNotFoundError`, trả về sentinel `[("!!", f"GIT_STATUS_FAILED: {e}")]` chặn đứng tiến trình release. |
| `4035452859` | `scripts/validation/check_release_cleanliness.py` | Khối teardown ghép path mà không ràng buộc nằm trong `repo_root` (nguy cơ path traversal), và ignore_errors nuốt lỗi xóa. | **ĐÃ KHẮC PHỤC**: Thêm rào chắn an ninh `abs_path.resolve().relative_to(root.resolve())` chống path traversal, kiểm tra `not abs_path.exists()` sau xóa và cảnh báo lỗi nếu tệp vẫn tồn tại. |
| `4035452897` | `scripts/tests/test_check_release_cleanliness.py` | Chưa có test bao phủ trường hợp `git status` thất bại (CalledProcessError / FileNotFoundError) kiểm chứng fail-closed. | **ĐÃ KHẮC PHỤC**: Bổ sung 2 unit tests `test_get_porcelain_status_git_error_fails_closed` và `test_get_porcelain_status_git_not_found_fails_closed` (11/11 tests pass). |
| `4035869238` | `scripts/validation/check_release_cleanliness.py` | `run_post_check` tự động xóa tệp tracked nếu tên khớp `KNOWN_TEST_ARTIFACTS`. | **ĐÃ KHẮC PHỤC**: Đảm bảo tệp tracked bị `M/D/A/R/C/U` luôn luôn bị chặn (BLOCK) và không bao giờ bị xóa tự động. Chỉ tệp untracked (`??`) khớp danh mục cache mới được thu hồi an toàn. Đã bổ sung test `test_run_post_check_does_not_purge_tracked_modified_known_artifact`. |
| `4035905024` | `scripts/validation/check_release_cleanliness.py` | Gọi `sys.stdout/sys.stderr.reconfigure()` ở module level vi phạm repo guidance và phá vỡ pytest I/O capture trên Windows. | **ĐÃ KHẮC PHỤC**: Di dời toàn bộ stream reconfiguration vào bên trong CLI entrypoint `main()`. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Cổng 0.1 (Pre-Flight Cleanliness Lock):** Chặn đứng quy trình trước khi chạy test nếu phát hiện tệp chưa commit, bảo toàn 100% mã nguồn của kỹ sư.
2. **Cổng 0.3 (Post-Test Hermetic Scoped Teardown):** Đối soát trạng thái sau khi chạy integration tests, tự động thu hồi an toàn các cache kiểm thử đã biết (`embeddings.npy`, `ci_log.txt`, `tmp_*.json`) kèm cảnh báo vàng; chặn đứng nếu có bài test làm thay đổi mã nguồn hoặc tệp lạ.
3. **Tiện ích CLI Chuyên Trách ([`check_release_cleanliness.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/validation/check_release_cleanliness.py)):** Xây dựng công cụ kiểm tra độc lập hỗ trợ `--phase pre` và `--phase post`, tương thích tuyệt đối Windows UTF-8 (`sys.stdout.reconfigure`), xử lý tệp qua `git status --porcelain -z` (null-terminated), fail-closed khi lỗi, và chống path traversal.
4. **Nâng Cấp Kỹ Năng ([`ccba-release-feature`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-release-feature/SKILL.md)):** Tích hợp Cổng 0.1 và Cổng 0.3 vào Bước 0; bổ sung dọn dẹp tiến trình mồ côi (`ensure_single_instance('pytest')`) và `git --no-pager checkout main` cho Bước 3.2 chuyển nhánh an toàn.
5. **Bộ Kiểm Thử Tự Động ([`test_check_release_cleanliness.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/tests/test_check_release_cleanliness.py)):** 11 unit tests kiểm tra toàn diện cả 2 phase pre/post, fail-closed, cách ly path traversal và bảo vệ tệp tracked (100% pass).
6. **Giải Quyết Sự Cố CI Runner Treo & Architecture Drift:** Kế thừa bản vá process safety (`ancestor_pids` guard, CI bypass) từ PR #281 và đăng ký `scripts/validation/` vào `README.md`.

---

## 4. Kết Quả Kiểm Định CI Cuối Cùng Trên GitHub Actions (PR #284)

- **`validate` (Documentation Check):** ✅ PASS (24s)
- **`scan` (Security & Privacy):** ✅ PASS (12s)
- **`Lint Markdown`:** ✅ PASS (10s)
- **`Test - Python 3.10`:** ✅ PASS (3m25s)
- **`Test - Python 3.11`:** ✅ PASS (3m5s)
- **`Test - Python 3.12`:** ✅ PASS (2m23s)

**Tổng kết:** 6/6 Checks PASS 100%. Trạng thái `CLEAN` / `MERGEABLE`.

---

# Walkthrough: PR #283 — Dynamic Base Branch Detection cho ccba-create-pr (v1.2.0)

## 1. Tổng Quan PR #283
- **Branch:** `proposal/dynamic-base-branch-for-create-pr` $\rightarrow$ `main`
- **Tiêu đề:** `feat(skill): dynamic base branch detection for ccba-create-pr (v1.2.0)`
- **PR liên quan:** [PR #283](https://github.com/vvChu/ccba-agent-platform/pull/283)
- **Đề xuất bởi Spoke:** `dgx-spark-toolkit` (specialized_extension)
- **Thể chế & Kiến trúc:** ADR-0045 (Spoke Leakage & Proposal Governance), ADR-0047 (Catalog Governance), ADR-0056 (Upstream Contribution Loop), ADR-0058 (Hard Completion Lock)

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #283)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4033766114` | `.agents/skills/ccba-create-pr/SKILL.md` | Lệnh `gh pr create` dùng chuỗi xuống dòng kiểu PowerShell (`` `n ``) bên trong code block `bash`. | **ĐÃ KHẮC PHỤC**: Cập nhật sang cú pháp bash chuẩn: `gh pr create --title "<Title>" --body "<Body>\n\nCloses #<id>" --base <default_branch> --head <current_branch>`. |
| `4033766141` | `.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md` | Link `file:///home/vvc/...` là đường dẫn tuyệt đối theo máy cá nhân. | **ĐÃ KHẮC PHỤC**: Loại bỏ hoàn toàn đường dẫn tuyệt đối, chuyển sang relative path `../skills/ccba-create-pr/SKILL.md`. |
| `4033766164` | `.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md` | Đoạn snippet phát hiện nhánh chính phụ thuộc `sed` và fallback chỉ `main`/`master`. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa cơ chế tự động xác định nhánh chính qua `git symbolic-ref --short refs/remotes/origin/HEAD` và fallback native git. |
| `4033766190` | `.agents/skills/ccba-create-pr/SKILL.md` | Bước 0 thiếu lệnh git cụ thể lấy `origin/HEAD` để xác định `<default_branch>`. | **ĐÃ KHẮC PHỤC**: Đã bổ sung rõ ràng lệnh `git symbolic-ref --short refs/remotes/origin/HEAD` vào Bước 0 của `SKILL.md`. |
| `4033809116` | `packages/ccba-ai/pyproject.toml` | Thay đổi pin `mcp` thành `<2.0.0` nằm ngoài phạm vi mô tả của PR. | **ĐÃ KHẮC PHỤC**: Hoàn nguyên `packages/ccba-ai/pyproject.toml` về nguyên bản trên `main`, loại bỏ hoàn toàn thay đổi ngoài phạm vi. |
| `4033855890` | `.agents/skills/ccba-create-pr/SKILL.md` | Cần lệnh git xác định và tự đủ để agent suy ra `<default_branch>`. | **ĐÃ KHẮC PHỤC**: Bổ sung `git symbolic-ref --short refs/remotes/origin/HEAD` tại Bước 0 đảm bảo tính tự lập (self-contained). |
| `4033855941` | `packages/ccba-harness/tests/test_tuner.py` | Ba dòng trống trước test function vi phạm ruff/PEP8 E303. | **ĐÃ KHẮC PHỤC**: Đã định dạng chuẩn 2 blank lines và pass 100% ruff check. |
| `4034010442` | `.agents/skills/ccba-create-pr/SKILL.md` | PR thay đổi nhiều package và config ngoài phạm vi ban đầu. | **ĐÃ KHẮC PHỤC**: Đã merge đồng bộ với `main`, hoàn nguyên các file ngoài phạm vi, chỉ tập trung vào skill và proposal. |
| `4034040496` | `scripts/governance/drift_auditor.py` | Bộ lọc `"/tests/" not in filepath` không loại trừ `tests/...` ở repo root. | **ĐÃ KHẮC PHỤC**: Đã đồng bộ với `main` mới nhất, toàn bộ test suite pass 100%. |
| `4034040536` | `.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md` | Section 3 mô tả `$DEFAULT_BRANCH` trong khi Hub skill dùng `<default_branch>`. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa toàn bộ Section 1 và Section 3 đồng bộ với placeholder `<default_branch>`. |
| `4036350143` | `.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md` | Section 3 RFC chỉ liệt kê tệp skill trong khi PR có các tệp phụ trợ. | **ĐÃ KHẮC PHỤC**: Cập nhật Section 3 của RFC phân tách rõ tệp trọng tâm và các thay đổi phụ trợ đồng bộ hệ thống. |
| `4036387067` | `.md/knowledge/reports/walkthrough.md` | Đường dẫn `file:///d:/...` là tuyệt đối cục bộ, không portable khi render trên GitHub. | **ĐÃ KHẮC PHỤC**: Chuyển toàn bộ link sang relative path chuẩn repo. |
| `PRR_kwDOQzfV088AAAABOAkS_g` | `.md/knowledge/reports/walkthrough.md`, `.agents/skills/ccba-create-pr/SKILL.md` | Đường dẫn tuyệt đối trong walkthrough và định dạng newline trong ví dụ gh pr create. | **ĐÃ KHẮC PHỤC**: Đã chuyển relative links trong walkthrough và chuẩn hóa `--body "$PR_BODY"` trong `SKILL.md`. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Nâng cấp Kernel Skill ([`ccba-create-pr`](../../.agents/skills/ccba-create-pr/SKILL.md)):**
   - Bump version từ `1.1.0` $\rightarrow$ `1.2.0`.
   - Bổ sung lệnh `git symbolic-ref --short refs/remotes/origin/HEAD` tại Bước 0 để xác định nhánh mặc định (`<default_branch>`).
   - Loại bỏ giả định ngầm hardcode `main`, tương thích hoàn hảo với cả `master` và các Spoke đa dạng.
   - Sử dụng placeholder `<default_branch>` xuyên suốt từ Bước 0 đến Bước 3 (`gh pr create --base <default_branch>`).
2. **RFC Proposal Chuẩn Hóa ([`2026-09-17_dynamic-base-branch-for-create-pr.md`](../../.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md)):**
   - Đầy đủ 4 trường metadata bắt buộc (`proposal_id`, `type`, `name`, `status`) và project provenance (`proposed_by_project: dgx-spark-toolkit`).
   - Đánh giá theo ma trận Giá trị $\times$ Rủi ro $\times$ KISS (Value: Rất cao, Risk: 0%, Complexity: Rất thấp).
3. **Bảo toàn Tính Toàn Vẹn Hệ Thống (Governance & Integrity):**
   - Bổ sung rào chắn placeholder `<...>` trong `tests/governance/test_global_skills_integrity.py`.
   - Đạt 100% PASS kiểm định `check_spoke_leakage.py`, `validate_skills.py --enforce-gpi`, và `compile_catalog.py --check`.

---

## 4. Kết Quả Kiểm Định CI Cuối Cùng Trên GitHub Actions (PR #283)

- **`validate` (Documentation Check):** ✅ PASS (26s)
- **`scan` (Security & Privacy):** ✅ PASS (10s)
- **`Lint Markdown`:** ✅ PASS (11s)
- **`Test - Python 3.10`:** ✅ PASS (3m26s)
- **`Test - Python 3.11`:** ✅ PASS (3m7s)
- **`Test - Python 3.12`:** ✅ PASS (3m37s)

**Tổng kết:** 6/6 Checks PASS 100%. Trạng thái `CLEAN` / `MERGEABLE`.

---

# Walkthrough: Issue #285 — Kiến Trúc Tham Chiếu Zero-Bloat & Gia Cố Phân Quyền Windows/OneDrive

## 1. Tổng Quan Issue #285
- **Branch:** `refactor/issue-285-zero-bloat-legal-sync-onedrive-hardening`
- **Tiêu đề:** `refactor(legal-sync): adopt Zero-Bloat reference architecture for Spokes and harden Windows/OneDrive permissions`
- **Issue liên quan:** [#285](https://github.com/vvChu/ccba-agent-platform/issues/285)
- **Thể chế & Kiến trúc:** ADR-0050 (Spoke Knowledge Sync), ADR-0051 (Virtual Hub Fallback & Zero-Bloat), ADR-0058 (Hard Completion Lock), RULE-2.7 (Safe Remove)

---

## 2. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Triệt tiêu nhân bản vật lý (Zero-Bloat Reference Mode - ADR-0051):**
   - Mặc định khi chạy `sync_spoke.py` hoặc `LegalKnowledgeSyncOrchestrator`, hệ thống kích hoạt chế độ **Reference-Only**, chỉ cập nhật siêu dữ liệu `legal_registry.yaml` mà không tự động sao chép hàng trăm MB tài liệu PDF/DOCX sang Spoke.
   - Cung cấp cờ tường minh `--pull-assets` khi cần tải trọn bộ tài liệu về Spoke để làm việc offline biệt lập.
2. **Gia cố an toàn tệp tin trên Windows / OneDrive:**
   - Loại bỏ hoàn toàn `shutil.rmtree(dest_subdir)` gây lỗi crash `PermissionError: [WinError 5] Access is denied`.
   - Thay thế bằng `shutil.copytree(item, dest_subdir, dirs_exist_ok=True, copy_function=safe_copy2)`.
   - `safe_copy2` tự động nhận diện và gỡ cờ Read-Only (`stat.S_IWRITE | stat.S_IREAD`) trên tệp đích trước khi ghi đè.
   - `safe_remove` (RULE-2.7) nhận diện NTFS Directory Junctions / Mount Points trên Windows, xử lý an toàn với `onexc`/`onerror` hook và retry loop xử lý khóa tệp `WinError 32`.
   - Gia cố `LegalRegistryManager.save()` gỡ cờ Read-Only trước khi ghi đè và hỗ trợ retry backoff chống xung đột lock với OneDrive daemon.
3. **Rào chắn Self-Copy trên Master Legal Corpus:**
   - Ngăn chặn triệt để nguy cơ `shutil.SameFileError` và hủy hoại SSOT khi chạy sync ngay tại repo `ccba-legal-knowledge`.
4. **Bảo tồn Hard Completion Lock (ADR-0058):**
   - Bổ sung cờ `--reference-only` vào CLI `ccba-legal sync` và `--pull-assets` vào `sync_spoke.py`/`ccba_platform_cli.py`.

---

## 3. Kết Quả Kiểm Định Tự Động (Deterministic Hard Completion Verification)

- **`verify-patch` (ccba_harness):** ✅ **ALL 4/4 COMMANDS PASSED (Exit Code 0)**
  - `pytest packages/ccba-legal-intel/tests/test_zero_bloat_sync.py ...`: 24/24 passed (100%)
  - `pytest scripts/tests/test_spoke_sync_modules.py -v`: 35/35 passed (100%)
  - `ruff check packages/ccba-legal-intel/ scripts/spoke/ scripts/ccba_platform_cli.py`: PASS (0 errors)
  - `mypy packages/ccba-legal-intel/src/ccba_legal/sync/ scripts/spoke/sync/ --ignore-missing-imports`: PASS (0 errors)

---

## 4. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #290)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4051355934` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:190` | `safe_remove()` gọi `os.rmdir()` cho mọi đường dẫn thỏa `is_dir()` và `_is_link_or_junction()`. Trên POSIX, symlink trỏ tới thư mục làm `Path.is_dir()` trả về `True`, nhưng symlink phải được gỡ bằng `unlink()`, không phải `rmdir()`; điều này có thể ném `NotADirectoryError`. | **ĐÃ KHẮC PHỤC**: Phân nhánh rõ ràng: chỉ gọi `os.rmdir(p)` khi `os.name == "nt" and p.is_dir() and not p.is_symlink()` (NTFS directory junction / mount point trên Windows); các symlink POSIX và Windows thông thường đều dùng `p.unlink()`. |
| `4051355961` | `packages/ccba-legal-intel/tests/test_zero_bloat_sync.py:256` | Kiểm thử junction dựa vào module nội bộ `_winapi` và gọi `_winapi.CreateJunction` vô điều kiện. `CreateJunction` có thể khuyết thiếu trên một số bản dựng Python/Windows. | **ĐÃ KHẮC PHỤC**: Thêm khối `try/except ImportError` và kiểm tra `hasattr(_winapi, "CreateJunction")` để `pytest.skip()` an toàn khi môi trường không hỗ trợ. |
| `4051391194` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:186` | `safe_remove()` gọi `os.chmod(p, ...)` cả khi `p` là symlink, làm thay đổi quyền của target file trên POSIX. | **ĐÃ KHẮC PHỤC**: Thêm điều kiện `if not p.is_symlink():` trước khi chmod; symlink được unlink trực tiếp không can thiệp target file. |
| `4051413719` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:208` | `safe_remove()` xóa cây thư mục qua `shutil.rmtree` có thể đệ quy vào trong NTFS directory junction trên Windows, xóa nhầm dữ liệu bên ngoài cây mục tiêu. | **ĐÃ KHẮC PHỤC**: Thay thế `shutil.rmtree` bằng `_safe_rmtree_tree` đệ quy kiểm tra `_is_link_or_junction(entry)` trước khi duyệt, đối xử junction/symlink như leaf node (`os.rmdir`/`unlink`) không bao giờ đệ quy vào trong target; bổ sung test case `test_safe_remove_directory_with_nested_junction`. |
| `4051442353` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:191` | `os.chmod(p, stat.S_IWRITE | stat.S_IREAD)` gán mode tuyệt đối `0o600` làm mất bit thực thi (`stat.S_IXUSR`) trên thư mục ở Linux, gây lỗi `PermissionError` khi xóa file con. | **ĐÃ KHẮC PHỤC**: Triển khai `_make_writable(p)` bảo toàn các bit chế độ hiện có (`st.st_mode | stat.S_IWUSR`), giữ nguyên quyền thực thi/duyệt thư mục của POSIX đồng thời gỡ cờ Read-Only trên Windows. |
| `4051475199` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:146` | `safe_copy2()` tính `actual_dst_p` khi `dst` là thư mục nhưng vẫn truyền `dst` gốc vào `shutil.copyfile/copy2`, gây lỗi khi file đích thực tế là symlink hoặc junction. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa biến `target_dst = str(actual_dst_p) if isinstance(dst, str) else actual_dst_p` và truyền `target_dst` cho cả `shutil.copyfile` lẫn `shutil.copy2`. |
| `PRR_kwDOQzfV088AAAABOSEnRQ` | `packages/ccba-legal-intel/src/ccba_legal/sync/__init__.py:29` | `_is_link_or_junction` là private helper nhưng lại được export trong `__all__`. | **ĐÃ KHẮC PHỤC**: Loại bỏ `_is_link_or_junction` khỏi `__all__` tuân thủ RULE-1.3 (Thin Seams). |
| `PRR_kwDOQzfV088AAAABOSGGlA` | Toàn bộ PR #290 | Copilot Review tổng quan về rủi ro duyệt NTFS junctions và chmod symlinks. | **ĐÃ KHẮC PHỤC HOÀN TOÀN**: 100% đã được giải quyết qua `_safe_rmtree_tree`, `_make_writable`, và test coverage mở rộng. |
| `PRR_kwDOQzfV088AAAABOSJ8LA` | Toàn bộ PR #290 | Copilot Review tổng quan về `safe_copy2` destination path và `_safe_remove_leaf`. | **ĐÃ KHẮC PHỤC HOÀN TOÀN**: Đã xử lý với `target_dst` và `_make_writable`. |
| `4051492631` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:102` | Trên Python 3.10-3.11 Windows, `st_reparse_tag` có thể không khả dụng khiến `_is_link_or_junction` bỏ sót NTFS directory junctions. | **ĐÃ KHẮC PHỤC**: Khi phát hiện cờ `FILE_ATTRIBUTE_REPARSE_POINT`, nếu `st_reparse_tag` không tồn tại hoặc bằng 0 thì nhận diện ngay là junction/mount point. |
| `4051505389` | `packages/ccba-legal-intel/src/ccba_legal/sync/utils.py:172` | `_safe_remove_leaf()` chỉ bỏ qua chmod khi `p.is_symlink()`, nhưng junctions không phải symlink nên vẫn bị gọi `_make_writable` làm biến đổi quyền target. | **ĐÃ KHẮC PHỤC**: Đổi điều kiện kiểm tra thành `if not _is_link_or_junction(p):` ở cả 2 vị trí, đảm bảo tuyệt đối không chmod target của junction. |
| `PRR_kwDOQzfV088AAAABOSMPeQ` | Toàn bộ PR #290 | Copilot Review tổng quan về quyền file `registry.py` và junction permission mutation. | **ĐÃ KHẮC PHỤC HOÀN TOÀN**: Đã cập nhật `_is_link_or_junction`, `_safe_remove_leaf`, và `LegalRegistryManager.save` bảo toàn các bit mode hiện có. |

---

# Walkthrough: PR #289 — Linter Hiệu Lực Pháp Lý Đa Định Dạng & Vá Lỗi Tầng Nhân Khám Phá Registry

## 1. Tổng Quan PR #289
- **Branch:** `proposal/legal-currency-linter-and-registry-discovery` $\rightarrow$ `main`
- **Tiêu đề:** `feat(legal-intel): add legal currency linter and fix registry discovery`
- **PR liên quan:** [PR #289](https://github.com/vvChu/ccba-agent-platform/pull/289)
- **Issue liên quan:** [Issue #288](https://github.com/vvChu/ccba-agent-platform/issues/288)
- **Đề xuất RFC:** `.agents/proposals/2026-09-18_legal-currency-linter-and-registry-discovery.md`
- **Thể chế & Kiến trúc:** ADR-0029, ADR-0030, ADR-0045, ADR-0050, ADR-0057, ADR-0058, ADR-0059

---

## 2. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Vá lỗi Tầng Nhân Tra Cứu Registry (`registry.py` & `models.py`):**
   - Khắc phục thứ tự ưu tiên 6 tầng `discover_master_registry_path()` (ADR 0050), giải quyết lỗi fallback nhầm vào stub rỗng thay vì registry Spoke 928 dòng.
   - Thêm cơ chế lập chỉ mục đảo `_inverted_replacements` và từ điển ánh xạ chuyển tiếp chuẩn `KNOWN_STATUTORY_REPLACEMENTS`.
   - Chuẩn hóa trạng thái `LegalDocStatus.UNVERIFIED` cho văn bản chưa được đăng ký thay vì gán nhầm `ACTIVE`.
   - Chuẩn hóa đối chiếu tương đương giữa `NĐ-CP` (ASCII `ND-CP`) và các biến thể dấu hai chấm (`TCVN 2737:1995` vs `TCVN 2737-1995`).
2. **Linter Nhận Thức Ngữ Cảnh Đa Định Dạng (`linter.py`):**
   - Hỗ trợ bóc tách trên đa định dạng giao nộp: `.md`, `.markdown`, `.txt`, `.pptx` (đọc trực tiếp XML `ppt/slides/slide*.xml`), `.docx` (`word/document.xml`).
   - Miễn trừ ngữ cảnh chuyển tiếp/đối chiếu lịch sử (`is_transitional_context`: *thay thế, bãi bỏ, trước đây là, so sánh, superseding*).
   - Kiểm soát nghiêm ngặt 2 tầng: `ERROR` (exit code 1) cho văn bản bãi bỏ bị khẳng định; `WARNING` (exit code 0) cho văn bản chưa thẩm định.
   - Bảo mật OOXML: Tích hợp `defusedxml` chống tấn công DTD / Entity Expansion, chặn tệp giải nén vượt quá `MAX_XML_ENTRY_SIZE` (10MB).
3. **Mở rộng CLI (`cli.py`):**
   - Bổ sung cờ `--check-currency` (`-c`) và `--json` cho lệnh `ccba_legal lint`.
4. **Bộ kiểm thử toàn diện (`test_linter_currency.py`):**
   - 8 test cases bao phủ toàn diện mọi kịch bản khẳng định bãi bỏ, miễn trừ chuyển tiếp, trích xuất slide PPTX, biến thể ASCII và kích thước XML.

---

## 3. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #289)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `4047565884` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:446` | `lint_file_currency()` không bắt được số hiệu nghị định viết dạng ASCII `ND-CP` không dấu. | **ĐÃ KHẮC PHỤC**: Mở rộng biểu thức chính quy và hàm chuẩn hóa để xử lý tương đương cả 2 biến thể `NĐ-CP` và `ND-CP`. |
| `4047565934` | `packages/ccba-legal-intel/src/ccba_legal/linter.py` | Quét thư mục dùng `rglob('*')` tải toàn bộ cây thư mục vào bộ nhớ trước khi lọc. | **ĐÃ KHẮC PHỤC**: Chuyển sang `os.walk` với cơ chế loại bỏ top-down các thư mục bị bỏ qua (`.git`, `.venv`, `legal_docs`), tối ưu bộ nhớ và thời gian quét. |
| `4047565981` | `packages/ccba-legal-intel/tests/test_linter_currency.py:169` | Thiếu regression test cho dạng đầu vào `.../ND-CP` (ASCII). | **ĐÃ KHẮC PHỤC**: Bổ sung test case `test_statute_code_normalization` kiểm thử cả hai dạng `ND-CP` và `NĐ-CP`. |
| `4047785304` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:478` | Rào chặn trùng lặp cảnh báo dùng substring matching thay vì so sánh bằng trên ID chuẩn hóa. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa mã văn bản và so sánh bằng (`norm_gen == obs`) để tránh bỏ sót hoặc cảnh báo trùng. |
| `4047834831` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:609` | `lint_target_path()` chỉ nhận diện `.md` là Markdown mà bỏ sót đuôi mở rộng `.markdown`. | **ĐÃ KHẮC PHỤC**: Bổ sung hỗ trợ đuôi `.markdown` đồng bộ với `.md` trong cả linter định dạng và linter hiệu lực. |
| `4047834889` | `.md/knowledge/log.md:5` | Tệp nhật ký Append-Only bị mất khối mô tả blockquote ở đầu tệp. | **ĐÃ KHẮC PHỤC**: Khôi phục lại khối blockquote mô tả mục đích sử dụng tệp. |
| `4047878708` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:302` | `safe_parse_xml()` fallback sử dụng `xml.etree.ElementTree` có nguy cơ bị tấn công DTD / Entity Expansion. | **ĐÃ KHẮC PHỤC**: Bổ sung `defusedxml` vào dependencies và chủ động kiểm tra từ chối payload XML chứa `<!DOCTYPE` hoặc `<!ENTITY` trong fallback stdlib. |
| `4047927534` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:303` | Rà soát an toàn phân tích cú pháp XML đối với các payload untrusted OOXML. | **ĐÃ KHẮC PHỤC**: Chặn đứng việc parse nếu phát hiện khai báo thực thể nguy hiểm khi không có `defusedxml`. |
| `4047985753` | `.agents/proposals/2026-09-18_legal-currency-linter-and-registry-discovery.md` | Tệp proposal ghi "zero external dependency" nhưng thực tế có bổ sung dependency nhẹ `defusedxml`. | **ĐÃ KHẮC PHỤC**: Cập nhật tài liệu RFC proposal làm rõ việc sử dụng dependency nhẹ `defusedxml` để tăng cường bảo mật. |
| `4051397478` | `packages/ccba-legal-intel/src/ccba_legal/registry.py:577` | `get_lifecycle()` và `find_doc()` không nhận diện `217/2026/ND-CP` và `217/2026/NĐ-CP` là một. | **ĐÃ KHẮC PHỤC**: Tự động tra cứu thử biến thể đối ứng (`NĐ-CP` $\leftrightarrow$ `ND-CP`) trong `find_doc()` và `get_lifecycle()`. |
| `4051457124` | `.md/knowledge/session_learnings.md` | Tài liệu chứa giá trị token mẫu có thể gây cảnh báo secret scanner. | **ĐÃ KHẮC PHỤC**: Thay thế bằng placeholder biến môi trường `${SPARK_API_KEY}` theo đúng quy tắc RULE-4.5. |
| `PRR_kwDOQzfV088AAAABOSIylg` | Toàn bộ PR #289 | Tổng quan đánh giá của Copilot về chuẩn hóa `find_doc()` và bảo mật tài liệu. | **ĐÃ KHẮC PHỤC HOÀN TOÀN**: Đã xử lý toàn diện qua các commit bổ sung. |
| `PRR_kwDOQzfV088AAAABOSLTeA` | `packages/ccba-legal-intel/src/ccba_legal/linter.py:371` | Sắp xếp slide PPTX gọi `re.search()` 2 lần mỗi phần tử và danh sách `docx` chưa định kiểu strict mypy. | **ĐÃ KHẮC PHỤC**: Dùng assignment expression `m := re.search(r"\d+", x)` để cache kết quả và gán `results: list[tuple[int, str, str]] = []`. |

---

# Walkthrough: PR #295 — Tích Hợp Pha 1 Legal Ground Truth Parity & Telemetry Vào Nightly Tuner

## 1. Tổng Quan PR #295
- **Branch:** `proposal/nightly-legal-parity-tuner-integration` $\rightarrow$ `main`
- **Tiêu đề:** `feat(cron): integrate Phase 1 legal ground truth parity and telemetry into nightly tuner`
- **PR liên quan:** [PR #295](https://github.com/vvChu/ccba-agent-platform/pull/295)
- **Đề xuất RFC:** `.agents/proposals/2026-09-19_nightly-legal-parity-tuner-integration.md`
- **Commit hợp nhất:** `5cdc0d787be4db8cac11c21d0874b4c4b4490c5d` (Squash Merge)
- **Thể chế & Kiến trúc:** ADR-0037, ADR-0041, ADR-0042, ADR-0045, ADR-0047, ADR-0057, ADR-0058

---

## 2. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Tích hợp Pha 1 Telemetry vào Cỗ máy Ban đêm (`run_nightly_tuner.sh` & `.bat`):**
   - Bổ sung khối kiểm định Pha 1: Chạy `run_nightly_telemetry.py --cohorts golden` trước Pha 2 (Document Auto-Evolution) và Pha 3 (Nightly Auto-Tuner).
   - Tự động hóa commit và push báo cáo telemetry ban đêm (`nightly_*.md`, `nightly_*.json`) với danh tính daemon `CCBA Nightly Daemon` và cờ `--no-verify` tránh CI loops.
   - Gửi cảnh báo Telegram tức thì khi phát hiện lỗi hồi quy kiểm chuẩn pháp lý / Master CI.
   - Cơ chế fallback linh hoạt và hỗ trợ đầy đủ cờ `--dry-run`.
2. **Cập nhật Bất biến Kỹ năng Ingestion & Processing:**
   - `.agents/skills/ccba-legal-ingest/SKILL.md`: Bổ sung Kịch bản 5 về Session Takeover TVPL Pro, định tuyến Tab Tiêu chuẩn TCVN và mô hình Safe Landing Download.
   - `.agents/skills/ccba-markdown-document-processing/SKILL.md`: Bổ sung Mục 4 về kiểm chuẩn Verbatim Ground Truth ($\ge 98.0\%$ greedy coverage) và Anti-Vacuous Table Regularity (zero ragged rows, tách rời chú thích chân bảng).
3. **Quản trị Đề xuất & Hệ sinh thái:**
   - `.agents/proposals/2026-09-19_nightly-legal-parity-tuner-integration.md`: RFC proposal chính thức ghi nhận đầy đủ ma trận Giá trị × Rủi ro × KISS.
   - `docs/adr/TRACEABILITY_MATRIX.md`: Bổ sung ánh xạ ADR-0037 và ADR-0041 cho kỹ năng markdown document processing.
   - `.md/data/spoke_registry.yaml`: Cập nhật mã định danh spoke bảo mật.

---

## 3. Kết Quả Kiểm Định Tự Động (Deterministic Hard Completion Verification)

- **Worker 1 (Spoke Leakage & Privacy Guard):** ✅ **PASSED** (7 files, 0 critical violations, 0 warnings).
- **Worker 2 (Deep Seams & Skills Governance):**
  - `python scripts/validate_skills.py --enforce-gpi`: ✅ **PASSED** (73/73 skills validated, 0 errors).
  - `bash -n scripts/cron/run_nightly_tuner.sh`: ✅ **PASSED** (Cú pháp hợp lệ).
  - `python -m ccba_harness verify-patch --preset skill`: ✅ **ALL 2/2 COMMANDS PASSED** (`validate_skills` + `compile_catalog`).
- **Worker 3 (Proposal Lifecycle & Catalog Governance):**
  - Metadata frontmatter hợp chuẩn, catalog tái biên dịch thành công 73 skills.
- **GitHub Actions CI (6/6 checks):**
  - `Lint Markdown`: SUCCESS
  - `Test - Python 3.10`: SUCCESS
  - `Test - Python 3.11`: SUCCESS
  - `Test - Python 3.12`: SUCCESS
  - `scan`: SUCCESS
  - `validate`: SUCCESS

---

## 4. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot & Maintainer

| ID / Review | Tệp Tin | Vấn Đề / Yêu Cầu | Trạng Thái & Giải Pháp |
|---|---|---|---|
| Review PR #295 | Toàn bộ PR #295 | Rà soát tự động GitHub Copilot | **HOÀN TOÀN SẠCH**: 0 pending review requests, 0 comments. |
| Maintainer Gate | Toàn bộ PR #295 | Phê duyệt hợp nhất và kích hoạt Bước 5 Post-Merge Governance | **ĐÃ PHÊ DUYỆT**: Squash merge thành công vào `main` tại commit `5cdc0d78`. |

---

# Walkthrough: PR #297 — Word COM Single-Pass Form Filler Module & Form Layout Guard

## 1. Tổng Quan PR #297
- **Branch:** `feat/ooxml-form-filler-guard` $\rightarrow$ `main`
- **Tiêu đề:** `feat(ooxml): add Word COM single-pass form filler module with layout guard`
- **PR liên quan:** [PR #297](https://github.com/vvChu/ccba-agent-platform/pull/297)
- **Issue liên quan:** Closes [#296](https://github.com/vvChu/ccba-agent-platform/issues/296)
- **Commit hợp nhất:** `3f2972aa` (Squash and merge)
- **Thể chế & Kiến trúc:** ADR-0058 (Hard Completion Lock), ADR-0057 (Two-Stage Governance), KISS & Architecture Parity

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #297)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| Review PR #297 | Toàn bộ PR #297 | Rà soát tự động GitHub Copilot | **HOÀN TOÀN SẠCH**: 0 pending review requests, 0 comments. |
| Audit Script | `audit_pr_comments.py` | Kiểm tra tự động các thay đổi và comments | **[OK]**: All Copilot reviews and comments on PR #297 are clean or resolved. |
| Maintainer Gate | PR #297 | Phê duyệt hợp nhất và kích hoạt quy trình release | **ĐÃ PHÊ DUYỆT & MERGE**: Squash merge thành công vào `main` tại commit `3f2972aa`. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Sub-module Form Filler Mới ([`ccba_ooxml.form_filler`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-ooxml/src/ccba_ooxml/form_filler/)):**
   - **Unified Facade (`WordFormFiller`):** Giao diện thống nhất hỗ trợ auto-detect hệ điều hành (`engine="auto"`), context manager tự thu hồi tiến trình Word an toàn (`with WordFormFiller(...) as filler:`), và fluent chaining API.
   - **Engine A (`WinwordEngine` — Windows Native):**
     - Thao tác trực tiếp trên Word DOM qua COM (`win32com.client`).
     - Điền trực tiếp trên file `.doc` (Word 97-2003 nhị phân) và `.docx` gốc (In-Place Single-Pass) theo `Paragraph.Range` và `Table.Cell`, không qua chuyển đổi trung gian.
     - Tự động đóng tài liệu và tắt tiến trình Word an toàn trong khối `finally`, triệt tiêu nguy cơ rò rỉ tiến trình `WINWORD.EXE`.
   - **Engine B (`SofficeFallbackEngine` — Cross-Platform Linux/Docker):**
     - Sử dụng LibreOffice (`soffice` headless runner trong `ccba_ooxml.soffice`) kết hợp `python-docx` khi chạy trên Linux, container Docker hoặc máy chủ không có Microsoft Word.
     - Thao tác trực tiếp trên cây XML OpenXML (`w:cantSplit`).

2. **Form Layout Guard (`FormLayoutGuard`):**
   - **Anti-Row Split:** Cưỡng chế `Row.AllowBreakAcrossPages = False` (COM) hoặc chèn thẻ `<w:cantSplit/>` (DOCX XML) để bảo vệ toàn vẹn bảng biểu, ngăn hàng bị xé đôi giữa 2 trang in.
   - **Empty Row Pruning:** Tự động cắt tỉa các dòng mẫu trống thừa trong bảng biểu danh sách động.
   - **Page Break Enforcement:** Tự động chèn ngắt trang (`PageBreakBefore`) cho các phần kết luận/chữ ký theo từ khóa nhận diện.

3. **Tài Liệu & Quản Trị Hệ Thống:**
   - Sổ tay kỹ thuật: [`.agents/skills/ccba-xu-ly-van-phong/resources/form-filling.md`](file:///home/vvc/ccba/ccba-agent-platform/.agents/skills/ccba-xu-ly-van-phong/resources/form-filling.md).
   - Đăng ký triggers trong `platform-loader/catalog.yaml` và `ccba-xu-ly-van-phong/SKILL.md` (`điền form word`, `fill form doc`, `form-filler`, `layout guard`).
   - Cập nhật tài liệu kiến trúc `README.md` loại bỏ Architecture Drift.
   - Biên dịch web docs tự động (`docs/`).

4. **Kiểm Thử Tự Động & CI:**
   - Unit tests: [`test_form_filler.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-ooxml/tests/test_form_filler.py) (7/7 tests passed).
   - Package tests: `packages/ccba-ooxml/tests/` (67/67 tests passed).
   - Monorepo isolated tests: 11/11 package suites passed.
   - GitHub Actions CI: 6/6 jobs passed (Markdown lint, Python 3.10, 3.11, 3.12, Security scan, Documentation check).





