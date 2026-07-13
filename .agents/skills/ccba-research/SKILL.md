---
name: ccba-research
description: Nghiên cứu chuyên sâu một vấn đề kỹ thuật hoặc pháp lý đối chiếu với các nguồn tài liệu gốc đáng tin cậy bằng cách khởi chạy subagent chạy ngầm.
keywords: [research, nghiên cứu, tìm hiểu, tra cứu]
---

# 📚 Kỹ năng: ccba-research (Nghiên Cứu Chạy Ngầm)

Kỹ năng này hướng dẫn Agent cách khởi chạy một **background subagent** (`research` subagent) để thực hiện các cuộc điều tra tài liệu, thu thập thông tin facts từ các API, mã nguồn hoặc Văn bản Pháp luật (VBPL) song song dưới nền. Điều này giúp Agent chính tiếp tục làm việc mà không bị block và giảm thiểu token bloating cho cuộc hội thoại chính.

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)
Kỹ năng chỉ được coi là hoàn thành khi đáp ứng các điều kiện sau:
1.  Khởi chạy thành công subagent `research` chạy ngầm.
2.  Subagent thu thập thông tin trực tiếp từ **các nguồn sơ cấp đáng tin cậy** (tài liệu chính thức, source code dự án, API gốc, VBPL hiện hành) chứ không dùng tài liệu viết lại cấp hai.
3.  Kết quả nghiên cứu được xuất ra một file Markdown duy nhất, có trích dẫn nguồn (citations) rõ ràng cho từng tuyên bố.
4.  File kết quả nghiên cứu được lưu trữ tại thư mục tri thức dự án:
    `.md/knowledge/research_and_studies/` (nếu chưa có thư mục này, hãy tạo mới).

---

## 🛠️ Quy trình thực hiện

### Bước 1: Xác định câu hỏi nghiên cứu & Nguồn sơ cấp
Xác định rõ câu hỏi nghiên cứu của người dùng và các nguồn tài liệu gốc cần đọc (ví dụ: file luật trong `.md/legal_docs/`, API docs của bên thứ ba, codebase hiện tại).
   *Tiêu chí hoàn thành:* Agent đã ghi nhận danh sách các câu hỏi nghiên cứu cốt lõi cùng đường dẫn các tệp nguồn sơ cấp tương ứng.

### Bước 2: Khởi chạy Subagent chạy ngầm
Sử dụng công cụ `invoke_subagent` để spawn một subagent thuộc loại `research` với prompt mô tả chi tiết:
- **Role**: `Codebase Researcher` hoặc `Legal Analyst` tùy thuộc vào nội dung nghiên cứu.
- **Prompt**:
  - Giao nhiệm vụ cụ thể cho subagent (những câu hỏi cần trả lời).
  - Chỉ định rõ file/thư mục cần đọc và các URL tài liệu chính thống.
  - Yêu cầu subagent lưu file báo cáo Markdown vào thư mục `.md/knowledge/research_and_studies/research_[chủ_đề]_[timestamp].md` và thông báo lại đường dẫn tuyệt đối khi hoàn tất.
   *Tiêu chí hoàn thành:* Agent chính nhận được ID phiên làm việc (Conversation ID) của subagent và ghi nhận trạng thái khởi chạy thành công dưới nền.

### Bước 3: Tiếp tục công việc chính & Hấp thụ kết quả
Trong khi subagent chạy ngầm đang đọc tài liệu và viết báo cáo, Agent chính tiếp tục trao đổi hoặc thực hiện các task khác với người dùng.
Khi nhận được thông báo subagent đã hoàn thành:
- Đọc file báo cáo Markdown mà subagent vừa tạo ra.
- Trình bày tóm tắt kết quả nghiên cứu và trỏ người dùng tới liên kết file báo cáo click được.
   *Tiêu chí hoàn thành:* Báo cáo Markdown từ subagent được Agent chính nạp vào ngữ cảnh, trích xuất tóm tắt và hiển thị liên kết truy cập trực tiếp cho người dùng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
