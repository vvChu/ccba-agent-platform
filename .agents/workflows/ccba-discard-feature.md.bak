---
description: Hủy bỏ branch hiện tại, xóa cả local và remote
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-discard-feature
triggers:
- discard
- hủy branch
- xóa branch
---
# Workflow: Discard Feature (Hủy bỏ Branch)

Quy trình xóa bỏ an toàn một branch thử nghiệm không sử dụng nữa.

## Bước 1: Xác nhận an toàn

1. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
2. Cảnh báo rõ ràng cho người dùng trước khi xóa vĩnh viễn và yêu cầu xác nhận (`yes/no`). Nếu từ chối, dừng thực hiện ngay lập tức.

## Bước 2: Quay về Main và Dọn dẹp

1. Chuyển ngữ cảnh về branch `main`:
   ```bash
   git checkout main
   ```
2. Xóa branch trên remote (nếu có):
   ```bash
   git push origin --delete [discard_branch]
   ```
   *(Nếu xảy ra lỗi do remote branch không tồn tại, bỏ qua và tiếp tục)*
3. Xóa branch cục bộ:
   ```bash
   git branch -D [discard_branch]
   ```

## Bước 3: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất:
   - 🗑️ Đã hủy bỏ branch thành công.
   - 🔙 Đã quay về branch `main` an toàn.
