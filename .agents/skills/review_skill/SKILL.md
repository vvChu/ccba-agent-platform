---
name: review_skill
description: Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết skill của CCBA.
disable-model-invocation: true
---

# Kỹ năng Rà soát và Tối ưu hóa Skill (Review Skill)

Kỹ năng này thực hiện quy trình đánh giá tĩnh (static) và ngữ nghĩa (semantic) của một tệp tin `SKILL.md` để đảm bảo tính khả đoán (predictability), độ súc tích (pruning) và tuân thủ các quy tắc chất lượng của CCBA.

---

## Quy trình Thực hiện (Process)

1.  **Thu thập và phân tích tài liệu đầu vào:**
    - Sử dụng `view_file` để đọc tệp tin `SKILL.md` cần đánh giá.
    - Sử dụng `view_file` để nạp cẩm nang chất lượng kỹ năng tại [writing-great-skills](../writing-great-skills/SKILL.md).
    - **Tiêu chí hoàn thành:** Nội dung của cả tệp tin đích và cẩm nang chuẩn được nạp đầy đủ vào ngữ cảnh Agent.

2.  **Đánh giá linter và cấu trúc (Linter & Structure Check):**
    - Kiểm tra độ dài mô tả `description` trong frontmatter (bắt buộc dưới **180 ký tự**).
    - Kiểm tra xem mọi bước hướng dẫn trong các phần quy trình (dưới tiêu đề `Process` hoặc `Quy trình`) có chứa dòng `Tiêu chí hoàn thành:` hoặc `Completion Criterion:` hay chưa.
    - Kiểm tra tính hợp lệ của các liên kết tương đối (relative links), phát hiện các đường dẫn tuyệt đối hoặc link hỏng.
    - **Tiêu chí hoàn thành:** Lập danh sách cụ thể các điểm vi phạm quy chuẩn linter tĩnh kèm vị trí dòng.

3.  **Rà soát chất lượng ngữ nghĩa (Semantic Audit Check):**
    - **Premature completion:** Rà soát xem các tiêu chí hoàn thành đã đủ rõ ràng, kiểm chứng được chưa.
    - **Duplication:** Tìm kiếm các đoạn trùng lặp ý hoặc cấu trúc viết lại.
    - **Sprawl:** Đánh giá xem tài liệu có quá phình to không; nếu có, chỉ rõ phần tham chiếu cần tách ra tệp sibling (áp dụng Progressive Disclosure).
    - **No-op:** Phát hiện các câu hướng dẫn sáo rỗng hoặc vô nghĩa mà mô hình mặc định đã biết làm.
    - **Tiêu chí hoàn thành:** Đưa ra đánh giá chi tiết cho từng lỗi ngữ nghĩa được phát hiện kèm theo lý do cụ thể.

4.  **Đề xuất bản vá tối ưu hóa (Optimization Patch):**
    - Tạo bản dự thảo chỉnh sửa (draft patch) tối ưu hóa tệp tin `SKILL.md` sau khi đã cắt tỉa (pruning) sạch sẽ các lỗi đã chỉ ra.
    - **Tiêu chí hoàn thành:** Sinh ra nội dung file `SKILL.md` hoàn chỉnh mới sạch lỗi, sẵn sàng để ghi đè.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
