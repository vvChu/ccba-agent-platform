# Ticket #01: [Tự động bỏ câu hỏi Triage khi thiếu Skill Triage](01-smart-skipping-triage.md)

- **Mã số**: `01-smart-skipping-triage`
- **Loại Ticket**: `Research [AFK]`
- **Trạng thái**: Open (Unblocked)
- **Assignee**: Unassigned

## Mô tả Task

Bổ sung bước trinh sát kiểm tra sự tồn tại của kỹ năng `/ccba-triage` trong catalog hoặc thư mục `.agents/skills/`. Nếu phát hiện repo/Spoke không cài đặt hoặc sử dụng triage, tự động bỏ qua toàn bộ phần phỏng vấn Triage Label Vocabulary trong `/ccba-setup-skills`.

## Tiêu chí Hoàn thành

- [ ] `ccba-setup-skills/SKILL.md` có bổ sung điều kiện kiểm tra sự tồn tại của skill `triage` trước khi phỏng vấn Triage.
- [ ] Giảm 1 câu hỏi phỏng vấn cho các Spoke đơn giản không cần triage.
