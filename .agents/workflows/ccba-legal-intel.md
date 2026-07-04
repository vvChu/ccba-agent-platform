---
description: Khởi động quy trình tự động cào, đóng gói và tích hợp văn bản pháp luật mới từ Thư viện Pháp luật (TVPL)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_consulting"
---

# Workflow: Legal Intelligence Crawler (/ccba-legal-intel)

Khi người dùng kích hoạt lệnh dưới dạng:
`/ccba-legal-intel <URL>`

Agent tiếp nhận bắt buộc phải nạp và thực thi kỹ năng `ccba-legal-intel` tại [SKILL.md](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-legal-intel/SKILL.md) để bắt đầu quy trình kiểm tra cổng Chrome CDP, thực thi cào dữ liệu, phân tách phụ lục, sửa liên kết tương đối và đăng ký văn bản mới vào Registry hệ thống.
