# 🧠 Hướng Dẫn: Mẫu Thử Logic (Logic Prototype)

Mẫu thử logic là một ứng dụng giao diện dòng lệnh tương tác siêu nhỏ (TUI) cho phép người dùng chạy thử mô hình trạng thái (state machine) bằng tay. Sử dụng mẫu này khi câu hỏi thiết kế xoay quanh **logic nghiệp vụ (business logic), chuyển đổi trạng thái (state transitions), hoặc cấu trúc dữ liệu (data shape)**.

---

## 📅 Trường hợp áp dụng
- *"Tôi không chắc mô hình trạng thái này có xử lý được trường hợp biên khi X xảy ra rồi đến Y không?"*
- *"Cấu trúc dữ liệu này có thực sự cho phép biểu diễn mối quan hệ của..."*
- *"Tôi muốn thử nghiệm xem API trông như thế nào trước khi viết code thật."*
- Bất kỳ trường hợp nào người dùng muốn **bấm phím và nhìn trạng thái hệ thống thay đổi**.

---

## 🛠️ Quy trình thực hiện

### 1. Viết rõ câu hỏi thiết kế
Trước khi viết code, hãy mô tả rõ câu hỏi thiết kế cần kiểm chứng bằng 1 đoạn văn ngắn ở đầu file mã nguồn hoặc file `README.md` tạm của mẫu thử.

### 2. Chọn ngôn ngữ & công cụ
Sử dụng đúng ngôn ngữ lập trình của dự án hiện tại. Tận dụng các công cụ/thư viện đã có trong dự án, không cài đặt thêm package manager hoặc runtime mới chỉ để phục vụ mẫu thử.

### 3. Tách biệt Module Logic thuần túy (Pure Logic Module)
Đặt toàn bộ logic cốt lõi (reducer, state machine hoặc các pure functions) đằng sau một interface sạch sẽ, không phụ thuộc vào terminal hay I/O.
- **Pure Reducer**: `(state, action) => state`. Dùng khi các hành động là các sự kiện rời rạc và trạng thái là một giá trị duy nhất.
- **State Machine**: Trạng thái và điều kiện chuyển đổi tường minh. Dùng khi câu hỏi xoay quanh "hành động nào được phép chạy ở trạng thái hiện tại".
- **Pure Functions**: Các hàm biến đổi dữ liệu đơn thuần, không có state ngầm.
- **Class / Module**: Có method quản lý state nội bộ.

*Lưu ý:* Giữ module này thuần túy (không `console.log`, không I/O). TUI shell sẽ import module này và gọi nó, luồng thông tin không đi ngược lại. Khi kiểm chứng xong, ta chỉ việc nhấc module thuần túy này vào codebase thật, còn TUI shell thì xóa đi.

### 4. Xây dựng TUI siêu nhỏ hiển thị trạng thái
Xây dựng một TUI mỏng để điều khiển:
- Mỗi khi trạng thái thay đổi, xóa màn hình (`console.clear()` / `print("\033[2J\033[H")`) và render lại toàn bộ khung hình. Người dùng sẽ luôn nhìn thấy một màn hình trạng thái ổn định thay vì một danh sách cuộn dài vô tận.
- Khung hình gồm 2 phần:
  1. **Trạng thái hiện tại (Current state)**: In đẹp, rõ ràng (JSON format hoặc mỗi dòng 1 trường). Dùng chữ **in đậm (bold)** cho tiêu đề và chữ **mờ (dim)** cho bối cảnh ít quan trọng (IDs, timestamps).
  2. **Phím tắt điều khiển (Keyboard shortcuts)**: Đặt ở dưới cùng, ví dụ: `[a] Thêm người dùng  [d] Xóa người dùng  [q] Thoát`.
- Chạy vòng lặp (read keystroke -> mutate state -> re-render) cho đến khi phím Thoát được bấm.

### 5. Cho phép chạy bằng 1 lệnh duy nhất
Đăng ký lệnh chạy vào `package.json` hoặc task runner tương ứng để người dùng có thể chạy ngay lập tức (ví dụ: `npm run dev:proto-logic`).

---

## 🚫 Các lỗi cần tránh (Anti-patterns)
- **Tuyệt đối không viết test cho prototype.** Prototype sinh ra để bị xóa, không cần test.
- **Không kết nối với cơ sở dữ liệu thật.** Chỉ dùng in-memory store.
- **Không viết code tổng quát hóa.** Mẫu thử chỉ tập trung trả lời đúng 1 câu hỏi duy nhất.
- **Không trộn lẫn code TUI và code Logic.** Giữ logic sạch để có thể tái sử dụng.
