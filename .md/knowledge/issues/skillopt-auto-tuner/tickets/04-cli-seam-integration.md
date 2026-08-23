# Ticket 4: [Tích hợp CLI Flag --auto-tune vào ccba-skills-eval](04-cli-seam-integration.md)

* **Thuộc bản đồ**: [CCBA Skill Auto-Tuner Map](../map.md)
* **Loại tác vụ**: Task [HITL]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Blocked by Ticket 1, 2, 3)

## 📋 Mục tiêu
Tích hợp toàn bộ 3 thành phần (Optimizer Prompt, Synthetic Task Generator, Validation Gate) vào workflow `/ccba-skills-eval` dưới dạng cờ `--auto-tune`.

## 🔍 Chi tiết phân tích
- Cập nhật workflow spec tại `.agents/workflows/ccba-skills-eval.md`.
- Mở rộng script thực thi `eval-gate` để xử lý cờ `--auto-tune`.
- Xuất báo cáo diff hiển thị các chỉnh sửa trong `SKILL.md` sau khi tuning thành công.

## 📌 Đầu ra mong muốn
Mã nguồn triển khai hoàn chỉnh cho workflow `/ccba-skills-eval --auto-tune`.
