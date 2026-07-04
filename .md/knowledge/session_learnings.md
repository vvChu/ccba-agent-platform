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
- **Giải pháp:** Viết một script kiểm định nhanh (`check_our_links.py`) nhắm trực tiếp vào danh sách các file vừa tạo/chỉnh sửa để check link tuyệt đối (`file:///`) và tương đối.
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

### 5. Baseline Scouting song song sử dụng Subagents
- **Ngữ cảnh:** Khi xây dựng tài liệu kỹ thuật ban đầu cho một codebase lớn hoặc chưa có tài liệu kỹ thuật chuẩn, việc nạp toàn bộ codebase vào một context duy nhất của Agent chính dễ gây quá tải và thiếu chi tiết.
- **Giải pháp:** Chia codebase thành các phân vùng module/package chính thức, khởi chạy song song **tối đa 3-5 subagents** chuyên biệt để nghiên cứu sâu từng phân vùng, sau đó merge các báo cáo tóm tắt để xây dựng tài liệu baseline.
- **Nguồn:** Session `4adb3c4a-3709-4d72-8346-ed0627775238`, 04/07/2026.

### 6. Sao lưu & Rollback tự động khi Phân rã Tài liệu lớn (Size Limit Gate)
- **Ngữ cảnh:** Khi phân rã tài liệu lớn (vượt quá 800 LOC) thành cấu trúc modular, các liên kết tương đối trỏ chéo rất dễ bị hỏng (Broken Links).
- **Giải pháp:** Thực hiện sao lưu tự động tệp tin gốc vào thư mục tạm trước khi chỉnh sửa. Nếu kiểm định `validate_docs.py` báo lỗi liên kết hỏng (`Exit 1`) và Agent không thể sửa đổi sau 3 lần thử, bắt buộc thực hiện rollback khôi phục lại tệp gốc và dọn dẹp các tệp con bị lỗi.
- **Nguồn:** Session `4adb3c4a-3709-4d72-8346-ed0627775238`, 04/07/2026.

### 7. Khớp phần tử DOM theo từ khóa và container cha (Closest Header Matching)
- **Ngữ cảnh:** Khi cần trích xuất các hộp quan hệ hoặc bảng biểu nằm rải rác trên trang web (như TVPL Lược đồ) mà không có class/id cố định hoặc tiêu đề dùng các ký tự gạch ngang/khoảng trắng không đồng nhất (en-dash `–`, em-dash `—`, hyphen `-`).
- **Giải pháp:** Sử dụng `document.querySelectorAll` lọc phần tử có `innerText` bắt đầu bằng từ khóa chính, sau đó dùng `headerEl.closest(...)` để tìm thẻ container chung gần nhất (như `td`, `div`, `table`) rồi lấy tất cả các liên kết `<a>` con bên trong.
- **Nguồn:** Session `49823473-eb8c-4ac7-9dc6-c55d0690e5f7`, 04/07/2026.

### 8. Cách ly môi trường chạy thử nghiệm bằng biến định danh (Pytest Environment Isolation)
- **Ngữ cảnh:** Khi phát triển thư viện kết nối dịch vụ ngoài (như NotebookLM) hỗ trợ cả chế độ Mock (chạy test) và chế độ Real (chạy thật trên máy host đã login). Nếu không cô lập, runner kiểm thử trên host sẽ tự động đọc file cookies thật của dev dẫn đến lỗi bypass Mock, làm hỏng CI.
- **Giải pháp:** Kiểm tra sự xuất hiện của biến môi trường `PYTEST_CURRENT_TEST` trong hàm khởi tạo client để tự động bỏ qua việc nạp cookies thực tế trên host, duy trì chế độ Mock an toàn cho test suite.
- **Nguồn:** Session `49823473-eb8c-4ac7-9dc6-c55d0690e5f7`, 04/07/2026.

---

## Anti-patterns (Cách tránh)

### 1. Quét kiểm định tài liệu đệ quy trên thư mục tạm
- **Vấn đề:** Chạy `validate_docs.py .` trên toàn thư mục dự án khi có hàng nghìn tệp tin tạm/log rác của Agent sẽ gây nghẽn tiến trình và đưa ra hàng trăm lỗi giả (false positives).
- **Thay thế bằng:** Chỉ chạy quét trên các thư mục mã nguồn và tài liệu tĩnh chính thức (`validate_docs.py` giới hạn thư mục), hoặc sử dụng script kiểm thử cục bộ.

### 2. Gửi tài liệu hiện trạng thô trực tiếp lên Cloud API
- **Vấn đề:** Gửi các tài liệu hành chính (Quyết định nhân sự, Hợp đồng tài chính, API Keys) trực tiếp lên AI Gateway công cộng mà không qua làm sạch dẫn đến rủi ro rò rỉ dữ liệu mật.
- **Thay thế bằng:** Bắt buộc chạy qua bộ lọc che giấu dữ liệu nhạy cảm (**`maskara-privacy`**) để redact trước khi gửi chuỗi văn bản lên mô hình AI.

### 3. Không tự động dọn dẹp các Workspace tạm thời của Subagents
- **Vấn đề:** Để các workspace tạm do subagents sinh ra khi chạy teamwork (`/teamwork-preview`) hoặc chạy song song đọng lại trong codebase làm loãng cấu trúc thư mục, tốn bộ nhớ và tăng thời gian quét linter.
- **Thay thế bằng:** Tích hợp quy trình quét và tự động dọn dẹp các thư mục rác này trực tiếp vào cuối mỗi phiên hoạt động thông qua workflow tổng kết (`/ccba-session-retrospective`).

### 4. Dùng so khớp chuỗi cứng nhắc hoặc Regex thô cho tiêu đề layout động
- **Vấn đề:** Các trang web tiếng Việt thường dùng dấu gạch ngang không đồng nhất (ví dụ: en-dash `–`, em-dash `—`, hyphen `-`) hoặc ký tự khoảng trắng lạ. Dùng `split('-')` hoặc regex cứng nhắc sẽ làm rớt dữ liệu (ví dụ: mất quan hệ pháp lý `relations`).
- **Thay thế bằng:** So khớp tương đối bằng `startsWith()`, regex linh hoạt loại bỏ bracket số hiệu `replace(/[\-\–\—\s\u00a0]*\[\d+\]/g, '')`, và tìm kiếm container cha `closest()`.

### 5. Quên chạy Ruff Formatter trước khi đẩy code lên CI
- **Vấn đề:** Chỉ chạy `ruff check --fix` để sửa lỗi logic linter mà quên chạy `ruff format` để format định dạng căn lề, dẫn đến việc CI chạy `ruff format --check` báo lỗi exit code 1 và làm hỏng luồng build.
- **Thay thế bằng:** Luôn chạy chuỗi lệnh `python -m ruff check --fix . && python -m ruff format .` trước khi push mã nguồn.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
