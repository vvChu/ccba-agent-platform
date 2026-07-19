---
description: Khởi động phiên thảo luận ý tưởng và chuẩn bị tài liệu đầu vào tại input_documents/
command: /ccba-brainstorm [-- <topic_id>]
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# CCBA Brainstorming & Ingestion Workflow

Workflow này giúp khởi chạy một phiên thảo luận ý tưởng, tự động quét và phân loại tài liệu đầu vào tại thư mục nháp `input_documents/`, đồng thời kích hoạt các hướng dẫn phân tích đặc thù theo từng chủ đề nghiệp vụ.

## Các bước thực hiện của Agent

### 1. Đọc cấu hình và Xử lý tham số (Config & Routing)
Agent bắt buộc phải đọc và gộp cấu hình các chủ đề từ hai nguồn:
1. **Mặc định từ Hub:** Đọc cấu hình mặc định tại [brainstorm_topics.yaml](resources/brainstorm_topics.yaml).
2. **Cục bộ từ Spoke:** Kiểm tra sự tồn tại của tệp cấu hình cục bộ tại `.md/knowledge/brainstorm_topics.yaml`. Nếu có, đọc và gộp (merge) với cấu hình mặc định (tập tin cục bộ được phép ghi đè các chủ đề trùng `topic_id` hoặc khai báo thêm chủ đề mới).

**Xử lý tham số Bypass:** Agent phân tích câu lệnh kích hoạt để phát hiện tham số truyền sau ký tự `--`:
* **Nếu có tham số trùng khớp `topic_id`:** Bypass — lập tức di chuyển sang **Bước 3** để nạp Kỹ năng và chuyển đổi tài liệu, bỏ qua Bước 2 (Quét) và Menu chọn.
* **Nếu tham số không trùng khớp:** In cảnh báo `⚠️ Chủ đề '[tham-so]' không tồn tại trong cấu hình.` và chuyển sang **Bước 2**.
* **Nếu không có tham số:** Chạy tiếp **Bước 2** thông thường.

*Tiêu chí hoàn thành:* Agent đã nạp cấu hình từ ít nhất một nguồn, in ra cấu trúc các chủ đề khả dụng, và quyết định rẽ nhánh chính xác.

---

### 2. Quét tài liệu và Chọn chủ đề (Scan & Select)
Quét toàn bộ danh sách tệp tin nằm trong thư mục [input_documents/](../../../input_documents/):
* In bảng danh sách tệp tin phát hiện được kèm dung lượng (KB/MB).
* Đọc lướt nội dung (skimming) và so khớp từ khóa của các tệp với danh sách `keywords` của các chủ đề trong cấu hình để tự động đề xuất chủ đề phù hợp nhất.
* Hiển thị danh sách tất cả các chủ đề khả dụng cho người dùng lựa chọn. Chờ người dùng xác nhận chủ đề hoặc yêu cầu đổi sang chủ đề khác.

*Tiêu chí hoàn thành:* Người dùng đã phản hồi lựa chọn chủ đề từ danh sách và Agent đã xác nhận chủ đề được kích hoạt.

---

### 3. Chuyển đổi định dạng và Nạp Kỹ năng (Ingestion & Skill Activation)
Sau khi chủ đề được xác nhận, Agent tiến hành:
1. **Chuyển đổi tài liệu:** Chuyển đổi theo quy trình `/ccba-convert-markdown` — tham khảo skill [markdown-document-processing](../skills/markdown-processing/SKILL.md) cho quy tắc routing theo `project.mode`.
   * Đối với các tệp nhẹ `< 5MB` (`.docx`, `.txt`): Tự động chuyển đổi sang Markdown.
   * Đối với các tệp nặng `> 5MB` (PDF bản vẽ, Excel lớn): In cảnh báo, lập bảng tóm tắt metadata và chỉ convert chi tiết khi thảo luận đi sâu vào tệp đó.
2. **Nạp Kỹ năng:** Nạp toàn bộ các kỹ năng nghiệp vụ được chỉ định trong thuộc tính `required_skills` của chủ đề được chọn.

*Tiêu chí hoàn thành:* Toàn bộ các tệp nhẹ đã được chuyển đổi sang Markdown, và các kỹ năng nghiệp vụ tương ứng đã được nạp thành công.

---

### 4. Áp dụng Guidelines và Khởi động Brainstorming
In ra danh sách các chỉ dẫn thảo luận đặc thù (`guidelines`) của chủ đề đã chọn để bắt đầu phiên trao đổi hai chiều với người dùng.
*   **Nghiên cứu bổ sung:** Khi phát sinh nhu cầu nghiên cứu chuyên sâu (tài liệu lớn, API bên thứ ba, so sánh VBPL), kích hoạt `/ccba-research` chạy song song.

*Tiêu chí hoàn thành:* Các chỉ dẫn của chủ đề đã chọn được hiển thị đầy đủ và cuộc thảo luận chính thức được bắt đầu.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Config đã nạp và chủ đề đã được xác nhận.
*   [x] Tài liệu đầu vào đã chuyển đổi Markdown (nếu có).
*   [x] Guidelines đã hiển thị và phiên brainstorming đã bắt đầu — Agent ở trạng thái chờ trao đổi với người dùng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
