---
name: ccba-review-skill
description: Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết skill của CCBA.
user-invocable: true
keywords: [review-skill, audit-skill, skill-quality, writing-great-skills]
---

# Quy trình thực thi Slash Command `/ccba-review-skill`

Khi người dùng kích hoạt lệnh dưới dạng:
`/ccba-review-skill <đường-dẫn-file-skill-cần-review>`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

1.  **Nạp cẩm nang tiêu chuẩn**:
    *   Tự động nạp tệp hướng dẫn viết skill tại [writing-great-skills](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/writing-great-skills/SKILL.md) vào ngữ cảnh.
2.  **Đọc tệp tin cần đánh giá**:
    *   Đọc nội dung của tệp tin `SKILL.md` được chỉ định tại `<đường-dẫn-file-skill-cần-review>`.
3.  **Tiến hành Audit chất lượng**:
    *   Đối chiếu tệp tin cần đánh giá với các nguyên tắc trong cẩm nang `writing-great-skills`.
    *   Chỉ ra cụ thể các lỗi (nếu có) bao gồm:
        *   **Premature completion** (Tiêu chí hoàn thành chưa rõ ràng/fuzzy).
        *   **Duplication** (Nội dung trùng lặp hoặc viết lại nhiều lần).
        *   **Sprawl** (Tài liệu quá dài dòng, chưa phân tầng Progressive Disclosure).
        *   **No-op** (Các câu chỉ dẫn thừa thãi mà Agent mặc định đã biết làm).
4.  **Đề xuất bản vá tối ưu**:
    *   Xuất bản nháp đề xuất cải tiến tệp tin `SKILL.md` đã được tối giản và cắt tỉa (pruned) sạch sẽ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
