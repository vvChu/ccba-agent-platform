---
description: Tạo feature branch mới với cleanup tự động
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Tạo Feature Branch Mới

Khi user gọi `/new-feature`, thực hiện các bước sau:

## Bước 1: Chuẩn bị môi trường

// turbo

1. Checkout và cập nhật main:

```bash
git checkout main
git pull origin main
```

## Bước 2: Cleanup branches cũ

// turbo
2. Xóa các branch local đã merge:

```bash
git fetch -p
git branch --merged main | grep -v "main" | xargs -r git branch -d
```

## Bước 3: Hỏi thông tin feature

1. Hỏi user các câu hỏi sau:
   - "Đây là loại công việc gì? (feature/fix/docs/refactor/experiment)"
   - "Mô tả ngắn gọn feature này?"

2. Dựa trên câu trả lời, đề xuất tên branch theo format:
   - `feature/ten-feature` - Tính năng mới
   - `fix/ten-bug` - Sửa bug
   - `docs/ten-doc` - Cập nhật docs
   - `docs/ten-doc` - Cập nhật docs
   - `refactor/ten-module` - Refactor code
   - `experiment/ten-thu-nghiem` - Thử nghiệm tính năng mới

   Quy tắc naming:
   - Lowercase
   - Dùng dấu gạch ngang `-` thay space
   - Ngắn gọn, dễ hiểu (3-5 từ)

3. Xác nhận với user: "Đề xuất tên branch: `[tên]`. OK?"

## Bước 4: Tạo branch mới

// turbo
6. Sau khi user đồng ý, tạo branch:

```bash
git checkout -b [tên-branch-đã-chọn]
```

## Bước 5: Push lên remote

// turbo
7. Push branch lên GitHub:

```bash
git push -u origin [tên-branch-đã-chọn]
```

## Bước 6: Xác nhận hoàn thành

1. Thông báo cho user:
   - ✅ Branch `[tên]` đã tạo và push
   - ✅ Đã xóa N branch cũ (nếu có)
   - 🚀 Sẵn sàng bắt đầu code!
