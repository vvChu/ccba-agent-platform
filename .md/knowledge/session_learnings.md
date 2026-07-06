# Session Learnings — OKF Bundle & Legal Crawler Upgrades (2026-07-05)

Tài liệu này tổng hợp các bài học kinh nghiệm, patterns và giải pháp tối ưu được đúc rút từ chuỗi nâng cấp tính năng và sửa lỗi linter pháp lý.

---

## Patterns (Mẫu tốt)

### 1. VIP Session Mutex Lock
- **Ngữ cảnh**: Tránh xung đột phiên đăng nhập VIP (kick-out) khi chạy nhiều tiến trình cào dữ liệu song song hoặc phân tán.
- **Giải pháp**:
  - Sử dụng file lock nguyên tử tại một vị trí cố định (ví dụ: `.md/data/tvpl_vip_session.lock`).
  - Ghi nhận thông tin PID và timestamp của tiến trình sở hữu khóa.
  - Hỗ trợ cơ chế tự giải phóng (Override) nếu khóa chết (deadlock) vượt quá thời gian tối đa cho phép (ví dụ: > 5 phút).
  - Sử dụng block `try...finally` để đảm bảo tệp khóa luôn được giải phóng sạch sẽ khi thoát tiến trình (kể cả khi gặp ngoại lệ).
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 2. Late-binding Closure Capture (Default Parameter Binding)
- **Ngữ cảnh**: Định nghĩa hàm lồng (nested function) hoặc hàm callback bên trong một vòng lặp sử dụng biến vòng lặp (ví dụ: `filepath` trong vòng lặp duyệt tệp). Tránh cảnh báo Ruff B023.
- **Giải pháp**: Sử dụng default parameter binding để bắt cứng giá trị của biến vòng lặp tại thời điểm khai báo thay vì tham chiếu động lúc thực thi:
  ```python
  for filepath in files:
      def replace_link(match, filepath=filepath):
          # Sử dụng filepath an toàn ở đây
          ...
  ```
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 3. Raise from None in Non-chained Exceptions
- **Ngữ cảnh**: Khi kiểm tra logic nghiệp vụ độc lập (như kiểm tra timeout) bên trong một block `try...except Exception:` và muốn ném ngoại lệ mới nhưng không muốn hiển thị trace ngược (context chain) của lỗi trước đó không liên quan. Tránh cảnh báo Ruff B904.
- **Giải pháp**: Sử dụng `from None`:
  ```python
  try:
      ...
      if time.time() - start >= timeout:
          raise TimeoutError("Timeout occurred") from None
  except Exception as e:
      ...
  ```
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 4. Skill Link Portability
- **Ngữ cảnh**: Khi định nghĩa các liên kết tham chiếu bên trong tệp `SKILL.md` (ví dụ: dẫn đến tệp reference hoặc cấu hình).
- **Giải pháp**: Luôn sử dụng liên kết tương đối (relative paths) thay vì liên kết tuyệt đối dạng `file:///d:/...` để tránh bị hỏng link khi các nhà phát triển khác chạy trên máy cá nhân của họ.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-05

### 5. Parse-Protection (Bảo vệ phân tích thủ công)
- **Ngữ cảnh**: Khi cần tự động cập nhật báo cáo hoặc tệp tri thức bằng AI/scripts nhưng muốn bảo toàn tuyệt đối phần ghi chú thủ công của con người viết trong cùng một tệp.
- **Giải pháp**: Thiết kế tệp tin phân tầng và sử dụng cặp thẻ marker comment ẩn để cách ly hoàn toàn:
  * Đọc tệp tin gốc và dùng regex để trích xuất nội dung giữa `<!-- DEVELOPER-NOTES-START -->` và `<!-- DEVELOPER-NOTES-END -->`.
  * Tạo nội dung tự động mới và bọc trong cặp thẻ `<!-- AUTO-GENERATED-START -->` và `<!-- AUTO-GENERATED-END -->`.
  * Nối hai phần lại và ghi đè lại file.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

### 6. Two-axis Parallel Review (Đánh giá song song hai trục)
- **Ngữ cảnh**: Cần rà soát một đối tượng phức tạp dưới nhiều góc độ khác nhau (như code review theo Standards và Spec) để tránh ô nhiễm context.
- **Giải pháp**: Spawn hai sub-agents chạy độc lập và song song dưới cùng một context cha. Sub-agent A chỉ rà soát Standards; sub-agent B chỉ rà soát Spec. Sau đó gộp kết quả ở Agent chính.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

---

## Anti-patterns (Cách tránh)

### 1. Late-binding Reference in Loop Closures
- **Vấn đề**: Sử dụng trực tiếp biến vòng lặp bên trong một hàm callback/closure lồng mà không capture. Trình linter sẽ báo lỗi Ruff B023, đồng thời gây lỗi logic nghiêm trọng khi các luồng chạy sau đều tham chiếu đến phần tử cuối cùng của vòng lặp thay vì phần tử tương ứng của chúng.
- **Thay thế bằng**: Sử dụng tham số mặc định để bind cứng giá trị (`def callback(arg, loop_var=loop_var):`).

### 2. Copy-paste Frontmatter Fields Manual Maintenance
- **Vấn đề**: Việc phân tách tệp lớn (split document) mà không chuyển tiếp các siêu dữ liệu quản trị quan trọng (`resource`, `status`, `timestamp`) khiến các tệp con bị linter báo lỗi thiếu trường bắt buộc, hoặc gây mất thông tin truy vết.
- **Thay thế bằng**: Nâng cấp trình đóng gói tự động sao chép các trường Frontmatter siêu dữ liệu cần thiết từ tệp gốc sang toàn bộ tệp con và tệp phụ lục đính kèm.

### 3. Monolithic Workflow File
- **Vấn đề**: Đặt toàn bộ nội dung hướng dẫn chi tiết các bước và tiêu chí hoàn thành trực tiếp bên trong thư mục `.agents/workflows/`. Điều này làm tăng kích thước tệp tĩnh và tăng context load của mô hình một cách vô ích.
- **Thay thế bằng**: Tách thành một tệp workflow mỏng (wrapper) chỉ chứa mô tả ngắn gọn và lệnh nạp động tệp `SKILL.md` tương ứng nằm dưới thư mục `.agents/skills/`.

### 4. Redundant Agent Skills
- **Vấn đề**: Tạo thêm một kỹ năng (Skill) thực thi độc lập cho Agent (ví dụ: `tvpl_vip_mutex_downloader`) khi logic đó đã được xử lý hoàn chỉnh và tự động trong code Python chạy ngầm. Việc này làm tăng Context Load mà không đem lại giá trị thực thi trực tiếp nào cho Agent.
- **Thay thế bằng**: Tái sử dụng qua code hoặc chuyển đổi thành tài liệu kiến trúc (ADR) lưu trong thư mục tri thức.

### 5. Automatic High-cost LLM API Invocation
- **Vấn đề**: Tự động gọi phân tích sâu của LLM trên các tệp mới/cập nhật ngay khi phát hiện thay đổi SHA mà không hỏi ý kiến người dùng. Điều này gây lãng phí token và tài nguyên lớn.
- **Thay thế bằng**: Bổ sung cờ kiểm tra nhanh (ví dụ: `--check-only`) để Agent liệt kê các tệp thay đổi và hỏi ý kiến kỹ sư trước khi thực thi AI Gateway phân tích sâu.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
