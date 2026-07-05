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

### Bước 4: Dọn dẹp Workspace Tạm thời & Phân phối Tài liệu Đầu vào Thô
Agent thực hiện dọn dẹp các thư mục rác và phân phối tri thức đã sử dụng:

1. **Dọn dẹp Workspace tạm của Subagents**:
   - Quét thư mục gốc `.agents/` để tìm các thư mục con của subagents được tạo ra trong quá trình chạy teamwork hoặc song song (bắt đầu bằng: `auditor_`, `challenger_`, `explorer_`, `reviewer_`, `worker_`, `teamwork_preview_`, `sub_orch_`, `victory_auditor_`, `temp-marketing`).
   - Thực hiện xóa vật lý toàn bộ các thư mục con tạm thời này (chỉ giữ lại các thư mục cấu hình cốt lõi như `skills/`, `workflows/`, `templates/` và tệp hiến pháp `AGENTS.md`).
2. **Phân phối tài liệu đầu vào thô**:
   - Quét thư mục tạm `input_documents/` ở gốc dự án để phân phối tri thức đã sử dụng:
     * Tài liệu pháp lý, quy định $\rightarrow$ `.md/legal_docs/` hoặc `.md/extracted_docs/`.
     * Báo cáo phân tích kỹ thuật, sơ đồ, hướng dẫn $\rightarrow$ `.md/knowledge/`.
     * Biên bản, ghi chú thảo luận họp $\rightarrow$ `.md/seminars/`.
     * Tệp log, test script tạm $\rightarrow$ `.md/scratch/`.
3. **In bảng đề xuất di chuyển**: Trình bày bảng đề xuất để người dùng xác nhận.
4. **Thực thi di chuyển & Làm sạch**: Sau khi người dùng xác nhận, Agent di chuyển vật lý các tệp đã chốt vào đúng vị trí và xóa sạch các file rác còn lại trong `input_documents/`.
- **Tiêu chí hoàn thành:** Thư mục `input_documents/` được dọn sạch hoàn toàn và các thư mục tạm thời của subagents trong `.agents/` được xóa bỏ triệt để sau khi người dùng xác nhận bảng đề xuất.

### Bước 5: Xuất Báo cáo Tóm tắt
Xuất báo cáo tổng kết ngắn gọn (theo mẫu `## 📋 Session Retrospective Summary`) ra màn hình chat.
- **Tiêu chí hoàn thành:** Báo cáo được hiển thị đầy đủ kèm các liên kết Markdown dẫn đến các tệp tri thức tương ứng vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
