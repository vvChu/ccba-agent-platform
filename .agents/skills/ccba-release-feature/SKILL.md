---
name: ccba-release-feature

description: Merge PR, cleanup branch, auto-close local issues và cập nhật walkthrough
applies_to:
- Phần mềm
bundle: _core
scope: universal
posture: seam-exempt
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-release-feature
metadata:
  version: "1.3.9"
  author: "CCBA Hub"
triggers:
- release
- merge PR
- phát hành
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge), kiểm tra Copilot Review, tự động đóng issue và dọn dẹp môi trường.

---

## Bước 0: Kiểm soát Buồng kín & Kiểm thử Toàn diện (Hermetic Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải tuân thủ Giao thức TRIHT (Tiered Release Integrity & Hermetic Teardown)** gồm 3 giai đoạn để ngăn chặn hoàn toàn nguy cơ mất mã nguồn và chống gián đoạn chuyển nhánh:

1. **Cổng 0.1 — Khóa Sạch Sẽ Tiền Kiểm Tra (Pre-Flight Cleanliness Lock):**
   - *Bắt buộc kiểm tra:* Repository phải ở trạng thái sạch sẽ 100% (không có tệp modified hoặc untracked chưa commit). Tuyệt đối cấm release khi mã nguồn cục bộ chưa được commit vào PR (tại Spoke định tuyến qua `CCBA_HUB_PATH`):
     ```bash
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/check_release_cleanliness.py" --phase pre --repo-root .
     ```
   - Nếu phát hiện tệp chưa commit thuộc tác vụ song song khác:
     1. Thực hiện stash có định danh rõ ràng kèm cả tệp untracked:
        ```bash
        git stash push -u -m "wip: concurrent work before release PR #[PR_NUMBER]"
        ```
     2. Xác nhận lại nhánh hiện tại trước khi kích hoạt Cổng 0.2:
        ```bash
        git branch --show-current
        ```
   - *Rào chắn Cô lập `git worktree` (`RULE-4.21`):* Khi thư mục gốc đứng ở nhánh khác `<default_branch>` (`main`/`master`) hoặc `<default_branch>` có `ahead > 0`, cấm `git checkout`/`git pull` trên thư mục gốc; dùng `git worktree` cô lập từ `origin/<default_branch>`, chạy Cổng 0.1–0.3 & Bước 1–3, tháo worktree (`git worktree remove <path> && git worktree prune`) trước khi merge PR, và cập nhật `git fetch --prune origin <default_branch>:<default_branch>`.

2. **Cổng 0.2 — Thực thi Kiểm thử Toàn diện Slow Integration Tests:**
   - **Hub:** `python scripts/eval/run_isolated_tests.py --all --stress` (nếu chạy trong isolated `git worktree`, trỏ tới `.venv` của repo gốc qua `git rev-parse --path-format=absolute --git-common-dir`: `<main-repo>/.venv/bin/python scripts/eval/run_isolated_tests.py --all --stress`).
   - **Legal / Knowledge Corpus Spokes:** `python scripts/validate_legal_spoke.py`.
   - **Software / Enterprise Governance Spokes** *(không giả định `scripts/validate_legal_spoke.py` hay `scripts/eval/*` tồn tại cục bộ)*: chạy harness đặc thù `python .agents/skills/verify-<spoke>/harness/runner.py` (nếu có), hoặc scoped `python -m pytest tests/ -q` (nếu có bộ test) kèm `python scripts/_guardrails/check_spoke_cleanliness.py`. Dừng ngay nếu bất kỳ cổng nào fail.

3. **Cổng 0.3 — Post-Test Scoped Teardown Gate:**
   ```bash
   python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/check_release_cleanliness.py" --phase post --repo-root .
   ```
   Dừng khẩn cấp nếu exit code 1.

**Tiêu chí hoàn thành:** Cổng 0.1 sạch 100%, 100% bài kiểm thử Cổng 0.2 pass (xác minh chạy bằng Python của `.venv` repo gốc khi ở trong `git worktree`), và Cổng 0.3 dọn dẹp buồng kín thành công.

---

## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. **Lấy thông tin PR & Merge Danger Triage (`ADR-0067`):**
   ```bash
   git branch --show-current && gh pr view --json number,title,state,headRefName,body
   ```
   Nếu `One-way door`, bán kính `Monorepo-wide / Spoke-affecting`, hoặc `> 200 LOC`: bắt buộc có `### Tradeoff Card (ADR-0067)` (`<= 30` dòng, neo `#L<a>-L<b>`) và chạy:
   ```bash
   python -m ccba_harness door-triage <changed_files> --pr-body-file <body_file> --enforce-tradeoff-card
   ```
2. **Xác thực GitHub CLI & Kiểm tra CI (`gh auth status` & `gh pr checks`):**
   - *Zero-Polling Policy:* Nếu pending -> chạy `gh pr checks --watch` rồi dừng gọi tool (Reactive Wakeup); cấm poll lặp `manage_task status`.
   - *Cổng Dự phòng Quota-Lock Fail-Closed:* Chỉ mô phỏng CI tại `/tmp` khi thỏa đủ 4 cổng (mọi job fail `steps == []` + failure annotation khóa thanh toán, kiểm toán REST/GraphQL non-truncated không bật `required_status_checks`, User phê duyệt, clone `/tmp` redact bí mật) — xem chi tiết tại `references/release_scripts_and_recovery.md`.
3. **Chốt chặn Copilot Review (`reviewRequests`/`reviews`) & Hard Blocker (`audit_pr_comments.py`):**
   ```bash
   gh pr view --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.author.login]}'
   python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/audit_pr_comments.py"
   ```
   Chờ Copilot submit xong mới audit; nếu exit code 1 hoặc có góp ý VALID chưa xử lý -> sửa/giải trình trực tiếp vào `.md/knowledge/reports/walkthrough.md` kèm `review_id` (`RULE-4.10`, cấm `.md/walkthrough.md`).
4. **Chiến lược Merge (`RULE-2.21` bắt buộc `--merge` cho `verify-ccba-*`):**
   ```bash
   git diff --name-only origin/<default_branch>..HEAD -- 'packages/ccba-harness/.agents/skills/verify-ccba-*/SKILL.md'
   ```
   - Có chạm `verify-ccba-*/SKILL.md` (`sync_commit` / `covered_sha256`): **BẮT BUỘC `gh pr merge [PR_NUMBER] --merge --delete-branch`**, cấm `--squash`; sau pull kiểm tra `git cat-file -e <sync_commit>^{commit}` mã `0`.
   - Mặc định còn lại: `gh pr merge --squash --delete-branch` (kiểm tra `gh api repos/{owner}/{repo} --jq .allow_auto_merge` nếu dùng `--auto`; dùng `--watch` + End Turn nếu `false`). Nếu `gh pr merge` gặp lỗi GraphQL `projectCards`, dùng REST fallback `gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/merge -X PUT -f merge_method=squash -f sha=<head_sha>` và bỏ `git push origin --delete` nếu repo bật `delete_branch_on_merge: true`.

**Tiêu chí hoàn thành:** CI 100% xanh (hoặc Quota-Lock thỏa đủ 4 cổng fail-closed + biên lai redacted), Copilot review giải quyết xong và PR đã merge thành công.

---

## Bước 2: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy commit PR: `git log origin/<default_branch>..HEAD --oneline`.
2. Cập nhật tóm tắt thay đổi & kết quả nghiệm thu vào `walkthrough.md`.

**Tiêu chí hoàn thành:** Tệp walkthrough.md được cập nhật đầy đủ tóm tắt thay đổi.

---

## Bước 3: Sync Local Codebase, Auto-Close Local Issue & Dọn dẹp

1. **Kiểm tra working tree & thu hồi `pytest` mồ côi, đồng bộ `<default_branch>` (`RULE-4.21`):**
   ```bash
   git status --porcelain
   # Tại Hub:
   python -c "from scripts.eval.process_safety import ensure_single_instance; ensure_single_instance('pytest')"
   # Tại Spoke (điều hướng qua $CCBA_HUB_PATH nếu có; không giả định scripts/eval/* tồn tại cục bộ):
   python -c "import os, pathlib, sys; hub = pathlib.Path(os.environ.get('CCBA_HUB_PATH', '../ccba-agent-platform')).resolve(); (hub / 'scripts/eval/process_safety.py').is_file() and (sys.path.extend([str(hub), str(hub / 'packages/ccba-harness/src')]) or __import__('scripts.eval.process_safety', fromlist=['ensure_single_instance']).ensure_single_instance('pytest'))"
   # Nếu <default_branch> sạch (ahead == 0): git --no-pager checkout <default_branch> && git pull origin <default_branch>
   # Nếu đứng ở nhánh khác / ahead > 0: git fetch --prune origin <default_branch>:<default_branch>
   git branch -D [feature_branch_name] && git fetch --prune
   ```
2. **Dọn nhánh remote đã merge 100% & Sync Spoke (nếu tại Hub):** Xác minh `git log origin/<default_branch>..origin/<branch>` rỗng trước khi `git push origin --delete`; chạy `python scripts/sync_spoke.py --spoke [spoke_path] --sync-item ccba-release-feature --apply`.
3. **Đóng Issue cục bộ & Tái biên dịch Catalog:** Đặt `status: closed` tại `.md/knowledge/issues/issue-XXX.md`, cập nhật `.agents/proposals/` nếu có (`status: "merged"`, `merged_pr`, `merged_commit`, `merged_date`), và chạy `python scripts/governance/compile_catalog.py` (nếu tại Hub).
4. **PR lưu trữ Walkthrough & Khôi phục Stash:** Kiểm tra từng đường dẫn theo logic OR (`git ls-files --error-unmatch`); nếu `is_hub=True` hoặc có file được track -> mở PR `docs/walkthrough-pr-[PR_NUMBER]` kèm `door-triage --enforce-tradeoff-card` và `validate_docs.py`; ngược lại giữ Artifact tại `<appDataDir>/brain/...`. Khôi phục `git stash pop stash@{N}` (nếu conflict dùng `git reset --merge && git clean -df`) — xem script đầy đủ tại `references/release_scripts_and_recovery.md`.

**Tiêu chí hoàn thành:** Nhánh `<default_branch>` cục bộ đồng bộ, nhánh feature xóa, issue cục bộ closed, `validate_docs.py` & `door-triage` PASS (nếu tạo PR walkthrough) và stash song song được khôi phục an toàn.

---

## Bước 4: Thông báo hoàn tất

Báo cáo rõ ràng 4 trạng thái: Feature đã merge vào `<default_branch>`, branch local/remote đã dọn, issue đã đóng và `walkthrough.md` đã lưu trữ hoàn tất.

**Tiêu chí hoàn thành:** Toàn bộ trạng thái tích hợp, dọn dẹp và đóng issue được thông báo hoàn tất.

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/release_scripts_and_recovery.md` | Chi tiết 4 cổng Quota-Lock CI Simulation, dọn nhánh remote đã merge, script PR `walkthrough.md` (`door-triage`) và khôi phục stash chống conflict |
