---
description: Merge PR, cleanup branch và cập nhật walkthrough
applies_to:
  - "Phần mềm"
bundle: "_software"
disable-model-invocation: true
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge) và dọn dẹp môi trường.

## Bước 0: Thực thi Kiểm thử Toàn diện Slow Integration Tests (Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải chạy kiểm thử toàn bộ tập test `slow` và `stress` trên toàn bộ packages** (thông qua cơ chế Dynamic Discovery) để đảm bảo các bài test cào mạng/tích hợp không bị hỏng ngầm (test decay):
```bash
python scripts/eval/run_isolated_tests.py --all --stress
```
- Nếu có bài test nào thất bại, Agent **phải dừng quy trình release ngay lập tức** để tiến hành sửa lỗi trước khi tiếp tục.


## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. Lấy và ghi nhớ tên branch hiện hành (Feature Branch Name) trước khi thực hiện dọn dẹp:
   ```bash
   git branch --show-current
   ```
2. Kiểm tra xem GitHub CLI (`gh`) có hoạt động không:
   ```bash
   gh auth status
   ```
3. Thực hiện đối soát bình luận của Copilot trên PR:
   ```bash
   gh api repos/:owner/:repo/pulls/[PR_NUMBER]/comments --jq '.[] | {id: .id, path: .path, line: .line, body: .body}'
   ```
   *Quy tắc bắt buộc:* 
   - Kể cả khi quy trình `/ccba-create-pr` đã bị quá thời gian chờ (timeout) đối với Copilot, khi thực hiện `/ccba-release-feature` Agent **bắt buộc phải chạy lại đối soát comments** trước khi merge.
   - Nếu phát hiện bất kỳ bình luận mới nào của Copilot (vừa được tạo sau thời điểm timeout), Agent phải tạm dừng quy trình merge, đánh giá và thực hiện chỉnh sửa mã nguồn cục bộ, commit & push cập nhật, và cập nhật `walkthrough.md` trước khi tiếp tục.
   - Nếu phát hiện các góp ý hợp lý (VALID) chưa sửa, hoặc các góp ý không hợp lý chưa được giải trình trong `walkthrough.md`, script sẽ báo lỗi chặn merge để Agent tiến hành sửa lỗi cục bộ và push cập nhật trước.
4. Nếu `gh` đã đăng nhập và đối soát thành công:
   - Kiểm tra trạng thái CI của PR hiện hành:
     ```bash
     gh pr checks
     ```
   - Nếu CI pass: Thực hiện merge và xóa remote branch tự động (sử dụng Squash and Merge để giữ lịch sử nhánh main tinh gọn):
     ```bash
     gh pr merge --squash --delete-branch
     ```
5. Nếu `gh` chưa đăng nhập:
   - Sử dụng `browser_subagent` truy cập trang PR của branch hiện tại.
   - Chờ CI pass, chọn **Squash and merge** -> **Confirm squash and merge** -> **Delete branch**.
   - Báo lỗi cụ thể cho người dùng nếu CI thất bại hoặc có xung đột (conflict).

## Bước 2: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy danh sách các commit của feature branch hiện tại (so sánh với main/origin/main) **trước khi** chuyển nhánh:
   ```bash
   git log origin/main..[feature_branch_name] --oneline
   ```
2. Cập nhật nội dung tóm tắt thay đổi vào tệp tin `walkthrough.md`.

## Bước 3: Sync Local Codebase & Dọn dẹp

1. Kiểm tra trạng thái làm việc (working tree) để đảm bảo không có file nào bị dơ (uncommitted changes):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Nếu có thay đổi chưa commit (ví dụ tệp tạm hoặc hotfix), hãy commit hoặc stash trước khi chuyển nhánh.
2. Quay về branch `main` và kéo code mới nhất:
   ```bash
   git checkout main && git pull origin main
   ```
3. Xóa branch feature cục bộ. Vì GitHub thường sử dụng cơ chế Squash Merge hoặc Rebase Merge (khiến mã hash commit khác biệt), lệnh `git branch -d` có thể báo lỗi chưa merge. Hãy sử dụng lực lượng xóa để dọn dẹp sạch sẽ:
   ```bash
   git branch -D [feature_branch_name]
   ```

## Bước 4: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất:
   - ✅ Feature đã được tích hợp thành công.
   - 🗑️ Branch cục bộ đã được dọn dẹp (force-deleted).
   - 📝 Lịch sử thay đổi `walkthrough.md` đã cập nhật.
