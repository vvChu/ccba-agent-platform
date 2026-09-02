# Ticket T04: Thử nghiệm MCP Server Chaining từ Antigravity CLI

* **Loại Ticket:** `Prototype [HITL]`
* **Assignee:** Unassigned
* **Trạng thái:** 🟢 Ready
* **Bản đồ trực thuộc:** [Hệ Sinh Thái CLI & Tự Động Hoá Agentic](file:///d:/GitHubProjects/ccba-agent-platform/.md/wayfinder/cli-and-agent-automation-ecosystem/map.md)

---

## 🎯 Câu Hỏi Cần Làm Rõ / Mục Tiêu
Làm thế nào để kết nối và gọi các MCP Tools (PostgreSQL, BigQuery, Playwright Browser, GitHub Tracker) trực tiếp từ dòng lệnh `agy -p "..."` phục vụ việc debug và kiểm thử tự động?

---

## 📋 Đề Xuất Kịch Bản Triển Khai
1. Kiểm tra cấu hình MCP Servers trong `~/.gemini/antigravity/mcp/`.
2. Kiểm thử câu lệnh: `agy -p "List files in directory using filesystem MCP..."`.
3. Ghi nhận playbook hướng dẫn lập trình viên sử dụng MCP từ dòng lệnh vào `docs/playbooks/mcp_cli_guide.md`.

---

## 🏁 Tiêu Chí Hoàn Thành (Definition of Done)
- [ ] Xác nhận `agy mcp list` hiển thị đầy đủ MCP servers khả dụng.
- [ ] Ghi nhận playbook hướng dẫn sử dụng MCP trên CLI.
