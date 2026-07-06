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
   - Đề xuất tiến hóa kỹ năng (Skill Discovery) lên Hub thông qua lệnh `/ccba-propose-to-hub` nếu phát hiện logic đóng gói tốt.
   - **Tiêu chí hoàn thành:** Đề xuất được hiển thị rõ ràng trên màn hình chat cho người dùng lựa chọn (không tự ý ghi đè global memory khi chưa hỏi).

4. **Dọn dẹp Workspace Tạm thời & Phân phối Tài liệu Đầu vào Thô:**
   Agent thực hiện dọn dẹp các thư mục rác và phân phối tri thức đã sử dụng theo các bước con sau:
   - **Dọn dẹp Workspace tạm của Subagents**: Quét thư mục gốc `.agents/` để tìm các thư mục con của subagents được tạo ra trong quá trình chạy teamwork hoặc song song (bắt đầu bằng: `auditor_`, `challenger_`, `explorer_`, `reviewer_`, `worker_`, `teamwork_preview_`, `sub_orch_`, `victory_auditor_`, `temp-marketing`) và xóa vật lý toàn bộ các thư mục con tạm thời này (chỉ giữ lại các thư mục cấu hình cốt lõi như `skills/`, `workflows/`, `templates/` và tệp hiến pháp `AGENTS.md`).
   - **Phân phối tài liệu đầu vào thô**: Quét thư mục tạm [input_documents/](../../../input_documents/) ở gốc dự án để phân phối tri thức đã sử dụng:
     * Tài liệu pháp lý, quy định $\rightarrow$ [.md/legal_docs/](../../../.md/legal_docs/) hoặc [.md/extracted_docs/](../../../.md/extracted_docs/).
     * Báo cáo phân tích kỹ thuật, sơ đồ, hướng dẫn $\rightarrow$ [.md/knowledge/](../../../.md/knowledge/).
     * Biên bản, ghi chú thảo luận họp $\rightarrow$ [.md/seminars/](../../../.md/seminars/).
     * Tệp log, test script tạm $\rightarrow$ [.md/scratch/](../../../.md/scratch/).
   - **In bảng đề xuất di chuyển**: Trình bày bảng đề xuất Move Matrix rõ ràng trong cửa sổ chat để người dùng xác nhận.
   - **Thực thi di chuyển & Làm sạch**: Sau khi được người dùng duyệt phê duyệt tường minh, tiến hành di chuyển vật lý các tệp đã chốt vào đúng vị trí và xóa sạch các file rác còn lại trong [input_documents/](../../../input_documents/).
   - **Tiêu chí hoàn thành:** Bảng đề xuất di chuyển được hiển thị thành công, nhận được xác nhận duyệt của người dùng trước khi tiến hành xóa, và cuối cùng thư mục [input_documents/](../../../input_documents/) cùng các thư mục tạm subagents được làm sạch triệt để.

5. **Xuất Báo cáo Tóm tắt:**
   - Xuất báo cáo tổng kết ngắn gọn (theo mẫu `## 📋 Session Retrospective Summary`) ra màn hình chat.
   - **Tiêu chí hoàn thành:** Báo cáo được hiển thị đầy đủ kèm các liên kết Markdown dẫn đến các tệp tri thức tương ứng vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
