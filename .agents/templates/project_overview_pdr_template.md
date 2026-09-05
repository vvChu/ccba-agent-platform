# Product Development Requirements (PDR): [Tên Dự Án]

Tài liệu này định nghĩa các yêu cầu phát triển và tổng quan kiến trúc của dự án con (Spoke) **[Tên Dự Án]**.

---

## 1. Tổng quan Dự án (Project Overview)
- **Mô tả ngắn gọn**: [Mô tả mục đích và vai trò của dự án trong 2-3 câu]
- **Milestone hiện tại**: [Ví dụ: A0 - Thiết kế cơ sở / A1 - Phối hợp chi tiết]
- **Kiến trúc chính**: [Ví dụ: Next.js + Tailwind CSS / Python FastAPI + PostgreSQL]

---

## 2. Đánh giá Khả năng Tái sử dụng (Reuse Assessment)

> [!IMPORTANT]
> **Quy định bắt buộc theo Layer 1 Constitution:**
> Agent bắt buộc phải rà quét Hub catalog (`platform-loader/catalog.yaml`) trước khi phát triển tính năng mới để tối đa hóa khả năng kế thừa.

- **Trạng thái tra cứu Hub catalog**: [Ghi nhận danh sách các tools/workflows/skills tương tự đã tồn tại trên Hub]
- **Đánh giá Cost-Benefit**:
  - *Tại sao kế thừa*: [Nêu các thành phần Hub sẽ được tái sử dụng trực tiếp để giảm thiểu dependencies]
  - *Tại sao viết mới (nếu có)*: [Nêu rõ sự khác biệt nghiệp vụ đặc thù bắt buộc phải viết code mới]

---

## 3. Yêu cầu Tính năng (Functional Requirements)
- **[Yêu cầu 1]**:
  - Mô tả: ...
  - Tiêu chí nghiệm thu (Acceptance Criteria): ...
- **[Yêu cầu 2]**:
  - Mô tả: ...
  - Tiêu chí nghiệm thu: ...

---

## 4. Ràng buộc Kỹ thuật & Bảo mật (Non-Functional Constraints)
- **Hiệu suất**: Giới hạn thời gian phản hồi API hoặc thời gian xử lý.
- **Bảo mật**: Tuyệt đối không hardcode credentials, bắt buộc quét bảo mật qua `maskara-privacy`.
- **Kích thước Tài liệu**: Giới hạn tối đa 800 LOC cho mỗi tệp tài liệu tĩnh, tự động phân rã nếu vượt quá.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
