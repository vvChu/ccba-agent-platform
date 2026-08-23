---
description: Push code hiện tại và tạo Pull Request tự động
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-create-pr
triggers:
- create PR
- pull request
- tạo PR
---
# Workflow: Create Pull Request

Quy trình tự động hóa đẩy mã nguồn và khởi tạo Pull Request siêu tốc.

## Bước 0: Main Branch Guard (Tự động phát hiện & sửa sai)

1. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
2. **Nếu đang ở `main`**: Kiểm tra xem có commits chưa push không:
   ```bash
   git log origin/main..main --oneline
   ```
3. **Nếu có commits chưa push trên `main`** → Tự động tạo feature branch retroactively:
   a. Phân tích commit messages để suy ra loại công việc (`feat`, `fix`, `docs`, `refactor`, `chore`) và mô tả ngắn gọn.
   b. Đề xuất tên branch (ví dụ: `feat/architecture-sync-enforcement`) và xin xác nhận người dùng.
   c. Sau khi được đồng ý, thực hiện:
      ```bash
      # Tạo feature branch tại vị trí hiện tại (giữ nguyên commits)
      git branch [ten_branch]
      # Reset main về origin (xóa commits khỏi main)
      git reset --hard origin/main
      # Chuyển sang feature branch
      git checkout [ten_branch]
      ```
   d. Thông báo: *"Đã tự động tạo branch `[ten_branch]` từ N commits trên main. Main đã được reset về origin."*
4. **Nếu không có commits chưa push trên `main`** → Báo lỗi: *"Không có thay đổi nào trên main để tạo PR. Hãy tạo feature branch và commit trước."* Dừng workflow.
5. **Nếu đã ở feature branch** → Bỏ qua bước này, tiếp tục Bước 1.

## Bước 1: Kiểm định Chất lượng Local CI Eval Gates (Shift-Left Gate)

1. Kích hoạt toàn bộ hệ thống kiểm thử tự động và kiểm định tài liệu tại local TRƯỚC KHI đẩy code:
   ```bash
   .venv\Scripts\python scripts/run_harness_evals.py
   ```
2. **Quy tắc chặn lỗi tại nguồn:**
   - Nếu `run_harness_evals.py` trả về `PASS 100%`: Mã nguồn đạt chuẩn, tiếp tục Bước 2.
   - Nếu có Gate bị `FAIL` hoặc phát hiện Architecture Drift: Tạm dừng workflow, yêu cầu Agent/người dùng sửa lỗi tại local (hoặc chạy `python scripts/update_arch_stats.py`) và commit lại trước khi đẩy mã nguồn.

## Bước 2: Kiểm tra trạng thái và Push code lên remote

1. Kiểm tra trạng thái làm việc (working tree):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Đảm bảo không còn thay đổi chưa commit.
2. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
3. Đẩy branch lên origin và thiết lập upstream:
   ```bash
   git push -u origin [current_branch]
   ```

## Bước 3: Khởi tạo Pull Request

1. Kiểm tra xem GitHub CLI (`gh`) có hoạt động không:
   ```bash
   gh auth status
   ```
2. Nếu `gh` đã đăng nhập:
   - Tự động lấy danh sách 5 commit gần nhất để làm nội dung mô tả:
     ```bash
     git log -n 5 --pretty=format:"- %s"
     ```
   - Tự động tạo PR bằng dòng lệnh (thay thế tiêu đề dựa trên tên branch và body bằng mô tả commit):
     ```bash
     gh pr create --title "[Feature/Fix Title]" --body "[Commit List Description]" --base main --head [current_branch]
     ```
3. Nếu `gh` chưa đăng nhập:
   - Sử dụng `browser_subagent` mở link tạo PR động:
     - URL: Lấy từ `git remote get-url origin` chuyển thành dạng URL Pull Request.
     - Tiêu đề: Lấy từ tên branch (bỏ prefix `feature/`, `fix/`, viết hoa chữ cái đầu).
     - Nội dung: Tóm tắt từ 5 commit gần nhất (`git log -n 5 --pretty=format:"- %s"`).

## Bước 4: Thông báo kết quả

1. Trình bày đường dẫn PR, trạng thái kiểm thử CI và tiến trình yêu cầu review (Review Requests) cho người dùng.
2. Nhắc nhở người dùng: "PR đã được khởi tạo. GitHub Actions CI và GitHub Copilot Review đang chạy ngầm. Hãy gọi `/ccba-release-feature` khi CI đã xanh và Copilot đã hoàn tất lượt review để đối soát và merge."
