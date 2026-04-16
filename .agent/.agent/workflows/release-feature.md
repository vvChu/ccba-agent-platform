---
description: Merge PR, cleanup branch và cập nhật walkthrough
---

# Workflow: Release Feature

Khi user gọi `/release-feature`, thực hiện các bước sau:

## Bước 1: Merge PR trên GitHub

1. Sử dụng `browser_subagent` để merge:
   - Tìm PR đang mở của branch hiện tại
   - Kiểm tra xem nút "Merge" có active không (CI passed?)
   - Nếu active: Click Merge -> Confirm -> Delete Branch
   - Nếu inactive: Báo lỗi user (do CI fail hoặc conflict)

## Bước 2: Sync Local Codebase

// turbo
2. Checkout về main và cập nhật:

```bash
git checkout main
git pull origin main
```

// turbo
3. Xóa branch feature local (vì đã merge & delete trên remote):

```bash
git branch -d [feature_branch_name]
```

## Bước 3: Cập nhật Walkthrough

4. Lấy danh sách commit message của feature vừa merge:
   - Dùng `git log` để tìm các commit từ point branch ra khỏi main.

2. Tự động tóm tắt thay đổi (AI Summarization) dựa trên commit messages.

3. Cập nhật file `walkthrough.md`:
   - Thêm section mới cho feature này.
   - Ghi rõ: Output files, tính năng mới, kết quả test.
   - Embed screenshot từ quá trình merge nếu có.

## Bước 4: Thông báo hoàn tất

7. Báo cáo:
   - ✅ Feature [Tên] đã release thành công!
   - 📉 Branch local đã xóa.
   - 📝 Walkthrough đã cập nhật.
