---
description: Push code hiện tại và tạo Pull Request tự động
applies_to:
  - "Phần mềm"
bundle: "_software"
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

## Bước 1: Kiểm tra trạng thái và Push code lên remote

1. Kiểm tra trạng thái làm việc (working tree):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Đảm bảo không còn thay đổi chưa commit. Nếu có, hãy commit các thay đổi đó trước khi tiến hành push.
2. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
3. Đẩy branch lên origin và thiết lập upstream:
   ```bash
   git push -u origin [current_branch]
   ```

## Bước 2: Kiểm tra Đồng bộ Tài liệu Kiến trúc (Architecture Sync Gate)

1. Hệ thống CI (`scripts/run_harness_evals.py`) sẽ tự động quét biến động kiến trúc (Architecture Drift).
2. Nếu anh có thay đổi cấu trúc (thêm thư mục package, skill, workflow) nhưng CI báo lỗi Drift, vui lòng chạy `python scripts/update_arch_stats.py` và commit lại trước khi tạo PR.
3. Nếu không có thay đổi cấu trúc hoặc CI báo xanh → tiếp tục Bước 3.

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

1. Trình bày đường dẫn PR và trạng thái kiểm thử CI cho người dùng.
2. Nhắc nhở người dùng: "Hãy gọi `/ccba-release-feature` khi CI đã xanh để merge và dọn dẹp."
