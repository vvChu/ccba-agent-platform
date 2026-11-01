# 🧠 Hướng Dẫn: Mẫu Thử Logic (`Shareable HTML` & TUI Fallback — `v1.3.2`)

Mẫu thử logic là một bản demo tự đóng gói trong **1 tệp HTML độc lập duy nhất (`Shareable HTML`)** (hoặc fallback sang TUI dòng lệnh siêu nhỏ trong môi trường thuần headless) cho phép bất kỳ ai — kể cả người không lập trình (PM, chủ đầu tư, chuyên gia nghiệp vụ) — bấm nút và kiểm chứng mô hình trạng thái (state machine) bằng mắt thường. Sử dụng mẫu này khi câu hỏi thiết kế xoay quanh **logic nghiệp vụ (business logic), chuyển đổi trạng thái (state transitions), hoặc cấu trúc dữ liệu (data shape)**.

---

## 📅 Trường hợp áp dụng
- *"Tôi không chắc mô hình trạng thái này có xử lý được trường hợp biên khi X xảy ra rồi đến Y không?"*
- *"Cấu trúc dữ liệu này có thực sự cho phép biểu diễn mối quan hệ của..."*
- *"Tôi muốn thử nghiệm xem API trông như thế nào trước khi viết code thật."*
- Bất kỳ trường hợp nào người dùng muốn **bấm nút và nhìn trạng thái hệ thống thay đổi trực tiếp**.

---

## 🛠️ Quy trình thực hiện

### 1. Viết rõ câu hỏi thiết kế
Trước khi viết code, hãy mô tả rõ mô hình trạng thái và câu hỏi thiết kế cần kiểm chứng bằng 1 đoạn văn ngắn hiển thị ngay phần mở đầu của bản demo (không chỉ ẩn trong comment).

### 2. Tách biệt Module Logic thuần túy (Portable Pure Logic Module)
Đặt toàn bộ logic cốt lõi (reducer, state machine hoặc các pure functions) bên trong một khối `<script>` (hoặc module Python độc lập nếu chạy TUI) đằng sau một interface sạch sẽ, không chạm vào DOM hay I/O:
- **Pure Reducer**: `(state, action) => state`. Dùng khi các hành động là các sự kiện rời rạc và trạng thái là một giá trị duy nhất.
- **State Machine**: Trạng thái và điều kiện chuyển đổi tường minh. Dùng khi câu hỏi xoay quanh "hành động nào được phép chạy ở trạng thái hiện tại".
- **Pure Functions**: Các hàm biến đổi dữ liệu đơn thuần, không có state ngầm.
- **Class / Module**: Có method quản lý state nội bộ.

*Lưu ý:* Giữ module này thuần túy (không truy cập `document`, không gắn button handler bên trong). Lớp vỏ trang HTML chỉ gọi vào module này; khi câu hỏi thiết kế đã được giải đáp, ta nhấc nguyên khối module thuần túy này vào codebase thật.

### 3. Xây dựng Tệp `Shareable HTML` Duy Nhất (Primary Mode) + `Guided Walkthroughs`
Ưu tiên tạo **1 tệp HTML/CSS/JS thuần duy nhất** (không cài framework, không bundler, không cần dev server) để mở trực tiếp bằng thao tác nhấp đúp chuột và gửi qua lại dễ dàng. Viết toàn bộ nhãn bằng **ngôn ngữ nghiệp vụ (domain language)** theo thứ tự từ trên xuống dưới:
1. **Tiêu đề & giải thích 1 dòng**: Nêu rõ câu hỏi thiết kế từ Bước 1.
2. **Bảng Trạng thái hiện tại (`Current state`)**: Hiển thị toàn bộ các trường trạng thái có nhãn rõ ràng (không xả JSON thô), tự động render lại sau mỗi cú nhấp chuột và làm nổi bật trường vừa thay đổi.
3. **Các nút Chơi tự do (`Free-play buttons`)**: Mỗi hành động một nút bấm để người dùng thử mọi thứ tự bất kỳ.
4. **Kịch bản Dẫn hướng theo Tab (`Guided Walkthroughs`)**: Mỗi tab là một kịch bản kiểm chứng (happy path, ca biên hiểm hóc, hoặc thao tác bị cấm) kèm mô tả ngắn và chuỗi **nút bấm theo thứ tự từng bước**. Khi bắt đầu một tab walkthrough, hệ thống tự động reset về trạng thái khởi tạo chuẩn để kịch bản luôn chạy lặp lại nhất quán.

### 4. Phương án Dự phòng TUI Dòng Lệnh (Headless / CLI Fallback)
Khi môi trường làm việc thuần terminal không có trình duyệt, xây dựng TUI mỏng xóa màn hình và in lại **Current state** + **Keyboard shortcuts** sau mỗi phím bấm, đăng ký chạy bằng 1 lệnh duy nhất.

### 5. Thu hoạch Module Thuần & Lưu vết Nhánh Throwaway
Khi mẫu thử đã giải đáp xong câu hỏi thiết kế: nhấc module logic thuần túy vào codebase thật, lưu vết tệp HTML mẫu thử trên nhánh throwaway (`prototype/<slug>`, ngoài `main`) như một nguồn tư liệu gốc (*primary source*), và ghi nhận kết luận vào `.md/knowledge/issues/[feature_name]/prototypes/NOTES.md`.

---

## 🚫 Các lỗi cần tránh (Anti-patterns)
- **Tuyệt đối không viết test cho prototype.** Prototype sinh ra để trả lời câu hỏi nhanh, không cần test.
- **Không kết nối với cơ sở dữ liệu thật.** Chỉ dùng in-memory store.
- **Không dùng framework/bundler/server cho bản demo logic.** Một tệp HTML duy nhất mở được ngay lập tức mới đảm bảo tính chia sẻ (*shareable*).
- **Không trộn lẫn DOM/UI và code Logic.** Giữ logic sạch để nhấc thẳng sang module sản xuất.
