# Ticket #02: [Tự động suy luận Monorepo để chốt Single/Multi-Context](02-monorepo-inference.md)

- **Mã số**: `02-monorepo-inference`
- **Loại Ticket**: `Task [AFK]`
- **Trạng thái**: Open (Unblocked)
- **Assignee**: Unassigned

## Mô tả Task

Bổ sung thuật toán trinh sát quét các tín hiệu đặc trưng của Monorepo (`pnpm-workspace.yaml`, `workspaces` trong `package.json`, `CONTEXT-MAP.md`). Nếu không thấy tín hiệu Monorepo ➔ Tự động chốt `single-context` mà không làm phiền người dùng.

## Tiêu chí Hoàn thành

- [ ] Kỹ năng `ccba-setup-skills` không bắt chọn Single/Multi-context đối với 95% dự án đơn vị thông thường.
- [ ] Tự động ghi nhận `single-context` vào file chỉ dẫn domain mà không dừng lại phỏng vấn.
