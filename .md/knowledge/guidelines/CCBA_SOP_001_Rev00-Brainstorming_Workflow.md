# CCBA Quy trình Hoạt động Chuẩn (SOP) — Brainstorming & Xử lý Tài liệu Nhất quán

> [!NOTE]
> **Mã số:** CCBA_SOP_001_Rev00  
> **Ngày ban hành:** 29.06.2026  
> **Phạm vi áp dụng:** Toàn bộ thành viên và AI Agents hoạt động trên CCBA Platform.

Tài liệu này định nghĩa quy trình chuẩn hóa để tiếp nhận, thảo luận và số hóa tri thức từ mọi nguồn thông tin đầu vào thô (PDF, Word, Excel, Hình ảnh, Ghi chú nháp) thông qua một điểm nạp duy nhất.

---

## 1. Nguyên tắc cốt lõi

1. **Điểm nạp duy nhất (Single Source of Input):** Mọi tài liệu, dữ liệu thô phục vụ phiên làm việc hoặc nghiên cứu ban đầu bắt buộc phải được đặt tại thư mục **`input_documents/`** ở thư mục gốc của dự án.
2. **Lean & KISS:** Không thực hiện phân loại thủ công phức tạp ở giai đoạn bắt đầu. Hãy để Agent hỗ trợ quét và đề xuất phân loại tự động.
3. **Tiết kiệm tài nguyên LLM:** Phân cấp chuyển đổi định dạng linh hoạt để tránh lãng phí chi phí API calls đối với tài liệu rác hoặc quá nặng không dùng đến.

---

## 2. Luồng xử lý chi tiết (Workflow Steps)

### Bước 1: Thu thập và Nạp tài liệu (Ingestion)
Người dùng copy tất cả các nguồn dữ liệu vào thư mục [input_documents/](../../../input_documents):
* Các file PDF pháp lý, bản vẽ thiết kế.
* Các file Excel dữ liệu hoặc tiến độ.
* Các file ảnh sơ đồ, ảnh chụp màn hình.
* Các file ghi chú thô sơ khởi (ví dụ: `y_tuong_notes.txt`).

### Bước 2: Quét và Lập danh mục tự động (Auto-Discovery & Skimming)
Người dùng yêu cầu Agent quét thư mục đầu vào. Agent sẽ thực thi phân loại xử lý linh hoạt:
* **Đối với tệp đơn giản và dung lượng nhẹ (< 5MB, `.docx`, `.txt`):** Agent tự động chạy script chuyển đổi sang Markdown ngay lập tức để nạp tri thức vào phiên.
* **Đối với tệp nặng (> 5MB, PDF bản vẽ kỹ thuật lớn, Quy chuẩn hàng trăm trang):** Agent chỉ đọc lướt tiêu đề, metadata, lập bảng danh mục tóm tắt sơ bộ và **trì hoãn** chuyển đổi chi tiết. Chỉ chuyển đổi khi có yêu cầu cụ thể của người dùng hoặc khi thảo luận đi sâu vào tệp đó.

### Bước 2.5: Kích hoạt nhanh bằng Tham số (Hybrid Bypass Mode)
Nếu bạn đã biết rõ chủ đề cần thảo luận và muốn đi thẳng vào nhánh nghiệp vụ chuyên biệt mà không cần qua khâu quét tự động và menu chọn:
* **Cú pháp:** `/ccba-brainstorm -- <topic_id>`
  * *Ví dụ:* `/ccba-brainstorm -- legal` (đi thẳng vào nhánh Pháp lý), `/ccba-brainstorm -- pccc_mep` (đi thẳng vào nhánh Cơ điện & PCCC).
* **Cơ chế hoạt động:** Agent tự động so khớp `topic_id` với cấu hình, nạp các kỹ năng tương ứng (required skills) và kích hoạt bộ hướng dẫn (guidelines) đặc thù ngay lập tức. Nếu gõ sai hoặc để trống, Agent tự động fallback quay lại luồng quét và hiển thị menu chọn.

### Bước 3: Brainstorming và Thảo luận tương tác
* Hai bên tiến hành trao đổi trực tiếp trên chat về các ý tưởng thô và tài liệu trong `input_documents/`.
* Khuyến khích người dùng yêu cầu Agent vẽ sơ đồ **Mermaid** hoặc tạo file sơ đồ **Excalidraw** để trực quan hóa luồng tư duy.
* Khuyến khích yêu cầu Agent đóng vai trò **Người phản biện độc lập (Adversarial Challenger)** để chỉ ra ít nhất 3 rủi ro/điểm yếu của thiết kế trước khi chốt phương án.

### Bước 4: Đúc kết tri thức & Tự động dọn dẹp (Retrospective & Cleanup)
Khi kết thúc phiên làm việc, người dùng kích hoạt workflow `/ccba-session-retrospective`. Agent sẽ tự động:
1. Tổng hợp toàn bộ quyết định thiết kế vào tệp `.md/knowledge/session_learnings.md`.
2. Phân tích nội dung và tự động phân loại các tệp tin đã sử dụng trong `input_documents/` sang các thư mục con tương ứng của `.md/`:
   * Các văn bản quy chuẩn pháp lý, nghị định $\rightarrow$ `.md/legal_docs/` hoặc `.md/extracted_docs/`.
   * Các tài liệu phân tích kỹ thuật, sơ đồ, hướng dẫn $\rightarrow$ `.md/knowledge/`.
   * Biên bản thảo luận, ý kiến $\rightarrow$ `.md/seminars/`.
3. In bảng đề xuất di chuyển tệp tin để người dùng phê duyệt nhanh.
4. Thực thi di chuyển vật lý và dọn sạch hoàn toàn thư mục `input_documents/` để sẵn sàng cho các phiên làm việc tiếp theo.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
