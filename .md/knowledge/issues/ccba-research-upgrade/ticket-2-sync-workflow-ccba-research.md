# Ticket 2: Sync Workflow ccba-research (`ticket-2-sync-workflow-ccba-research`)

> **Map:** [`[Bản đồ Wayfinder ccba-research-upgrade]`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/ccba-research-upgrade/map.md)  
> **Loại Ticket:** Task [AFK]  
> **Trạng thái:** Đã đóng (Closed)  
> **Assignee:** Agent (Antigravity)  

---

## ❓ Câu hỏi / Tác vụ (Question / Task)

Đồng bộ tệp workflow [`d:\GitHubProjects\ccba-agent-platform\.agents\workflows\ccba-research.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/ccba-research.md):

1. Cập nhật mô tả và trigger của workflow để đảm bảo khớp với các cải tiến mới của `ccba-research` (Search Budget Cap 5 tool calls, Template 5 phần, Cross-reference & Dynamic storage).
2. Kiểm tra frontmatter và completion criteria của workflow file.

---

## 📋 Kết quả Thực hiện (Resolution)

- Đã đồng bộ tệp `ccba-research.md` trong `.agents/workflows/` khớp với `SKILL.md`.
- Đã chạy kiểm định thành công.

---

## 📋 Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tệp `ccba-research.md` trong `.agents/workflows/` được đồng bộ với `SKILL.md`.
- [x] Chạy `python scripts/validate_skills.py` (hoặc doc auditor) xác nhận không có lỗi.
