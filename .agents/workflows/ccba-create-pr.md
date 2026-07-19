---
description: Push code hiện tại và tạo Pull Request tự động
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Create Pull Request

Quy trình tự động hóa đẩy mã nguồn và khởi tạo Pull Request siêu tốc.

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

1. Kiểm tra xem branch hiện tại có thay đổi **cấu trúc** (thêm/bớt/rename thư mục, package, script, skill, workflow) không:
   ```bash
   git diff main --stat --name-only | grep -E "(scripts/|packages/|\.agents/skills/|\.agents/workflows/|pyproject\.toml)"
   ```
2. Nếu có thay đổi cấu trúc:
   - Chạy `validate_docs` để phát hiện liên kết hỏng:
     ```bash
     python scripts/validate_docs.py . --changed
     ```
   - Nhắc nhở người dùng: *"Phát hiện thay đổi cấu trúc. Bạn đã chạy `architecture-sync` để cập nhật tài liệu kiến trúc chưa? Chạy ngay nếu chưa."*
3. Nếu không có thay đổi cấu trúc → bỏ qua bước này.

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
