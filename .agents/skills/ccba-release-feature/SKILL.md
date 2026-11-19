---
name: ccba-release-feature

description: Merge PR, cleanup branch, auto-close local issues và cập nhật walkthrough
applies_to:
- Phần mềm
bundle: _core
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-release-feature
metadata:
  version: "1.3.7"
  author: "CCBA Hub"
triggers:
- release
- merge PR
- phát hành
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge), kiểm tra Copilot Review, tự động đóng issue và dọn dẹp môi trường.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (SOP orchestrator cho TRIHT, squash merge và đóng issue tự động). Lệnh `scripts/sync_spoke.py --spoke` giữ đúng mặt wrapper đã khóa ở Đợt 5; không đóng gói pipeline chuyển đổi dữ liệu độc lập hay phụ thuộc Seam Contract ứng dụng cụ thể. Giữ nguyên `tier: orchestrator`.

---

## Bước 0: Kiểm soát Buồng kín & Kiểm thử Toàn diện (Hermetic Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải tuân thủ Giao thức TRIHT (Tiered Release Integrity & Hermetic Teardown)** gồm 3 giai đoạn để ngăn chặn hoàn toàn nguy cơ mất mã nguồn và chống gián đoạn chuyển nhánh:

1. **Cổng 0.1 — Khóa Sạch Sẽ Tiền Kiểm Tra (Pre-Flight Cleanliness Lock):**
   - *Bắt buộc kiểm tra:* Repository phải ở trạng thái sạch sẽ 100% (không có tệp modified hoặc untracked chưa commit). Tuyệt đối cấm release khi mã nguồn cục bộ chưa được commit vào PR (tại Spoke định tuyến qua `CCBA_HUB_PATH`):
     ```bash
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/check_release_cleanliness.py" --phase pre
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
   - *Rào chắn Cô lập `git worktree` khi thư mục gốc đang ở nhánh khác hoặc `main` có phiên song song (`RULE-4.21`):* Bất cứ khi nào thư mục làm việc gốc đang đứng trên nhánh đồng đẳng khác `main` (`git branch --show-current != main`) **HOẶC** nhánh `main` cục bộ có commit chưa đẩy (`ahead > 0`), nghiêm cấm chạy `git checkout` hoặc `git pull` trực tiếp trên thư mục gốc. Agent bắt buộc khởi tạo một `git worktree` cô lập tách từ `origin/main` (hoặc nhánh PR cần phát hành) để chạy trọn vẹn Cổng 0.1–0.3, Bước 1–3 và gỡ bỏ worktree tạm (`git worktree remove <path> && git worktree prune`) **trước** khi gọi `gh pr merge --squash --delete-branch` (hoặc tách HEAD `git -C <worktree_path> checkout --detach` rồi chạy `gh pr merge --squash && git push origin --delete [feature_branch_name]`), sau đó đồng bộ `refs/heads/main` không chạm working tree bằng `git fetch --prune origin main:main`.

2. **Cổng 0.2 — Thực thi Kiểm thử Toàn diện Slow Integration Tests:**
   - **Tại Hub Platform (`ccba-agent-platform`):**
     ```bash
     python scripts/eval/run_isolated_tests.py --all --stress
     ```
   - **Tại Spoke (Pháp điển / Knowledge Corpus / Specialized Spokes):**
     ```bash
     # Nếu spoke có script kiểm định chuyên sâu:
     python scripts/validate_legal_spoke.py
     # hoặc chạy toàn bộ test cô lập cục bộ:
     python scripts/eval/run_isolated_tests.py --all
     ```
   - Nếu có bài test nào thất bại, Agent **phải dừng quy trình release ngay lập tức** để sửa lỗi.

3. **Cổng 0.3 — Hàng rào Thu hồi Tệp tạm Sau Kiểm thử (Post-Test Scoped Teardown Gate):**
   - *Bắt buộc kiểm tra:* Sau khi bài test chạy xong, đối soát delta trạng thái working tree. Tự động thu hồi an toàn các cache kiểm thử đã biết (`embeddings.npy`, `ci_log.txt`, `tmp_*.json`) và chặn đứng nếu có test suite sửa đổi mã nguồn:
     ```bash
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/check_release_cleanliness.py" --phase post
     ```
   - Nếu lệnh trả về exit code 1 (phát hiện mã nguồn bị sửa đổi hoặc tệp lạ), Agent **dừng khẩn cấp** để điều tra bài test vi phạm.

---

**Tiêu chí hoàn thành:** Cổng 0.1 sạch 100%, 100% bài kiểm thử Cổng 0.2 pass, và Cổng 0.3 dọn dẹp buồng kín thành công.

---

## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. **Lấy thông tin PR và Branch hiện hành (Platform-Agnostic):**
   ```bash
   git branch --show-current
   gh pr view --json number,title,state,headRefName,body
   ```

   - **Sàng lọc Mức độ Nguy hiểm & Thẻ Đánh Đổi (Merge Danger Triage & Tradeoff Card — ADR-0067):**
     * Đọc trường `## Merge Danger Assessment` (hoặc `## Merge Danger`) từ mô tả PR:
       - Nếu **Two-way door** và bán kính **Localized**: Áp dụng *Fast-path review* (kiểm tra nhanh CI và Copilot comments để merge).
       - Nếu **One-way door**, bán kính **Monorepo-wide / Spoke-affecting**, hoặc diff vượt ngưỡng 200 LOC: Bắt buộc tiến hành *Deep review* và xác minh PR body đã có khối `### Tradeoff Card (ADR-0067)` hợp lệ (`<= 30` dòng, có neo dòng `#L<a>-L<b>`) trước khi chạy CI/merge:
         ```bash
         python -m ccba_harness door-triage <changed_files> --pr-body-file <body_file> --enforce-tradeoff-card
         ```

2. **Kiểm tra xác thực GitHub CLI (`gh`):**
   ```bash
   gh auth status
   ```

3. **Kiểm tra trạng thái GitHub Actions CI (và Cổng Dự phòng Quota-Lock Fail-Closed):**
   ```bash
   gh pr checks
   ```
   - *Rào chắn Zero-Polling CI:* 
     - Nếu các checks đang ở trạng thái `pending`, Agent có thể khởi chạy `gh pr checks --watch` rồi **lập tức dừng gọi công cụ (End Turn)** để hệ thống đánh thức qua cơ chế *Reactive Wakeup* khi CI xanh.
     - **Tuyệt đối nghiêm cấm** chạy vòng lặp gọi `manage_task status` liên tiếp nhiều lần để thăm dò task `--watch`.
   - *Cổng Dự phòng Quota-Lock Fail-Closed (4 Cổng Bắt buộc — Cấm suy đoán hoặc lách luật):*
     Chỉ được phép chuyển sang mô phỏng CI cục bộ trên bản sao sạch khi thỏa **đồng thời cả 4 cổng** sau (bất kỳ điều kiện nào sai hoặc không đọc được $\to$ **DỪNG NGAY**):
     1. **Cổng 1 — Chứng thực Quota-Lock qua API Trực tiếp (`statusCheckRollup` + `jobs` + `annotations`):**
        - Toàn bộ check fail trên PR phải là `CheckRun` có kết luận `FAILURE` (nếu có bất kỳ `StatusContext` hay job nào fail vì lỗi biên dịch/test/lint $\to$ **DỪNG**).
        - Trích xuất `<run_id>` và `<job_id>` từ `detailsUrl` (mẫu `/actions/runs/<run_id>/job/<job_id>`, hoặc dự phòng qua `GET /repos/{owner}/{repo}/commits/<head_sha>/check-runs`), sau đó gọi `GET /repos/{owner}/{repo}/actions/runs/<run_id>/jobs` và `GET /repos/{owner}/{repo}/check-runs/<job_id>/annotations`.
        - Khẳng định **mọi** job fail đều có `steps == []` (`0` bước được chạy) **VÀ** có annotation mức `failure` chứa thông điệp khóa thanh toán/hạn mức tài khoản GitHub (`account payments have failed` hoặc `spending limit needs to be increased`).
     2. **Cổng 2 — Kiểm toán Ruleset & Branch Protection (Fail-Closed, Non-Truncated):**
        - Gọi REST trên nhánh mặc định (`<default_branch>`): `GET /repos/{owner}/{repo}/branches/<default_branch>/protection`, `GET /repos/{owner}/{repo}/rulesets`, và `GET /repos/{owner}/{repo}/rules/branches/<default_branch>`.
        - Nếu REST trả `HTTP 200`, xác nhận KHÔNG có `required_status_checks` nào đang bật (`enforcement == "active"` hoặc rule tổng hợp có `type == "required_status_checks"`). Nếu có $\to$ **DỪNG**.
        - Nếu REST trả `HTTP 403` (ví dụ repo `private` gói Free), bắt buộc truy vấn dự phòng qua GraphQL (`gh api graphql`): đọc `repository.rulesets(first: 20, includeParents: true)` (kèm `rules(first: 20)` bên trong từng ruleset) và `repository.branchProtectionRules(first: 20)`. Yêu cầu **fail-closed**: `HTTP 200`, `errors` rỗng/vắng mặt, mọi connection (`rulesets`, `rules`, `branchProtectionRules`) đều **không null**, và **`pageInfo.hasNextPage == false` ở mọi cấp** (kể cả `rules` lồng nhau); đồng thời không có ruleset `ACTIVE` / protection rule nào yêu cầu `REQUIRED_STATUS_CHECKS` / `requiresStatusChecks`. Nếu bị cắt trang (`hasNextPage == true`), null hoặc có check bắt buộc $\to$ **DỪNG**.
     3. **Cổng 3 — Phê duyệt Tường minh của Người dùng:**
        - Báo cáo đầy đủ bằng chứng Cổng 1 + Cổng 2 và chỉ được phép chạy mô phỏng thay thế khi có **chỉ thị/xác nhận rõ ràng của User** (trước hoặc tại thời điểm xử lý PR).
     4. **Cổng 4 — Mô phỏng CI trên Bản sao Sạch (`/tmp`) & Đăng Biên lai Đã Redact:**
        - Clone sạch nhánh PR ra `/tmp` (`git clone --depth 1 --branch <pr_branch> --single-branch ... /tmp/ci-clean-...`) và gỡ biến môi trường Hub cục bộ (`env -u CCBA_HUB_PATH -u HUB_PATH`) để đảm bảo zero-leakage từ file untracked hoặc trạng thái máy local.
        - Chọn runtime container **đúng kiến trúc gốc (`uname -m`) thuộc họ image khai báo trong workflow** (tuyệt đối không gắn cứng tên tag cụ thể trong skill và không chạy image lệch kiến trúc qua emulation nếu đã có tag gốc tương ứng); mọi job phụ thuộc secrets hoặc dịch vụ ngoài không khả dụng tại local phải ghi nhận tường minh `SKIPPED_NO_SECRETS`.
        - Rà soát và **khử toàn bộ token/password/certificate** (redact) trong báo cáo kết quả mô phỏng trước khi đăng lên PR qua `gh pr comment <PR> -F <tmp_report>`, sau đó xóa sạch `/tmp/ci-clean-*`.

4. **Chốt chặn Review Requests của Copilot (Chống Race Condition Merge Sớm):**
   - Trước khi đọc comments, Agent **bắt buộc phải kiểm tra xem Copilot đã nộp bài review xong hay chưa**:
     ```bash
     gh pr view --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.author.login]}'
     ```
   - *Quy tắc bắt buộc:*
     - Nếu danh sách `pending` chứa `copilot-pull-request-reviewer` (hoặc bot review) HOẶC Copilot chưa xuất hiện trong `reviewed` (nếu PR vừa tạo chưa quá 2 phút): Có nghĩa là Copilot **vẫn đang phân tích và chưa Submit Review**. Agent **tuyệt đối không được merge ngay**, mà phải dừng lượt hoặc chờ Copilot hoàn tất nộp bài (dùng `schedule`).
     - Chỉ khi Copilot đã hoàn tất lượt review và nộp bài vào `reviews` (hoặc không có review pending), Agent mới chuyển sang bước 5.

5. **Thực hiện đối soát bình luận & Review Body của Copilot trên PR (Hard Blocker):**
   ```bash
   python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/validation/audit_pr_comments.py"
   ```
   - Script tự động quét toàn bộ:
     - `reviews`: Quét `author.login` và chặn đứng nếu có `### 🟡 Changes recommended` hoặc `state == CHANGES_REQUESTED`.
     - `comments`: Quét inline comments trên các tệp thay đổi.
   - Nếu script trả về exit code 1 (`[FAIL] Changes recommended`), Agent **tuyệt đối không được merge**. Phải đánh giá và thực hiện chỉnh sửa mã nguồn cục bộ, commit & push cập nhật, và cập nhật `walkthrough.md` trước khi tiếp tục.
   - Nếu phát hiện các góp ý hợp lý (VALID) chưa sửa, hoặc các góp ý không hợp lý chưa được giải trình trong `walkthrough.md`, Agent phải giải trình hoặc sửa lỗi cục bộ và push cập nhật trước khi merge.
   - *Lưu ý quan trọng (ADR-0045 Spoke Leakage Guard & RULE-4.10):* Script `audit_pr_comments.py` tự động tìm kiếm đối soát theo thứ tự ưu tiên: `.md/knowledge/reports/walkthrough.md` (hoặc `walkthrough.md` tại gốc repo). Tuyệt đối KHÔNG lưu tại `.md/walkthrough.md` để tránh vi phạm rào chắn cấu trúc thư mục. BẮT BUỘC phải ghi nhận trực tiếp vào `.md/knowledge/reports/walkthrough.md` kèm mã `review_id` (`PRR_...`) hoặc comment `id` thay vì chỉ lưu trong thư mục brain artifact.

6. **Tiến hành Merge khi 100% điều kiện đạt chuẩn:**
   - **Kiểm tra Chiến lược Merge cho `verify-ccba-*` Re-Anchor (`RULE-2.21` — Bắt buộc `--merge`):**
     Trước khi merge, kiểm tra xem PR có chạm tệp neo `verify-ccba-*/SKILL.md` hay không:
     ```bash
     git diff --name-only origin/<default_branch>..HEAD -- 'packages/ccba-harness/.agents/skills/verify-ccba-*/SKILL.md'
     ```
     Nếu có cập nhật `sync_commit` / `covered_sha256`: **BẮT BUỘC dùng `--merge` (`gh pr merge [PR_NUMBER] --merge --delete-branch`), TUYỆT ĐỐI CẤM `--squash`**, để mã commit trước đó được neo trong `sync_commit` còn tồn tại cho `git cat-file -e` trên nhánh chính; ngay sau khi `pull`, kiểm chứng `git cat-file -e <sync_commit>^{commit}` trả mã `0`.
   - Nếu `gh` đã đăng nhập, CI pass (100% xanh) và Copilot review đã xử lý xong: Thực hiện merge và xóa remote branch tự động (mặc định dùng Squash and Merge để giữ lịch sử nhánh main tinh gọn, ngoại trừ ca re-anchor `RULE-2.21` ở trên phải dùng `--merge`):
     ```bash
     # Mặc định (không chạm verify-ccba-*/SKILL.md):
     gh pr merge --squash --delete-branch
     # Ngoại lệ RULE-2.21 (PR có commit code + commit re-anchor sync_commit):
     gh pr merge --merge --delete-branch
     ```
   - *Cơ chế Xử lý Linh hoạt khi CI đang chạy:*
     Kiểm tra thuộc tính `allow_auto_merge` của repository qua GitHub REST API (cảnh báo: `gh repo view --json autoMergeAllowed` lỗi `Unknown JSON field` trên `gh` CLI v2+) trước khi áp dụng cờ `--auto`:
     ```bash
     # Bước 1: Tra cứu xem repo có cho phép auto-merge không qua REST API:
     gh api repos/{owner}/{repo} --jq .allow_auto_merge
     ```
     - **Trường hợp A (Nếu kết quả là `true`):** Thực thi auto-merge (thay `--squash` bằng `--merge` nếu thuộc ngoại lệ `RULE-2.21`):
       ```bash
       gh pr merge [PR_NUMBER] --squash --delete-branch --auto
       ```
     - **Trường hợp B (Nếu kết quả là `false` — như Hub hiện tại):** Giám sát CI qua Reactive Wakeup (hoặc `schedule` phân tầng `240s` lần đầu rồi `60s` pha đuôi; cấm gọi thêm tool khác trong cùng lượt với `schedule`) rồi merge (dùng `--merge` nếu thuộc ngoại lệ `RULE-2.21`):
       ```bash
       gh pr checks [PR_NUMBER] --watch
       # Dừng gọi công cụ (End Turn). Khi Reactive Wakeup báo 100% checks xanh, thực hiện:
       gh pr merge [PR_NUMBER] --squash --delete-branch
       # Nếu đang đứng trên git worktree cô lập (RULE-4.21), tách HEAD trước khi merge rồi gỡ worktree để tránh chạm thư mục gốc đang bận hoặc đang ở nhánh đồng đẳng:
       git -C <worktree_path> checkout --detach && gh pr merge [PR_NUMBER] --squash && git push origin --delete [HEAD_BRANCH]
       ```
   - Nếu `gh` chưa đăng nhập: Sử dụng `browser_subagent` truy cập trang PR, chờ CI và Review hoàn tất rồi chọn **Squash and merge** (hoặc **Create a merge commit** nếu thuộc ngoại lệ `RULE-2.21`) -> **Confirm** -> **Delete branch**.

---

**Tiêu chí hoàn thành:** CI 100% xanh (hoặc đối với trường hợp Quota-Lock thỏa đủ 4 cổng dự phòng fail-closed: mọi job fail đều có `steps == []` và failure annotation khóa thanh toán, kiểm toán REST/GraphQL non-truncated xác nhận không có `required_status_checks` đang bật, User đã xác nhận, bản sao sạch `/tmp` chạy xanh kèm danh sách job secret `SKIPPED_NO_SECRETS` và biên lai đã redact được đăng lên PR), Copilot review giải quyết xong và PR đã merge thành công.

---

## Bước 2: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy danh sách các commit của feature branch hiện tại (so sánh với `origin/main`) **trước khi** chuyển nhánh:
   ```bash
   git log origin/main..HEAD --oneline
   ```
2. Cập nhật nội dung tóm tắt thay đổi và kết quả nghiệm thu vào tệp tin `walkthrough.md`.

---

**Tiêu chí hoàn thành:** Tệp walkthrough.md được cập nhật đầy đủ tóm tắt thay đổi.

---

## Bước 3: Sync Local Codebase, Auto-Close Local Issue & Dọn dẹp

1. Kiểm tra trạng thái làm việc (working tree) để đảm bảo không có file nào bị dơ (uncommitted changes):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Nếu có thay đổi chưa commit, hãy commit hoặc stash trước khi chuyển nhánh.

2. Thu hồi tiến trình kiểm thử mồ côi và đồng bộ nhánh `main` an toàn (chống treo Pager & tôn trọng phiên đồng đẳng `RULE-4.21`):
   ```bash
   python -c "from scripts.eval.process_safety import ensure_single_instance; ensure_single_instance('pytest')"
   # Nếu thư mục gốc đang ở nhánh `main` sạch (ahead == 0):
   git --no-pager checkout main && git pull origin main
   # Nếu thư mục gốc đang đứng ở nhánh đồng đẳng khác `main` hoặc `main` có phiên khác (ahead > 0):
   # KHÔNG chạm working tree gốc; cập nhật ref `main` cục bộ an toàn bằng:
   git fetch --prune origin main:main
   ```

3. Xóa branch feature cục bộ an toàn:
   ```bash
   git branch -D [feature_branch_name]
   ```

3b. **Dọn dẹp triệt để Stale Tracking Refs & Nhánh Mồ Côi Remote Đã Merge (ADR-0045 & Git Hygiene):**
   - Đồng bộ và dọn sạch các nhánh remote đã bị xóa:
     ```bash
     git fetch --prune
     ```
   - Rà soát các nhánh tạm trên remote có liên quan đến tính năng vừa phát hành:
     ```bash
     git ls-remote --heads origin "*[feature_keyword]*"
     ```
   - *Quy tắc An Toàn Xóa Nhánh Remote (Safe Remote Deletion Invariant):*
     Agent **CHỈ ĐƯỢC PHÉP** xóa nhánh remote nếu nhánh đó thỏa mãn một trong hai điều kiện bất biến:
     1. Là nhánh head chính thức của chính PR vừa được squash-merge thành công (`gh pr view --json headRefName`).
     2. Hoặc nhánh remote đó đã được tích hợp hoàn toàn vào `origin/main` (kiểm tra `git log origin/main..origin/[branch_name]` trả về rỗng).
     Tuyệt đối cấm xóa các nhánh chưa merge (có commit mới hơn `origin/main`) để tránh xóa nhầm nhánh đang phát triển dở dang của đồng đội trên thiết bị khác!
     ```bash
     # Kiểm tra diff (nếu không có output tức là nhánh đã được merge 100% vào main):
     git log origin/main..origin/[orphan_branch_name] --oneline
     # Chỉ thực hiện xóa an toàn khi lệnh trên không trả về commit nào:
     git push origin --delete [orphan_branch_name]
     ```
   - Nếu đang thao tác trên Hub, đồng bộ bản cập nhật kỹ năng sang Spoke:
     ```bash
     python scripts/sync_spoke.py --spoke [spoke_path] --sync-item ccba-release-feature --apply
     ```

4. **Tự động đóng Issue Cục bộ (Offline Knowledge Base Mirror):**
   - Nếu PR giải quyết một issue cụ thể (ví dụ `#228`), kiểm tra tệp tin tương ứng tại `.md/knowledge/issues/issue-XXX.md`.
   - Cập nhật trường trạng thái trong metadata: `status: closed` (hoặc `state: closed`) kèm ghi chú liên kết PR đã merge.

5. **Cập nhật Proposal Lifecycle, Compile Catalog & Nộp PR Walkthrough (Post-Merge Governance):**
   - Nếu PR xuất phát từ một Proposal trong `.agents/proposals/`, cập nhật frontmatter tệp proposal tương ứng: `status: "merged"`, `merged_pr: "#[PR_NUMBER]"`, `merged_commit: "[HASH]"`, `merged_date: "[YYYY-MM-DD]"`.
   - Tái biên dịch Catalog SSoT:
     ```bash
     python scripts/governance/compile_catalog.py
     ```
   - *Quy trình Lưu trữ Walkthrough qua PR Riêng (Bắt buộc theo RULE-2.4, RULE-3.5, RULE-4.5, RULE-4.21 & Pre-Push Lock):*
     Hook `pre-push` cấm tuyệt đối push trực tiếp lên `main` (`Direct push to 'main' is strictly prohibited!`). Không chạy mù `git add` cả 3 đường dẫn khi ở Spoke có thể không theo dõi các tệp walkthrough trong git: kiểm tra **từng đường dẫn theo logic OR** bằng `git ls-files --error-unmatch` trước khi mở PR lưu trữ (giữ nguyên ngoại lệ Step 1.5 cho phép ghi tạm `.md/knowledge/reports/walkthrough.md` trước khi merge nếu cần cho `audit_pr_comments.py` đọc rồi dọn sạch):
     ```bash
     # Xác định Hub vs Spoke & thu thập từng đường dẫn được git track (logic OR, đa nền tảng Windows/Linux):
     python -c '
     import pathlib, subprocess
     remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True)
     is_hub = "ccba-agent-platform" in remote.lower()
     candidates = ["walkthrough.md", ".md/knowledge/reports/walkthrough.md", ".agents/proposals"]
     tracked = [
         p for p in candidates
         if pathlib.Path(p).exists()
         and subprocess.run(
             ["git", "ls-files", "--error-unmatch", p],
             stdout=subprocess.DEVNULL,
             stderr=subprocess.DEVNULL,
         ).returncode == 0
     ]
     print(f"is_hub={is_hub} tracked={tracked}")
     '

     # Chỉ tạo PR `docs/walkthrough-pr-[PR_NUMBER]` nếu `is_hub=True` HOẶC `len(tracked) > 0`;
     # ngược lại trên Spoke không track các path trên, giữ Artifact walkthrough tại <appDataDir>/brain/...:
     # Trường hợp A (thư mục gốc đang ở nhánh `main` sạch):
     git checkout main && git pull origin main
     git checkout -b docs/walkthrough-pr-[PR_NUMBER]
     # Trường hợp B (thư mục gốc đang ở nhánh đồng đẳng khác `main` hoặc `main` ahead > 0):
     # Tạo worktree cô lập tại <walkthrough_wt> từ `origin/main` thay vì chạm working tree gốc:
     git fetch --prune origin main:main
     git worktree add -b docs/walkthrough-pr-[PR_NUMBER] <walkthrough_wt> origin/main

     # Trong nhánh docs/walkthrough-pr-[PR_NUMBER]: chỉ stage <tracked_paths> (hoặc tệp mới tại Hub);
     # tệp .md/knowledge/reports/walkthrough.md dẫn về gốc repo bằng ../../../ (RULE-2.4) và không chứa file:/// (RULE-3.5):
     # Nếu có PR song song vừa cập nhật .md/knowledge/reports/walkthrough.md trên origin/main gây BEHIND/xung đột:
     # reset/rebase nhánh lên origin/main để bảo toàn nguyên vẹn mục của PR đồng đẳng ở đầu tệp và nối mục PR hiện tại xuống dưới (cấm ghi đè xóa mất biên bản đồng đẳng), rồi đẩy bằng git push --force-with-lease.
     git add -- <tracked_paths>
     git commit -m "docs(walkthrough): record release feature PR #[PR_NUMBER] completion and review matrix"
     git push -u origin docs/walkthrough-pr-[PR_NUMBER]
     # Ghi mô tả PR vào tệp scratch (ví dụ /tmp/pr_walkthrough_body.md), chạy tiền kiểm door-triage (vì compute_cumulative_streak K>=3/72h vẫn nâng PR tài liệu lên ONE_WAY_DOOR đòi TradeoffCard) rồi truyền qua -F:
     python -m ccba_harness door-triage <tracked_paths> --pr-body-file /tmp/pr_walkthrough_body.md --enforce-tradeoff-card
     gh pr create --head docs/walkthrough-pr-[PR_NUMBER] --base main --assignee "@me" --title "docs(walkthrough): record release feature PR #[PR_NUMBER] completion" -F /tmp/pr_walkthrough_body.md
     gh pr checks --watch
     # Nếu đang dùng worktree cô lập, tách HEAD và gỡ worktree trước khi xóa nhánh remote:
     git -C <walkthrough_wt> checkout --detach && git worktree remove <walkthrough_wt> && git worktree prune
     gh pr merge [WALKTHROUGH_PR_NUMBER] --squash && git push origin --delete docs/walkthrough-pr-[PR_NUMBER]
     git fetch --prune origin main:main
     ```
   - **Tiêu chí hoàn thành:** Nếu tạo PR lưu trữ (`is_hub=True` hoặc `len(tracked) > 0`): `validate_docs.py` (không chứa `file:///`), `door-triage --enforce-tradeoff-card` trả về Exit Code `0`, PR lưu trữ vượt qua 100% CI Checks và được squash-merge sạch sẽ về `main`; nếu là Spoke không track các đường dẫn trên (`len(tracked) == 0`), Artifact walkthrough nằm tại `<appDataDir>/brain/...` mà không phát sinh file rác trong repo.

6. **Khôi phục Tác Vụ Song Song Đã Stash (Guarded Post-Release Stash Recovery):**
   - Kiểm tra xem Bước 0 có tạo stash cho PR hiện tại hay không:
     ```bash
     git stash list --grep="wip: concurrent work before release PR #[PR_NUMBER]"
     ```
   - Nếu tìm thấy mục stash tương ứng, xác định đúng chỉ mục định danh `stash@{N}` từ kết quả trên và khôi phục có rào chắn bảo vệ:
     ```bash
     git stash pop stash@{N}
     ```
     *(Lưu ý: Bắt buộc truyền rõ `stash@{N}` để tránh pop nhầm `stash@{0}` nếu danh sách có nhiều bản stash song song).*
   - *Rào chắn chống xung đột (Conflict Escape Hatch):* Nếu `git stash pop stash@{N}` gặp xung đột merge (conflict), Agent **tuyệt đối không để working tree ở trạng thái unmerged hoặc chứa tệp untracked rò rỉ trên main**. BẮT BUỘC chạy ngay:
     ```bash
     git reset --merge && git clean -df
     ```
     Lệnh này sẽ dọn sạch cả xung đột file theo dõi và các tệp untracked vừa bung ra, khôi phục nhánh `main` về trạng thái sạch sẽ 100%, trong khi bản stash vẫn được giữ an toàn trong stash list. Sau đó, thông báo rõ ràng cho người dùng: *"Phát hiện xung đột khi pop stash lên main. Đã khôi phục trạng thái sạch của main bằng `git reset --merge && git clean -df`. Bản stash vẫn được bảo toàn; vui lòng tạo nhánh mới và áp dụng bằng `git checkout -b <branch> && git stash apply stash@{N}`"*.

---

**Tiêu chí hoàn thành:** Nhánh main cục bộ đồng bộ, nhánh feature xóa và issue cục bộ closed.

---

## Bước 4: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất rõ ràng:
   - ✅ Feature đã được tích hợp thành công vào `main`.
   - 🗑️ Branch cục bộ và remote đã được dọn dẹp sạch sẽ.
   - 📌 Issue liên quan đã được đóng (trên GitHub và CSDL cục bộ).
   - 📝 Lịch sử thay đổi `walkthrough.md` đã được lưu trữ hoàn tất.


**Tiêu chí hoàn thành:** Toàn bộ trạng thái tích hợp, dọn dẹp và đóng issue được thông báo hoàn tất.
