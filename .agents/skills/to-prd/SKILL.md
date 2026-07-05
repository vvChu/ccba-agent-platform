---
name: to-prd
description: Chuyển đổi ngữ cảnh thảo luận hiện tại thành tài liệu Yêu cầu Sản phẩm (PRD) chính quy.
disable-model-invocation: true
---

# Soạn thảo Yêu cầu Sản phẩm (PRD)

Kỹ năng này giúp tổng hợp toàn bộ thông tin thảo luận và ngữ cảnh hiện tại thành một tài liệu PRD hoàn chỉnh mà không cần phỏng vấn lại người dùng.

## Quy trình thực hiện (Process)

1. **Khảo sát hệ thống và thiết lập Seams kiểm thử:**
   - Quét qua codebase để nắm bắt cấu trúc hiện tại và xác định các điểm seams (điểm phân tách logic) tối ưu cho việc viết test. Ưu tiên tái sử dụng các seams sẵn có hơn là tạo mới.
   - **Tiêu chí hoàn thành:** Xác định được các module bị ảnh hưởng và đề xuất được ít nhất một seam kiểm thử rõ ràng để người dùng phản hồi.

2. **Soạn thảo và phát hành PRD:**
   - Biên soạn PRD theo cấu trúc chuẩn. Nếu kho lưu trữ hỗ trợ Issue Tracker và có cấu hình, đăng tải PRD lên đó với nhãn `ready-for-agent`.
   - Nếu không dùng Tracker, tiến hành xuất tài liệu trực tiếp thành file Markdown cục bộ lưu tại `.md/knowledge/prd-{feature_name}.md`.
   - **Tiêu chí hoàn thành:** Tài liệu PRD được tạo thành công (cục bộ hoặc trên Issue Tracker) chứa đầy đủ các phân mục chuẩn (Problem Statement, Solution, User Stories, Implementation & Testing Decisions, Out of Scope).

---

## Cấu trúc chuẩn của PRD (Template)

```markdown
## Problem Statement (Mô tả bài toán)

[Mô tả vấn đề từ góc nhìn của người dùng]

## Solution (Giải pháp)

[Đề xuất giải pháp giải quyết bài toán]

## User Stories (Các câu chuyện người dùng)

[Danh sách chi tiết các câu chuyện theo mẫu: "Là <vai trò>, tôi muốn <tính năng>, để <giá trị>"]

## Implementation Decisions (Quyết định triển khai)

- Các module được tạo mới/sửa đổi
- Các giao diện lập trình (interface) bị ảnh hưởng
- Thay đổi cấu trúc cơ sở dữ liệu (schema) hoặc API contract (nếu có)
- Tránh đưa file path cụ thể hoặc code snippet trừ khi là mã máy trạng thái (state machine) / schema cốt lõi từ prototype.

## Testing Decisions (Quyết định kiểm thử)

- Mô tả hành vi bên ngoài cần test (black-box) thay vì kiểm thử chi tiết private implementation
- Liệt kê các module sẽ được viết test và các mã nguồn test mẫu hiện có để tham chiếu.

## Out of Scope (Phạm vi loại trừ)

[Những phần tính năng không thực hiện trong PRD này]
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
