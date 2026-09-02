# Ticket T03: Thiết lập Autonomous Docs & Deadlink Maintenance Daemon

* **Loại Ticket:** `Task [AFK]`
* **Assignee:** Unassigned
* **Trạng thái:** 🟢 Ready
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](file:///d:/GitHubProjects/ccba-agent-platform/.md/wayfinder/cli-and-agent-automation-ecosystem/map.md)

---

## 🎯 Câu Hỏi Cần Làm Rõ / Mục Tiêu
Làm thế nào để thiết lập một cron script/task scheduler tự động chạy ngầm hàng ngày sử dụng `agy --dangerously-skip-permissions` để quét tài liệu Markdown out-of-date, kiểm tra broken links, và tự động tạo Pull Request bảo trì định kỳ?

---

## 📋 Đề Xuất Kịch Bản Triển Khai
1. Xây dựng kịch bản `scripts/cron/run_daily_repo_maintenance.ps1`:
   - Kiểm tra `validate_docs.py` và `validate_cross_references.py`.
   - Sử dụng `agy -p "Review and align docs with new package exports..."`.
   - Nếu có file thay đổi: tự tạo branch `chore/auto-docs-sync-<date>` và tạo PR bằng `gh pr create`.
2. Hướng dẫn cấu hình Windows Task Scheduler hoặc cron job.

---

## 🏁 Tiêu Chí Hoàn Thành (Definition of Done)
- [ ] Kịch bản `run_daily_repo_maintenance.ps1` hoàn thiện.
- [ ] Kiểm thử chạy dry-run thành công.
