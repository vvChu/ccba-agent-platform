# CCBA Session Learnings: Tích lũy Tri thức Phiên làm việc (Cập nhật QC)

Tài liệu này lưu trữ các tri thức kỹ thuật, bài học thực tế, Patterns và Anti-patterns tích lũy được trong phiên làm việc này để làm tài liệu tham khảo lâu dài cho dự án CCBA Platform.

---

## Patterns (Mẫu tốt)

### 1. Mô hình Producer-Consumer cho Soạn thảo theo Mẫu (Study-to-Generate)
- **Ngữ cảnh:** Khi cần xây dựng hệ thống soạn thảo tài liệu (hợp đồng, quyết định, hồ sơ thầu) sử dụng AI. Nếu gộp chung cả việc nghiên cứu mẫu và sinh văn bản vào một flow duy nhất, AI sẽ dễ bị ảo ảnh, sai cấu trúc và khó duy trì tính nhất quán.
- **Giải pháp:** Phân tách làm hai quy trình độc lập:
  1.  **Quy trình A (Producer - `/ccba-extract-style`)**: Nghiên cứu tài liệu thô, phân tích văn phong và tự động sinh ra tệp template sạch có placeholders (`{{placeholders}}`) cùng metadata phân loại ở frontmatter.
  2.  **Quy trình B (Consumer - `/ccba-copywriting`)**: Chỉ nạp các tệp template chuẩn đã được dựng sẵn từ quy trình A, yêu cầu người dùng điền placeholders và hoàn thiện nội dung.
- **Nguồn:** Session `b75d19fa-761a-42da-ace5-94839b021a9f`, 04/07/2026.

### 2. Ưu tiên Đường dẫn tương đối (Relative Links) trong Tài liệu
- **Ngữ cảnh:** Khi viết tài liệu Markdown có các liên kết dẫn đến các tệp tin cấu hình hoặc thư mục khác trong dự án (ví dụ: liên kết đến thư mục `templates/` hoặc file `SKILL.md`).
- **Giải pháp:** Sử dụng liên kết tương đối chuẩn mực (ví dụ: `../skills/copywriting/templates/`) thay vì liên kết tuyệt đối cứng (ví dụ: `file:///d:/GitHubProjects/...`) để đảm bảo các tệp tin không bị lỗi liên kết hỏng khi chuyển mã nguồn sang môi trường máy tính khác của Kỹ sư hoặc Agent mới.
- **Nguồn:** Session `b75d19fa-761a-42da-ace5-94839b021a9f`, 04/07/2026.

### 3. Kiểm định liên kết cục bộ nhanh (Local Link Checking Script)
- **Ngữ cảnh:** Trong các dự án lớn, chạy công cụ kiểm định toàn bộ tài liệu (`validate_docs.py`) rất chậm do phải quét đệ quy hàng ngàn tệp log hoặc tệp tạm của Agent, sinh ra nhiều cảnh báo không liên quan.
- **Giải pháp:** Viết một script kiểm định nhanh ([check_our_links.py](file:///C:/Users/chuvu/.gemini/antigravity/brain/b75d19fa-761a-42da-ace5-94839b021a9f/scratch/check_our_links.py)) nhắm trực tiếp vào danh sách các file vừa tạo/chỉnh sửa để check link tuyệt đối (`file:///`) và tương đối.
- **Nguồn:** Session `b75d19fa-761a-42da-ace5-94839b021a9f`, 04/07/2026.

### 4. Ép kiểu UTF-8 cho Output Console trên Windows
- **Ngữ cảnh:** Khi chạy các Python scripts xử lý văn bản tiếng Việt từ terminal của Windows (cmd hoặc PowerShell), hệ thống mặc định dùng bảng mã cp1252 gây ra lỗi crash `UnicodeEncodeError`.
- **Giải pháp:** Chèn đoạn mã cấu hình ép kiểu mã hóa UTF-8 cho dòng xuất nhập chuẩn của hệ thống:
  ```python
  import sys
  if sys.platform == "win32":
      import io
      sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
      sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
  ```
- **Nguồn:** Session `b75d19fa-761a-42da-ace5-94839b021a9f`, 04/07/2026.

---

## Anti-patterns (Cách tránh)

### 1. Quét kiểm định tài liệu đệ quy trên thư mục tạm
- **Vấn đề:** Chạy `validate_docs.py .` trên toàn thư mục dự án khi có hàng nghìn tệp tin tạm/log rác của Agent sẽ gây nghẽn tiến trình và đưa ra hàng trăm lỗi giả (false positives).
- **Thay thế bằng:** Chỉ chạy quét trên các thư mục mã nguồn và tài liệu tĩnh chính thức (`validate_docs.py` giới hạn thư mục), hoặc sử dụng script kiểm thử cục bộ.

### 2. Gửi tài liệu hiện trạng thô trực tiếp lên Cloud API
- **Vấn đề:** Gửi các tài liệu hành chính (Quyết định nhân sự, Hợp đồng tài chính, API Keys) trực tiếp lên AI Gateway công cộng mà không qua làm sạch dẫn đến rủi ro rò rỉ dữ liệu mật.
- **Thay thế bằng:** Bắt buộc chạy qua bộ lọc che giấu dữ liệu nhạy cảm (**`maskara-privacy`**) để redact trước khi gửi chuỗi văn bản lên mô hình AI.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
