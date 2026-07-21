# Ticket 3: [Cập nhật Hướng dẫn Định tuyến Routing trong platform-loader](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/document-skills-refinement/tickets/03-update-platform-loader-routing.md)

* **Thuộc bản đồ**: [Document Skills Refinement Map](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/document-skills-refinement/map.md)
* **Loại tác vụ**: Docs [AFK]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Blocked by Ticket 1, 2)

## 📋 Mục tiêu
Cập nhật quy tắc định tuyến (Routing Logic) trong `platform-loader/SKILL.md` để Agent tự động ưu tiên kích hoạt Master Skill trước khi điều phối Sub-skills.

## 🔍 Chi tiết công việc
- Đọc `.agents/skills/platform-loader/SKILL.md`.
- Thêm quy tắc: Khi người dùng yêu cầu xử lý tài liệu chung (Word, Excel, Markdown), Agent nạp Master Skill phù hợp (`xu-ly-van-phong` hoặc `markdown-document-processing`), tránh nạp trực tiếp sub-skill đơn lẻ (`docx` hay `table-reconstructor`) trừ khi người dùng yêu cầu thao tác vi mô.

## 📌 Đầu ra mong muốn
Tệp `platform-loader/SKILL.md` được cập nhật phần Routing Instructions.
