---
name: session_retrospective
description: Tự động tổng hợp tri thức cuối phiên làm việc (Retrospective) & Phân phối dọn dẹp tài liệu đầu vào thô.
disable-model-invocation: true
---

# Quy trình Tổng kết Phiên làm việc (Session Retrospective)

Kỹ năng này được kích hoạt để tự động thu thập, phân loại các kiến thức có giá trị và thực hiện dọn dẹp các tệp tin tạm trước khi kết thúc phiên.

## Các bước thực hiện

### Bước 1: Thu thập & Phân loại Kiến thức
Phân tích lịch sử hội thoại hiện tại để xác định:
- **Vấn đề gốc**: Mục tiêu ban đầu của người dùng.
- **Giải pháp thành công**: Giải pháp cuối cùng và tại sao nó hoạt động.
- **Thất bại/Bài học**: Những phương án không hoạt động và lý do.
- **Phân loại**: Sắp xếp vào các nhóm Patterns, Anti-patterns, Solutions, Configurations.
- **Tiêu chí hoàn thành:** Các kiến thức được lọc ra phải mang tính thực tế, có khả năng tái sử dụng cao và không trùng lặp với tri thức đã có trên Hub.

### Bước 2: Cập nhật File Tri thức
Ghi nhận các kiến thức đã lọc vào tệp `.md/knowledge/session_learnings.md`.
- **Tiêu chí hoàn thành:** Cập nhật thành công thông tin có cấu trúc kèm mã phiên làm việc (Conversation ID) để truy nguyên.

### Bước 3: Đề xuất Memory & Workflow mới
- Đề xuất cập nhật `user_global` nếu có kiến thức quan trọng ảnh hưởng toàn cục.
- Đề xuất tiến hóa kỹ năng (Skill Discovery) lên Hub thông qua lệnh `/ccba-propose-to-hub` nếu phát hiện logic đóng gói tốt.
- **Tiêu chí hoàn thành:** Đề xuất được hiển thị rõ ràng trên màn hình chat cho người dùng lựa chọn (không tự ý ghi đè global memory khi chưa hỏi).

### Bước 4: Dọn dẹp Workspace Tạm thời & Phân phối Tài liệu
1. **Dọn dẹp Workspace của Subagents**: Xóa vật lý các thư mục tạm bắt đầu bằng `teamwork_preview_`, `sub_orch_`, `temp-` bên trong thư mục `.agents/`.
2. **Phân phối tài liệu thô**: Di dời các tệp trong `input_documents/` về đúng thư mục chức năng thuộc `.md/` (pháp lý vào `legal_docs/`, scratch scripts vào `scratch/`...).
3. **Tiêu chí hoàn thành:** Thư mục `input_documents/` và các thư mục tạm của subagents được dọn sạch hoàn toàn sau khi người dùng xác nhận bảng đề xuất di chuyển.

### Bước 5: Xuất Báo cáo Tóm tắt
Xuất báo cáo tổng kết ngắn gọn (theo mẫu `## 📋 Session Retrospective Summary`) ra màn hình chat.
- **Tiêu chí hoàn thành:** Báo cáo được hiển thị đầy đủ kèm các liên kết Markdown dẫn đến các tệp tri thức tương ứng vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
