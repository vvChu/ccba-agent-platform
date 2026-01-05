---
description: Hủy bỏ branch hiện tại, xóa cả local và remote
---

# Workflow: Discard Feature (Hủy bỏ Branch)

Khi user gọi `/discard-feature`, thực hiện các bước sau để xóa bỏ an toàn một branch thử nghiệm hoặc feature không dùng nữa.

## Bước 1: Xác nhận an toàn

1. Lấy tên branch hiện tại:

```bash
git branch --show-current
```

1. CẢNH BÁO user:
   "Bạn đang muốn XÓA VĨNH VIỄN branch `[current_branch]`.
   Hành động này sẽ:
   - Xóa branch ở local.
   - Xóa branch ở remote (nếu có).
   - Mất toàn bộ code chưa merge trong branch này.

   Bạn có chắc chắn muốn tiếp tục không? (yes/no)"

2. Nếu user trả lời "no" -> Dừng workflow.

## Bước 2: Cleanup Remote

// turbo
4. Xóa branch trên remote (nếu tồn tại):

```bash
git push origin --delete [current_branch]
```

*(Nếu lệnh lỗi do remote branch không tồn tại, bỏ qua và tiếp tục)*

## Bước 3: Cleanup Local

// turbo
5. Checkout về main:

```bash
git checkout main
```

// turbo
6. Force delete branch local:

```bash
git branch -D [current_branch]
```

## Bước 4: Thông báo hoàn tất

7. Báo cáo:
   - 🗑️ Đã hủy bỏ branch `[current_branch]`
   - 🔙 Đã quay về `main`
