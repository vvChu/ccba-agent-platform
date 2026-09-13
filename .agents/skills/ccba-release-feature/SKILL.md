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
  version: "1.1.0"
  author: "CCBA Hub"
triggers:
- release
- merge PR
- phát hành
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge), kiểm tra Copilot Review, tự động đóng issue và dọn dẹp môi trường.

## Bước 0: Thực thi Kiểm thử Toàn diện Slow Integration Tests (Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải chạy kiểm thử toàn bộ tập test `slow` và `stress`** để đảm bảo các bài test cào mạng/tích hợp không bị hỏng ngầm (test decay):

1. **Kiểm tra môi trường hiện tại (Hub vs Spoke):**
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
2. Nếu có bài test nào thất bại, Agent **phải dừng quy trình release ngay lập tức** để tiến hành sửa lỗi trước khi tiếp tục.

---

**Tiêu chí hoàn thành:** 100% bài kiểm thử slow và stress đều vượt qua thành công.

---

## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. **Lấy thông tin PR và Branch hiện hành (Platform-Agnostic):**
   ```bash
   git branch --show-current
   gh pr view --json number,title,state,headRefName
   ```

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

2. Quay về branch `main` và kéo code mới nhất:
   ```bash
   git checkout main && git pull origin main
   ```

3. Xóa branch feature cục bộ an toàn:
   ```bash
   git branch -D [feature_branch_name]
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
