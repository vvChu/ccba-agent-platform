---
name: ccba-build-skill
description: Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói sinh Skill mới đạt chuẩn CCBA.
user-invocable: true
keywords: [build-skill, create-skill, research, notebooklm]
disable-model-invocation: true
---
# Quy trình thực thi Slash Command `/ccba-build-skill`

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

1.  **Quét bảo mật & Nạp nguồn**:
    *   Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
    *   Chạy quét bảo mật qua `scripts/maskara.py` đối với các tệp tin cục bộ.
    *   Nạp nguồn vào Google NotebookLM thông qua CLI helper.
2.  **Chưng cất tri thức**:
    *   Chạy lệnh sinh `study-guide` hoặc `report` của CLI helper để kết xuất cẩm nang tri thức tổng hợp Markdown sạch vào `.md/knowledge/`.
    *   Đọc tệp tin cẩm nang này để nắm rõ toàn bộ logic, patterns và API của công cụ cần tạo skill.
3.  **Khởi tạo cấu trúc Skill đạt chuẩn**:
    *   Tạo thư mục skill tại `.agents/skills/<tên_skill_dạng_snake_case>/`.
    *   Tạo file `SKILL.md` chứa YAML Frontmatter chuẩn chỉnh và hướng dẫn chi tiết.
    *   Tạo các tệp tin script hỗ trợ (nếu có) vào thư mục `scripts/` tương ứng.
4.  **Đăng ký Slash Command**:
    *   Tạo một tệp tin workflow mỏng bắt đầu bằng `ccba-` tại `.agents/workflows/` (ví dụ: `ccba-<tên-lệnh>.md`) để đăng ký lệnh Slash Command chính thức của Skill.
5.  **Kiểm định chất lượng (QC Gate)**:
    *   Chạy công cụ `validate_docs.py` để kiểm định chất lượng tài liệu Markdown của Skill vừa tạo trước khi hoàn tất.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
