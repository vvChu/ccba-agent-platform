---
proposal_id: "2026-06-29_docs-validator"
type: "skill"
name: "docs-validator"
status: "merged"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_date: "2026-06-29"
applies_to:
  - "Tất cả"
---

## Mô tả
Đề xuất tích hợp công cụ kiểm định tài liệu `validate_docs.py` thành một Skill chính thức cho CCBA Agent Services Platform để chống lỗi thời tài liệu và ảo ảnh (hallucinations) từ AI Agents.

## Vấn đề giải quyết
Trong quá trình phát triển và refactor hệ thống, tài liệu Markdown rất dễ bị lệch pha so với codebase thực tế (sai tên hàm/lớp, biến cấu hình môi trường bị thiếu trong `.env.example`, hoặc các liên kết tương đối bị hỏng). AI Agent khi làm việc ở các phiên làm việc sau sẽ đọc các tài liệu lỗi thời này dẫn tới hành vi sai lệch.

## Giải pháp / Cấu trúc đề xuất
Đóng gói script kiểm tra `validate_docs.py` thành một Skill có tên là `docs-validator` đăng ký trực tiếp trong `catalog.yaml`. AI Agent có thể gọi chạy để quét toàn bộ tài liệu trước khi thực hiện commit/PR.

## Nội dung mẫu / Code mẫu
Tệp tin `SKILL.md` của skill đã được tạo tại `.agents/skills/docs-validator/SKILL.md`.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
