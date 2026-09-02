# Ticket T01: Đóng gói Shell Aliases & Terminal Helpers cho `agy` và `gh copilot`

* **Loại Ticket:** `Prototype [HITL]`
* **Assignee:** Unassigned
* **Trạng thái:** 🟢 Ready
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](../map.md)

---

## 🎯 Câu Hỏi Cần Làm Rõ / Mục Tiêu
Làm thế nào để kỹ sư CCBA có thể gõ các lệnh tắt trực tiếp trong PowerShell (ví dụ: `??` để hỏi lệnh shell, `ai-commit` để tự động tạo commit message, `ai-review` để review code diff) mà không cần gõ câu lệnh dài dòng?

---

## 📋 Đề Xuất Kịch Bản Triển Khai
1. Tạo file cấu hình mẫu PowerShell profile `scripts/shell/ccba_dev_aliases.ps1`:
   - `?? <prompt>` $\rightarrow$ Gọi `gh copilot suggest`
   - `ai-commit` $\rightarrow$ `git diff --cached | agy -p "Generate concise conventional commit message..." | git commit -F -`
   - `ai-review` $\rightarrow$ `git diff HEAD~1 | agy -p "Review this git diff against AGENTS.md rules..."`
   - `ai-chat <prompt>` $\rightarrow$ `agy -p $args`
2. Hướng dẫn nạp vào `$PROFILE` của PowerShell.

---

## 🏁 Tiêu Chí Hoàn Thành (Definition of Done)
- [ ] File `scripts/shell/ccba_dev_aliases.ps1` được tạo và kiểm thử thành công.
- [ ] Tài liệu hướng dẫn sử dụng được ghi nhận vào ticket.
