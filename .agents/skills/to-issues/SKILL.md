---
name: to-issues
description: Phân rã bản thiết kế/PRD thành các ticket phát triển độc lập dạng lát cắt dọc.
disable-model-invocation: true
---

# Phân rã tính năng thành Ticket (To Issues)

Kỹ năng này giúp bẻ nhỏ một bản PRD hoặc tài liệu thiết kế thành các ticket phát triển độc lập theo nguyên tắc lát cắt dọc (Tracer-bullet vertical slices).

## Quy trình thực hiện (Process)

1. **Phân tích ngữ cảnh và thiết kế lát cắt dọc:**
   - Đọc kỹ PRD nguồn (từ Issue Tracker hoặc từ tệp cục bộ). Khảo sát cấu trúc codebase hiện tại để lên phương án phân rã.
   - Thiết kế các ticket dạng **lát cắt dọc (vertical slices)**: đi xuyên suốt từ Database, API, Business Logic, UI đến Test Suite để đảm bảo mỗi ticket sau khi làm xong đều có thể demo hoặc chạy kiểm thử độc lập.
   - **Tiêu chí hoàn thành:** Phác thảo xong danh sách các ticket dự kiến kèm tiêu đề, mối quan hệ phụ thuộc (blocked by) và user story tương ứng.

2. **Chốt danh sách với người dùng:**
   - Trình bày danh sách ticket dự kiến dưới dạng danh sách số và tham khảo ý kiến người dùng về độ mịn (granularity) và tính đúng đắn của các mối quan hệ phụ thuộc.
   - **Tiêu chí hoàn thành:** Nhận được sự đồng ý và phê duyệt của người dùng đối với cấu trúc phân rã.

3. **Xuất bản các ticket:**
   - Tạo các ticket trên Issue Tracker (theo thứ tự các ticket độc lập trước, ticket bị chặn sau để dễ gắn liên kết tham chiếu).
   - Nếu không sử dụng tracker, xuất các ticket thành các tệp Markdown cục bộ tương ứng trong thư mục `.md/knowledge/issues/{slug}.md` và đồng bộ vào file index của dự án.
   - **Tiêu chí hoàn thành:** Toàn bộ các ticket đã duyệt được đăng tải thành công (cục bộ hoặc lên GitHub Issues) với đầy đủ thông tin mô tả và tiêu chuẩn nghiệm thu (Acceptance criteria).

---

## Mẫu cấu trúc Ticket (Issue Template)

```markdown
## Parent (Ticket cha)

[Liên kết hoặc tham chiếu đến ticket cha/PRD gốc]

## What to build (Mô tả yêu cầu triển khai)

[Mô tả ngắn gọn và súc tích về hành vi end-to-end của lát cắt dọc này. Hạn chế ghi cụ thể file path hoặc code snippet để tránh bị lỗi thời nhanh, trừ khi là state machine hoặc type shape đặc biệt]

## Acceptance criteria (Tiêu chí nghiệm thu)

- [ ] Lớp dữ liệu (Database/Schema) đã cập nhật/migration thành công.
- [ ] Endpoint API đã được tạo/nâng cấp và hoạt động đúng đặc tả.
- [ ] Giao diện (UI) hiển thị đúng thiết kế và kết nối thành công với API.
- [ ] Bộ test tự động (Unit/Integration Tests) đã được bổ sung và chạy pass 100%.

## Blocked by (Mối quan hệ phụ thuộc)

- [Đường dẫn/Mã định danh của ticket chặn, hoặc ghi "None" nếu có thể bắt đầu ngay]
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
