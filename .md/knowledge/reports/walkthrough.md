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

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Nâng cấp Kernel Skill ([`ccba-create-pr`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-create-pr/SKILL.md)):**
   - Bump version từ `1.1.0` $\rightarrow$ `1.2.0`.
   - Bổ sung lệnh `git symbolic-ref --short refs/remotes/origin/HEAD` tại Bước 0 để xác định nhánh mặc định (`<default_branch>`).
   - Loại bỏ giả định ngầm hardcode `main`, tương thích hoàn hảo với cả `master` và các Spoke đa dạng.
   - Sử dụng placeholder `<default_branch>` xuyên suốt từ Bước 0 đến Bước 3 (`gh pr create --base <default_branch>`).
2. **RFC Proposal Chuẩn Hóa ([`2026-09-17_dynamic-base-branch-for-create-pr.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/proposals/2026-09-17_dynamic-base-branch-for-create-pr.md)):**
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

