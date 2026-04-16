---
description: Push code hiện tại và tạo Pull Request tự động
---

# Workflow: Create Pull Request

Khi user gọi `/create-pr`, thực hiện các bước sau:

## Bước 1: Push code lên remote

// turbo

1. Lấy tên branch hiện tại:

```bash
git branch --show-current
```

// turbo
2. Push branch lên origin (set upstream):

```bash
git push -u origin [current_branch]
```

## Bước 2: Tạo Pull Request

3. Sử dụng `browser_subagent` để tạo PR:
   - URL: `https://github.com/vvChu/mdconverter/pull/new/[current_branch]`
   - Tiêu đề: Lấy từ tên branch (bỏ prefix feature/fix, Capitalize)
   - Nội dung: Tóm tắt từ 5 commit gần nhất (`git log -n 5 --pretty=format:"- %s"`)

2. Kiểm tra trang sau khi tạo để xác nhận CI đã bắt đầu chạy.

## Bước 3: Thông báo kết quả

5. Báo cáo cho user:
   - Link PR vừa tạo
   - Trạng thái CI (Đang chạy/Chưa chạy)
   - Nhắc nhở: "Hãy gọi `/release-feature` khi CI đã xanh để merge và cleanup."
