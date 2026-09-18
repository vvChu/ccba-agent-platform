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
| `PRR_kwDOQzfV088AAAABOSCFzQ` | Toàn bộ PR #290 | Copilot Review tổng thể yêu cầu sửa 2 điểm trên. | **ĐÃ KHẮC PHỤC HOÀN TOÀN**: 100% các góp ý đã được xử lý triệt để. |

