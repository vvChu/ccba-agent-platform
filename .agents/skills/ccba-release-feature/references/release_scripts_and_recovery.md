# Release Feature — Quota-Lock CI Simulation, Walkthrough PR & Recovery Scripts

Tài liệu tham chiếu Level 3 cho `ccba-release-feature`, chứa chi tiết Cổng Dự phòng Quota-Lock 4 bước, quy trình xóa nhánh mồ côi remote, script tạo PR lưu trữ `walkthrough.md` và cơ chế khôi phục stash chống xung đột.

## 1. Cổng Dự Phòng Quota-Lock Fail-Closed (4 Cổng Bắt Buộc)

Chỉ được phép chuyển sang mô phỏng CI cục bộ trên bản sao sạch khi thỏa **đồng thời cả 4 cổng** (bất kỳ điều kiện nào sai hoặc không đọc được -> **DỪNG NGAY**):

1. **Cổng 1 — Chứng thực Quota-Lock qua API Trực tiếp (`statusCheckRollup` + `jobs` + `annotations`):**
   - Toàn bộ check fail trên PR phải là `CheckRun` có kết luận `FAILURE` (nếu có `StatusContext` hoặc job fail biên dịch, test hoặc lint -> **DỪNG**).
   - Trích xuất `<run_id>` và `<job_id>` từ `detailsUrl` (`actions/runs/<run_id>/job/<job_id>`, hoặc dự phòng `GET /repos/{owner}/{repo}/commits/<head_sha>/check-runs`), gọi `GET /repos/{owner}/{repo}/actions/runs/<run_id>/jobs` và `GET /repos/{owner}/{repo}/check-runs/<job_id>/annotations`.
   - Khẳng định mọi job fail đều có `steps == []` (`0` bước được chạy) và annotation mức `failure` chứa thông điệp khóa thanh toán/hạn mức (`account payments have failed` hoặc `spending limit needs to be increased`).
2. **Cổng 2 — Kiểm toán Ruleset & Branch Protection (Fail-Closed, Non-Truncated):**
   - Gọi REST trên `<default_branch>`: `GET /repos/{owner}/{repo}/branches/<default_branch>/protection`, `GET /repos/{owner}/{repo}/rulesets`, và `GET /repos/{owner}/{repo}/rules/branches/<default_branch>`. Nếu `HTTP 200`, xác nhận KHÔNG có `required_status_checks` đang `active`.
   - Nếu `HTTP 403`, truy vấn GraphQL (`gh api graphql`): `repository.rulesets(first: 20, includeParents: true)` (kèm `rules(first: 20)`) và `repository.branchProtectionRules(first: 20)`. Bắt buộc `HTTP 200`, không `errors`, không null, mọi `pageInfo.hasNextPage == false`, và không có `REQUIRED_STATUS_CHECKS` / `requiresStatusChecks`.
3. **Cổng 3 — Phê duyệt Tường minh của Người dùng** trước hoặc tại thời điểm xử lý PR.
4. **Cổng 4 — Mô phỏng CI trên Bản sao Sạch (`/tmp`):**
   - Clone nhánh PR ra `/tmp/ci-clean-...` và chạy `env -u CCBA_HUB_PATH -u HUB_PATH` trên container đúng kiến trúc gốc (`uname -m`) thuộc họ image trong workflow; job thiếu secret ghi `SKIPPED_NO_SECRETS`.
   - Khử toàn bộ token/password/certificate trước khi đăng lên PR qua `gh pr comment <PR> -F <tmp_report>` và xóa sạch `/tmp/ci-clean-*`.

## 2. Dọn Dẹp Nhánh Mồ Côi Remote Đã Merge (Bước 3.3b)

```bash
git fetch --prune
git ls-remote --heads origin "*[feature_keyword]*"
# CHỈ xóa nếu git log origin/main..origin/[orphan_branch_name] --oneline trả về rỗng:
git log origin/main..origin/[orphan_branch_name] --oneline
git push origin --delete [orphan_branch_name]
```

## 3. Quy Trình Tạo PR Lưu Trữ `walkthrough.md` (Bước 3.5)

Hook `pre-push` cấm push thẳng lên `main`. Chỉ stage các đường dẫn được git track trên repo hiện tại (Hub hoặc Spoke):

```bash
python -c '
import pathlib, subprocess
remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True)
is_hub = "ccba-agent-platform" in remote.lower()
candidates = ["walkthrough.md", ".md/knowledge/reports/walkthrough.md", ".agents/proposals"]
tracked = [
    p for p in candidates
    if pathlib.Path(p).exists()
    and subprocess.run(["git", "ls-files", "--error-unmatch", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
]
print(f"is_hub={is_hub} tracked={tracked}")
'
```

Khi `is_hub=True` hoặc `len(tracked) > 0`:
- Nếu `main` sạch (`ahead == 0`): tạo nhánh `docs/walkthrough-pr-[PR_NUMBER]` từ `main`. Nếu thư mục gốc bận phiên song song (`RULE-4.21`): `git fetch --prune origin main:main && git worktree add -b docs/walkthrough-pr-[PR_NUMBER] <walkthrough_wt> origin/main`.
- Lưu ý: `.md/knowledge/reports/walkthrough.md` dẫn về gốc bằng `../../../` (`RULE-2.4`) và không chứa `file:///` (`RULE-3.5`). Nếu có PR đồng đẳng cập nhật cùng file -> rebase lên `origin/main` giữ nguyên mục PR đồng đẳng ở đầu, rồi đẩy bằng `git push --force-with-lease`.
- Kiểm định & mở PR:

```bash
git add -- <tracked_paths>
git commit -m "docs(walkthrough): record release feature PR #[PR_NUMBER] completion and review matrix"
git push -u origin docs/walkthrough-pr-[PR_NUMBER]
python -m ccba_harness door-triage <tracked_paths> --pr-body-file /tmp/pr_walkthrough_body.md --enforce-tradeoff-card
gh pr create --head docs/walkthrough-pr-[PR_NUMBER] --base main --assignee "@me" --title "docs(walkthrough): record release feature PR #[PR_NUMBER] completion" -F /tmp/pr_walkthrough_body.md
gh pr checks --watch
```

Nếu dùng worktree cô lập, tách HEAD (`git -C <walkthrough_wt> checkout --detach && git worktree remove <walkthrough_wt> && git worktree prune`) rồi mới chạy `gh pr merge [WALKTHROUGH_PR_NUMBER] --squash && git push origin --delete docs/walkthrough-pr-[PR_NUMBER]`.

## 4. Khôi Phục Tác Vụ Song Song Đã Stash (Bước 3.6)

```bash
git stash list --grep="wip: concurrent work before release PR #[PR_NUMBER]"
git stash pop stash@{N}
# Nếu xung đột merge khi pop lên main, lập tức làm sạch working tree và giữ bản stash:
git reset --merge && git clean -df
```
