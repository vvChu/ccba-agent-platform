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

---

## Anti-patterns (Cách tránh)

### 1. Late-binding Reference in Loop Closures
- **Vấn đề**: Sử dụng trực tiếp biến vòng lặp bên trong một hàm callback/closure lồng mà không capture. Trình linter sẽ báo lỗi Ruff B023, đồng thời gây lỗi logic nghiêm trọng khi các luồng chạy sau đều tham chiếu đến phần tử cuối cùng của vòng lặp thay vì phần tử tương ứng của chúng.
- **Thay thế bằng**: Sử dụng tham số mặc định để bind cứng giá trị (`def callback(arg, loop_var=loop_var):`).

### 2. Copy-paste Frontmatter Fields Manual Maintenance
- **Vấn đề**: Việc phân tách tệp lớn (split document) mà không chuyển tiếp các siêu dữ liệu quản trị quan trọng (`resource`, `status`, `timestamp`) khiến các tệp con bị linter báo lỗi thiếu trường bắt buộc, hoặc gây mất thông tin truy vết.
- **Thay thế bằng**: Nâng cấp trình đóng gói tự động sao chép các trường Frontmatter siêu dữ liệu cần thiết từ tệp gốc sang toàn bộ tệp con và tệp phụ lục đính kèm.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
