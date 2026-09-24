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
  version: "1.2.1"
  author: "CCBA Hub"
triggers:
- release
- merge PR
- phát hành
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge), kiểm tra Copilot Review, tự động đóng issue và dọn dẹp môi trường.

## Bước 0: Kiểm soát Buồng kín & Kiểm thử Toàn diện (Hermetic Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải tuân thủ Giao thức TRIHT (Tiered Release Integrity & Hermetic Teardown)** gồm 3 giai đoạn để ngăn chặn hoàn toàn nguy cơ mất mã nguồn và chống gián đoạn chuyển nhánh:

1. **Cổng 0.1 — Khóa Sạch Sẽ Tiền Kiểm Tra (Pre-Flight Cleanliness Lock):**
   - *Bắt buộc kiểm tra:* Repository phải ở trạng thái sạch sẽ 100% (không có tệp modified hoặc untracked chưa commit). Tuyệt đối cấm release khi mã nguồn cục bộ chưa được commit vào PR:
     ```bash
     python scripts/validation/check_release_cleanliness.py --phase pre
     ```
   - Nếu phát hiện tệp chưa commit, Agent **phải dừng quy trình ngay lập tức** để commit hoặc stash có chủ đích trước khi tiếp tục.

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
     python scripts/validation/check_release_cleanliness.py --phase post
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

   - **Sàng lọc Mức độ Nguy hiểm (Merge Danger Triage):**
     * Đọc trường `## Merge Danger Assessment` từ mô tả PR:
       - Nếu **Two-way door** và bán kính **Localized**: Áp dụng *Fast-path review* (kiểm tra nhanh CI và Copilot comments để merge).
       - Nếu **One-way door** hoặc bán kính **Monorepo-wide / Spoke-affecting**: Bắt buộc tiến hành *Deep review*, kiểm tra kỹ lưỡng các ảnh hưởng gãy vỡ hợp đồng giao diện, tính tương thích ngược với Spoke downstream trước khi quyết định merge.

2. **Kiểm tra xác thực GitHub CLI (`gh`):**
   ```bash
   gh auth status
   ```

3. **Kiểm tra trạng thái GitHub Actions CI:**
   ```bash
   gh pr checks
   ```
   - *Rào chắn Zero-Polling CI:* 
     - Nếu các checks đang ở trạng thái `pending`, Agent có thể khởi chạy `gh pr checks --watch` rồi **lập tức dừng gọi công cụ (End Turn)** để hệ thống đánh thức qua cơ chế *Reactive Wakeup* khi CI xanh.
     - **Tuyệt đối nghiêm cấm** chạy vòng lặp gọi `manage_task status` liên tiếp nhiều lần để thăm dò task `--watch`.

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
   python scripts/validation/audit_pr_comments.py
   ```
   - Script tự động quét toàn bộ:
     - `reviews`: Quét `author.login` và chặn đứng nếu có `### 🟡 Changes recommended` hoặc `state == CHANGES_REQUESTED`.
     - `comments`: Quét inline comments trên các tệp thay đổi.
   - Nếu script trả về exit code 1 (`[FAIL] Changes recommended`), Agent **tuyệt đối không được merge**. Phải đánh giá và thực hiện chỉnh sửa mã nguồn cục bộ, commit & push cập nhật, và cập nhật `walkthrough.md` trước khi tiếp tục.
   - Nếu phát hiện các góp ý hợp lý (VALID) chưa sửa, hoặc các góp ý không hợp lý chưa được giải trình trong `walkthrough.md`, Agent phải giải trình hoặc sửa lỗi cục bộ và push cập nhật trước khi merge.
   - *Lưu ý quan trọng (ADR-0045 Spoke Leakage Guard & RULE-4.10):* Script `audit_pr_comments.py` tự động tìm kiếm đối soát theo thứ tự ưu tiên: `.md/knowledge/reports/walkthrough.md` (hoặc `walkthrough.md` tại gốc repo). Tuyệt đối KHÔNG lưu tại `.md/walkthrough.md` để tránh vi phạm rào chắn cấu trúc thư mục. BẮT BUỘC phải ghi nhận trực tiếp vào `.md/knowledge/reports/walkthrough.md` kèm mã `review_id` (`PRR_...`) hoặc comment `id` thay vì chỉ lưu trong thư mục brain artifact.

6. **Tiến hành Merge khi 100% điều kiện đạt chuẩn:**
   - Nếu `gh` đã đăng nhập, CI pass (100% xanh) và Copilot review đã xử lý xong: Thực hiện merge và xóa remote branch tự động (sử dụng Squash and Merge để giữ lịch sử nhánh main tinh gọn):
     ```bash
     gh pr merge --squash --delete-branch
     ```
   - *Tùy chọn Auto-Merge:* Nếu CI vẫn đang chạy nốt những giây cuối, có thể kích hoạt cờ tự động merge:
     ```bash
     gh pr merge --squash --delete-branch --auto
     ```
   - Nếu `gh` chưa đăng nhập: Sử dụng `browser_subagent` truy cập trang PR, chờ CI và Review hoàn tất rồi chọn **Squash and merge** -> **Confirm squash and merge** -> **Delete branch**.

---

**Tiêu chí hoàn thành:** CI 100% xanh, Copilot review giải quyết xong và PR đã merge thành công.

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

2. Thu hồi tiến trình kiểm thử mồ côi và quay về branch `main` an toàn (chống treo Pager):
   ```bash
   python -c "from scripts.eval.process_safety import ensure_single_instance; ensure_single_instance('pytest')"
   git --no-pager checkout main && git pull origin main
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

5. **Cập nhật Proposal Lifecycle & Compile Catalog (Post-Merge Governance):**
   - Nếu PR xuất phát từ một Proposal trong `.agents/proposals/`, cập nhật frontmatter tệp proposal tương ứng: `status: "merged"`, `merged_pr: "#[PR_NUMBER]"`, `merged_commit: "[HASH]"`, `merged_date: "[YYYY-MM-DD]"`.
   - Tái biên dịch Catalog SSoT:
     ```bash
     python scripts/governance/compile_catalog.py
     ```
   - Commit cập nhật `walkthrough.md` và proposal lên `main`:
     ```bash
     git add walkthrough.md .agents/proposals/ && git commit -m "docs(walkthrough): record release feature PR #[PR_NUMBER] completion and review matrix" && git push origin main
     ```

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
