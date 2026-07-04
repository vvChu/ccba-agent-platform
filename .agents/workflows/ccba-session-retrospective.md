---
name: ccba-session-retrospective
description: Tổng hợp kiến thức cuối phiên làm việc (Retrospective) & Phân phối dọn dẹp tài liệu đầu vào thô.
user-invocable: true
keywords: [retrospective, cleanup, tổng hợp, dọn dẹp]
---

# Session Knowledge Retrospective Workflow

Workflow này được chạy trước khi kết thúc phiên làm việc để tự động tổng hợp, đánh giá và lưu trữ các kiến thức có giá trị nhất đã phát hiện trong quá trình làm việc, đồng thời dọn dẹp tài liệu thô.

## Quy trình Thực hiện & Tiêu chí Hoàn thành

### Bước 1: Thu thập & Phân loại Kiến thức
Phân tích lịch sử hội thoại hiện tại để xác định:
*   **Vấn đề gốc:** Mục tiêu ban đầu của người dùng.
*   **Giải pháp thành công:** Giải pháp cuối cùng và tại sao nó hoạt động.
*   **Thất bại/Bài học:** Những phương án không hoạt động và lý do.
*   **Phân loại kiến thức:** Phân chia thành các nhóm: Patterns (Mẫu tốt), Anti-patterns (Cần tránh), Solutions (Giải pháp cụ thể), Configurations (Cấu hình tối ưu).

*   **Completion Criterion:** Các kiến thức được lọc ra phải mang tính thực tế, có khả năng tái sử dụng cao và không trùng lặp với tri thức đã có trên Hub.

---

### Bước 2: Cập nhật File Tri thức
Ghi nhận các kiến thức đã lọc vào tệp `knowledge/session_learnings.md` (lưu tại `.md/knowledge/session_learnings.md` cục bộ của dự án).

*   **Format Yêu cầu:**
    ```markdown
    ## Patterns (Mẫu tốt)
    ### [Tên Pattern]
    - **Ngữ cảnh:** Khi nào áp dụng
    - **Giải pháp:** Các bước thực hiện
    - **Nguồn:** Session [conversation-id], [date]

    ## Anti-patterns (Cách tránh)
    ### [Tên Anti-pattern]
    - **Vấn đề:** Tại sao không nên làm
    - **Thay thế bằng:** Pattern thay thế
    ```
*   **Completion Criterion:** File `session_learnings.md` được ghi nhận/cập nhật thành công, thông tin có cấu trúc và chứa đầy đủ ID phiên làm việc để truy nguyên.

---

### Bước 3: Đề xuất Memory & Workflow mới
*   **Cập nhật `user_global`:** Nếu có kiến thức đặc biệt quan trọng ảnh hưởng toàn cục, đề xuất người dùng thêm dòng ghi nhớ ngắn gọn (dưới 100 ký tự) vào tệp cấu hình global.
*   **Tiến hóa Kỹ năng (Skill Discovery):** Nếu phát hiện logic nghiệp vụ trong phiên có tính đóng gói cao, hỏi người dùng:
    > *"Tôi phát hiện logic `[tên logic]` có thể đóng gói thành skill/workflow tái sử dụng.*
    > *Bạn có muốn tôi ghi đề xuất này lên Hub ngay bây giờ không? Lệnh: `/ccba-propose-to-hub`"*

*   **Completion Criterion:** Đề xuất được hiển thị rõ ràng trên màn hình chat cho người dùng lựa chọn (không tự ý ghi đè global memory khi chưa hỏi).

---

### Bước 4: Dọn dẹp Workspace Tạm thời & Phân phối Tài liệu Đầu vào Thô
Agent thực hiện dọn dẹp các thư mục rác và phân phối tri thức đã sử dụng:

1.  **Dọn dẹp Workspace tạm của Subagents**:
    - Quét thư mục gốc `.agents/` để tìm các thư mục con của subagents được tạo ra trong quá trình chạy teamwork hoặc song song (bắt đầu bằng: `auditor_`, `challenger_`, `explorer_`, `reviewer_`, `worker_`, `teamwork_preview_`, `sub_orch_`, `victory_auditor_`, `temp-marketing`).
    - Thực hiện xóa vật lý toàn bộ các thư mục con tạm thời này (chỉ giữ lại các thư mục cấu hình cốt lõi như `skills/`, `workflows/`, `templates/` và tệp hiến pháp `AGENTS.md`).
2.  **Phân phối tài liệu đầu vào thô**:
    - Quét thư mục tạm `input_documents/` ở gốc dự án để phân phối tri thức đã sử dụng:
      *   Tài liệu pháp lý, quy định $\rightarrow$ `.md/legal_docs/` hoặc `.md/extracted_docs/`.
      *   Báo cáo phân tích kỹ thuật, sơ đồ, hướng dẫn $\rightarrow$ `.md/knowledge/`.
      *   Biên bản, ghi chú thảo luận họp $\rightarrow$ `.md/seminars/`.
      *   Tệp log, test script tạm $\rightarrow$ `.md/scratch/`.
3.  **In bảng đề xuất di chuyển**: Trình bày bảng đề xuất để người dùng xác nhận.
4.  **Thực thi di chuyển & Làm sạch**: Sau khi người dùng xác nhận, Agent di chuyển vật lý các tệp đã chốt vào đúng vị trí và xóa sạch các file rác còn lại trong `input_documents/`.

*   **Completion Criterion**: Thư mục `input_documents/` được dọn sạch hoàn toàn và các thư mục tạm thời của subagents trong `.agents/` được xóa bỏ triệt để.

---

### Bước 5: Xuất Báo cáo Tóm tắt
Đóng gói phiên làm việc bằng một báo cáo ngắn gọn xuất ra màn hình chat:

```markdown
## 📋 Session Retrospective Summary

### Phiên làm việc
- **Ngày:** [date]
- **Mục tiêu:** [objective]
- **Kết quả:** ✅ Thành công / ⚠️ Một phần / ❌ Chưa hoàn thành

### Dọn dẹp & Phân loại tài liệu
- [x] Đã phân loại và dọn dẹp N tài liệu từ `input_documents/` sang hệ thống tri thức `.md/`

### Kiến thức mới tích lũy
- [x] N patterns / anti-patterns mới
- [x] N solutions mới

### Đề xuất Kỹ năng mới (Hub Proposal)
- [ ] **[Tên Skill đề xuất]**: [Lý do/Lợi ích/Logic lõi]

### Việc cần làm tiếp theo
- [Các việc cần làm tiếp]

---
💡 *Nếu bạn muốn đóng và bàn giao phiên làm việc này ngay bây giờ, hãy chạy lệnh:* `/ccba-handoff`
```

*   **Completion Criterion:** Báo cáo được hiển thị đầy đủ, đính kèm các liên kết Markdown dẫn đến các tệp tri thức tương ứng vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
