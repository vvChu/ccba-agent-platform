# Ticket T01: Đóng gói Shell Aliases & Terminal Helpers cho `agy` và `gh copilot`

* **Loại Ticket:** `Prototype [HITL]`
* **Assignee:** Unassigned
* **Trạng thái:** 🟢 Completed
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](../map.md)
* **File triển khai:** [`scripts/shell/ccba_aliases.ps1`](../../../../scripts/shell/ccba_aliases.ps1)

---

## 🎯 Câu Hỏi Cần Làm Rõ / Mục Tiêu
Làm thế nào để kỹ sư CCBA có thể gõ các lệnh tắt trực tiếp trong PowerShell (`??` tra cứu lệnh shell, `ai-commit` tự động tạo commit message <1.2s, `ai-review` review code diff, `ai-explain` giải thích lỗi) mà không cần gõ câu lệnh dài dòng và không bị delay?

---

## 📋 Đã Triển Khai Thực Tế (Lean Architecture)
Đã đóng gói file tiện ích [`scripts/shell/ccba_aliases.ps1`](../../../../scripts/shell/ccba_aliases.ps1):
1. `?? <prompt>` $\rightarrow$ Gọi `copilot -p` để tra cứu lệnh shell siêu tốc.
2. `ai-commit` $\rightarrow$ Đọc `git diff --cached` và gọi `ccba-ai` SDK sinh Conventional Commit trong **~1.2s**.
3. `ai-review` $\rightarrow$ Đọc diff so với `origin/main` và gọi `ccba-ai` audit bảo mật / KISS.
4. `ai-explain <cmd/log>` $\rightarrow$ Gọi `copilot explain` phân tích lỗi terminal tức thì.

### Hướng dẫn nạp vào PowerShell Profile:
Thêm dòng sau vào `$PROFILE`:
```powershell
. "D:\GitHubProjects\ccba-agent-platform\scripts\shell\ccba_aliases.ps1"
```

---

## 🏁 Tiêu Chí Hoàn Thành (Definition of Done)
- [x] File `scripts/shell/ccba_aliases.ps1` được tạo và kiểm thử thành công.
- [x] Đã áp dụng `ccba-ai` direct call để đạt tốc độ <1.5s (thay vì 40s của agy).
- [x] Tài liệu hướng dẫn sử dụng được ghi nhận vào ticket.
