---
description: Merge PR, cleanup branch và cập nhật walkthrough
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge) và dọn dẹp môi trường.

## Bước 1: Merge PR trên GitHub

1. Kiểm tra xem GitHub CLI (`gh`) có hoạt động không:
   ```bash
   gh auth status
   ```
2. Nếu `gh` đã đăng nhập:
   - Kiểm tra trạng thái CI của PR hiện hành:
     ```bash
     gh pr checks
     ```
   - Nếu CI pass: Thực hiện merge và xóa remote branch tự động:
     ```bash
     gh pr merge --merge --delete-branch
     ```
3. Nếu `gh` chưa đăng nhập:
   - Sử dụng `browser_subagent` truy cập trang PR của branch hiện tại.
   - Chờ CI pass, click nút **Merge** -> **Confirm** -> **Delete branch**.
   - Báo lỗi cụ thể cho người dùng nếu CI thất bại hoặc có xung đột (conflict).

## Bước 2: Sync Local Codebase & Dọn dẹp

1. Quay về branch `main` và kéo code mới nhất:
   ```bash
   git checkout main && git pull origin main
   ```
2. Xóa branch feature cục bộ:
   ```bash
   git branch -d [feature_branch_name]
   ```

## Bước 3: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy danh sách các commit của feature vừa merge:
   ```bash
   git log origin/main..HEAD --oneline
   ```
2. Cập nhật nội dung tóm tắt thay đổi vào tệp tin `walkthrough.md`.

## Bước 4: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất:
   - ✅ Feature đã được tích hợp thành công.
   - 🗑️ Branch cục bộ đã được dọn dẹp.
   - 📝 Lịch sử thay đổi `walkthrough.md` đã cập nhật.
