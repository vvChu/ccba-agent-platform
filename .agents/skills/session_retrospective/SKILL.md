---
name: session_retrospective
description: Tự động tổng hợp tri thức cuối phiên làm việc (Retrospective) & Phân phối dọn dẹp tài liệu đầu vào thô.
disable-model-invocation: true
---

# Quy trình Tổng kết Phiên làm việc (Session Retrospective)

Kỹ năng này được kích hoạt để tự động thu thập, phân loại các kiến thức có giá trị và thực hiện dọn dẹp các tệp tin tạm trước khi kết thúc phiên.

## Quy trình thực hiện (Process)

1. **Thu thập & Phân loại Kiến thức:**
   - Sử dụng `view_file` để đọc tệp [.md/knowledge/session_learnings.md](../../../.md/knowledge/session_learnings.md) hiện tại nhằm có cơ sở đối chiếu và chống trùng lặp.
   - Phân tích lịch sử hội thoại hiện tại để xác định:
     * **Vấn đề gốc**: Mục tiêu ban đầu của người dùng.
     * **Giải pháp thành công**: Giải pháp cuối cùng và tại sao nó hoạt động.
     * **Thất bại/Bài học**: Những phương án không hoạt động và lý do.
     * **Phân loại**: Sắp xếp vào các nhóm Patterns, Anti-patterns, Solutions, Configurations.
   - **Tiêu chí hoàn thành:** Các kiến thức được lọc ra phải mang tính thực tế, có khả năng tái sử dụng cao, và không trùng lặp với bất kỳ tri thức nào đã được lưu trữ trước đó.

2. **Cập nhật File Tri thức:**
   - Ghi nhận các kiến thức mới đã lọc vào tệp [.md/knowledge/session_learnings.md](../../../.md/knowledge/session_learnings.md).
   - **Tiêu chí hoàn thành:** Cập nhật thành công thông tin có cấu trúc kèm mã phiên làm việc (Conversation ID) để truy nguyên nguồn gốc.

3. **Đề xuất Memory & Workflow mới:**
   - Đề xuất cập nhật `user_global` nếu có kiến thức quan trọng ảnh hưởng toàn cục.
   - Đề xuất tiến hóa kỹ năng (Skill Discovery) lên Hub thông qua lệnh `/ccba-propose-to-hub` nếu phát hiện logic đóng gói tốt (chỉ áp dụng khi đang làm việc tại dự án Spoke, bỏ qua nếu đang đứng tại Hub).
   - **Tiêu chí hoàn thành:** Đề xuất được hiển thị rõ ràng trên màn hình chat cho người dùng lựa chọn (không tự ý ghi đè global memory khi chưa hỏi).

4. **Tự động hóa dọn dẹp Workspace & Phân phối Tài liệu (Quy trình 2 Bước):**
   - **Bước 1 (Xem trước):** Chạy công cụ ở chế độ mặc định (dry-run preview) để liệt kê các thay đổi dự kiến:
     ```bash
     python scripts/session_cleanup.py
     ```
     Hiển thị danh sách các worktree/branch sẽ xóa và ma trận di chuyển tệp thô từ [input_documents/](../../../input_documents/) vào cửa sổ chat để hỏi ý kiến xác nhận của người dùng.
   - **Bước 2 (Thực thi):** Chỉ sau khi người dùng phê duyệt tường minh, tiến hành thực thi dọn dẹp thực tế bằng lệnh:
     ```bash
     python scripts/session_cleanup.py --execute
     ```
   - **Tiêu chí hoàn thành:** Báo cáo xem trước được hiển thị, nhận được sự đồng ý của người dùng, thực thi lệnh với `--execute` thành công và trả workspace về trạng thái sạch sẽ.

5. **Xuất Báo cáo Tóm tắt:**
   - Xuất báo cáo tổng kết ngắn gọn (theo mẫu `## 📋 Session Retrospective Summary`) ra màn hình chat.
   - **Tiêu chí hoàn thành:** Báo cáo được hiển thị đầy đủ kèm các liên kết Markdown dẫn đến các tệp tri thức tương ứng vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
