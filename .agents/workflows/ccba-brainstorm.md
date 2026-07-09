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

### 1. Đọc và Gộp cấu hình chủ đề (Hierarchical Config Merge)
Agent bắt buộc phải đọc và gộp cấu hình các chủ đề từ hai nguồn:
1. **Mặc định từ Hub:** Đọc cấu hình mặc định tại [.agents/workflows/resources/brainstorm_topics.yaml](file:///d:/GitHubProjects/ccba-agent-platform/.agents/workflows/resources/brainstorm_topics.yaml).
2. **Cục bộ từ Spoke:** Kiểm tra sự tồn tại của tệp cấu hình cục bộ tại `.md/knowledge/brainstorm_topics.yaml`. Nếu có, đọc và gộp (merge) với cấu hình mặc định (tập tin cục bộ được phép ghi đè các chủ đề trùng `topic_id` hoặc khai báo thêm chủ đề mới như Back Office/Admin).

### 1.5. Xử lý tham số Bypass (Hybrid Branching Logic)
Agent phân tích câu lệnh kích hoạt để phát hiện tham số truyền sau ký tự `--`:
* **Nếu có tham số truyền vào (ví dụ: `/ccba-brainstorm -- legal`):**
  * So khớp tham số đó với danh sách các `topic_id` trong cấu hình đã gộp.
  * Nếu **TRÙNG KHỚP**: Agent thực hiện **Bypass** — lập tức di chuyển sang **Bước 4** để nạp Kỹ năng và chuyển đổi tài liệu, bỏ qua hoàn toàn Bước 2 (Quét tài liệu) và Bước 3 (Hiển thị Menu).
  * Nếu **KHÔNG TRÙNG KHỚP**: Agent in ra cảnh báo: `⚠️ Chủ đề '[tham-so]' không tồn tại trong cấu hình. Tự động chuyển về luồng quét và hiển thị menu chọn.` và chuyển sang **Bước 2**.
* **Nếu không có tham số truyền vào (gõ `/ccba-brainstorm` đơn thuần):** Chạy tiếp **Bước 2** thông thường.

---

### 2. Quét tài liệu đầu vào (Input Scan)
Quét toàn bộ danh sách tệp tin nằm trong thư mục [input_documents/](file:///d:/GitHubProjects/ccba-agent-platform/input_documents/):
* In bảng danh sách tệp tin phát hiện được kèm dung lượng (KB/MB).
* Đọc lướt nội dung (skimming) và so khớp từ khóa của các tệp với danh sách `keywords` của các chủ đề trong cấu hình để tự động đề xuất chủ đề phù hợp nhất.

---

### 3. Hiển thị Menu Tương tác và Rẽ nhánh (Interactive Branching)
Hiển thị danh sách tất cả các chủ đề khả dụng cho người dùng lựa chọn:
* In rõ chủ đề được Agent đề xuất tự động dựa trên kết quả khớp từ khóa ở Bước 2.
* Chờ người dùng xác nhận chủ đề được chọn hoặc yêu cầu đổi sang chủ đề khác (ví dụ: Pháp lý, MEP/PCCC, Admin...).

---

### 4. Chuyển đổi định dạng và Nạp Kỹ năng (Ingestion & Skill Activation)
Sau khi chủ đề được xác nhận, Agent tiến hành:
1. **Chuyển đổi linh hoạt (On-Demand Convert):**
   * Đối với các tệp nhẹ `< 5MB` (`.docx`, `.txt`): Tự động chuyển đổi sang Markdown và lưu tạm tại `.md/extracted_docs/` để làm giàu tri thức của phiên làm việc.
   * Đối với các tệp nặng `> 5MB` (PDF bản vẽ kỹ thuật lớn, Excel bảng tính lớn): In cảnh báo, lập bảng tóm tắt metadata và chỉ convert chi tiết khi thảo luận đi sâu vào tệp đó.
2. **Nạp Kỹ năng:** Nạp toàn bộ các kỹ năng nghiệp vụ được chỉ định trong thuộc tính `required_skills` của chủ đề được chọn.

---

### 5. Áp dụng Guidelines và Khởi động Brainstorming
In ra danh sách các chỉ dẫn thảo luận đặc thù (`guidelines`) của chủ đề đã chọn để bắt đầu phiên trao đổi hai chiều với người dùng.
*   **Chỉ dẫn nghiên cứu bổ sung (Research Legwork):** Nếu trong quá trình thảo luận phát sinh nhu cầu đọc sâu hoặc nghiên cứu chi tiết các tài liệu lớn, các API bên thứ ba, hoặc so sánh đệ quy các văn bản pháp luật, Agent nên chủ động đề xuất người dùng hoặc tự động kích hoạt kỹ năng `/ccba-research` để spawn subagent chạy song song dưới nền, tránh làm gián đoạn hoặc phình to context của cuộc hội thoại chính.

---

## Cách kích hoạt workflow

Người dùng có thể gọi workflow này bằng cách:

* **Luồng chuẩn (Quét & Chọn tương tác):**
  ```text
  /ccba-brainstorm
  ```
* **Luồng nhanh (Bypass đi thẳng vào chủ đề):**
  ```text
  /ccba-brainstorm -- <topic_id>
  ```
  *(Ví dụ: `/ccba-brainstorm -- legal`, `/ccba-brainstorm -- pccc_mep`)*

hoặc nói:
* "Bắt đầu brainstorm tài liệu mới"
* "Quét input_documents và thảo luận ý tưởng"
* "Khởi chạy quy trình brainstorm với chủ đề [tên_chủ_đề]"
