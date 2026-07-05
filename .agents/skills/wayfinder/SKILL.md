---
name: wayfinder
description: Lập bản đồ định hướng để giải quyết các bài toán lớn/mơ hồ thông qua danh sách các ticket công việc.
disable-model-invocation: true
---

# Kỹ năng Định hướng Giải quyết Bài toán Mơ hồ (Wayfinder)

Kỹ năng này giúp thiết lập và vận hành Bản đồ định hướng (Wayfinding Map) để chia nhỏ một ý tưởng lớn, mơ hồ thành các ticket điều tra cụ thể, giải quyết từng vấn đề một cho đến khi lộ trình đến đích hoàn toàn rõ ràng.

## Nguyên tắc Tham chiếu theo Tên (Refer by name)

Mỗi bản đồ và ticket đều có tên gọi cụ thể. Trong mọi báo cáo hoặc nhật ký giao tiếp, **bắt buộc** phải gọi tên đầy đủ của ticket (nhúng liên kết tương ứng) thay vì chỉ dùng số hiệu hoặc mã định danh (Ví dụ: dùng `[Đóng gói Mutex Lock](link)` thay vì chỉ viết `#42`).

---

## Cấu trúc Bản đồ (The Map)

Bản đồ có thể lưu dưới dạng file Markdown cục bộ (mặc định) hoặc dạng Issue trên Issue Tracker của kho lưu trữ (tham khảo `docs/agents/issue-tracker.md`). Cấu trúc bản đồ gồm 4 phần chính:

1. **Điểm đích (Destination):** Mô tả cụ thể trạng thái hoàn thành của toàn bộ bài toán (ví dụ: một bộ thông số spec, một quyết định kiến trúc cốt lõi đã chốt).
2. **Ghi chú (Notes):** Các lưu ý đặc biệt, kỹ năng cần nạp cho phiên làm việc.
3. **Quyết định đã chốt (Decisions so far):** Nhật ký lưu trữ kết quả của các ticket đã giải quyết (chứa tên ticket, link và tóm tắt 1 dòng).
4. **Sương mù (Fog):** Danh sách các vấn đề dự kiến sẽ phát sinh nhưng chưa thể làm sắc nét thành ticket ở thời điểm hiện tại.

---

## Phân loại Ticket (Ticket Types)

Mỗi ticket là một tác vụ có kích thước vừa đủ để giải quyết trong một phiên làm việc của Agent, thuộc một trong bốn loại:
- **Research (Nghiên cứu):** Đọc tài liệu, API bên ngoài. Đầu ra là tệp Markdown tóm tắt.
- **Prototype (Mẫu thử):** Tạo nhanh một mockup, outline, hoặc logic code thô để phản hồi trực quan.
- **Grilling (Chất vấn):** Phỏng vấn chuyên sâu từng câu hỏi một với Kỹ sư sử dụng kỹ năng `/grilling` và `domain-modeling`.
- **Task (Tác vụ):** Các công việc thủ công thực thi không cần thảo luận (cấu hình access, di chuyển thư mục...).

---

## Chỉ dẫn thực hiện quy trình

### Bước 1: Khởi lập bản đồ (Chart the map)
- Khi nhận yêu cầu mơ hồ, thực hiện phỏng vấn `/grilling` để xác định **Điểm đích (Destination)**.
- Phác thảo bản đồ đầu tiên: Liệt kê các quyết định cần làm rõ, xác định các ticket unblocked ở biên giới tri thức (Frontier), đưa các phần chưa rõ ràng vào mục **Sương mù (Fog)**.
- **Phân công (Claiming):** Đăng ký gán (assign) các ticket unblocked cho Agent thực hiện để tránh chạy trùng lặp.
- **Tiêu chí hoàn thành:** Tệp bản đồ được khởi tạo thành công (cục bộ hoặc trên tracker) chứa ít nhất một ticket unblocked và danh sách sương mù ban đầu.

### Bước 2: Thực thi giải quyết Ticket (Work through the map)
- Nạp toàn bộ nội dung Bản đồ vào ngữ cảnh làm việc.
- Chọn ticket unblocked đầu tiên theo thứ tự hoặc theo chỉ định của người dùng. Cập nhật trạng thái ticket thành `in-progress` (hoặc tự assign trên tracker) để xác nhận quyền sở hữu.
- Sử dụng các kỹ năng cần thiết để giải quyết ticket.
- Ghi nhận câu trả lời vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ, chuyển trạng thái ticket thành `resolved` (hoặc `closed`), đồng thời cập nhật làm sắc nét các vùng Sương mù lân cận thành ticket mới nếu đã đủ thông tin.
- **Tiêu chí hoàn thành:** Ticket mục tiêu được chuyển sang trạng thái hoàn thành, ghi nhận chi tiết kết quả xử lý và cập nhật bản đồ thành công.

### Bước 3: Bàn giao phiên (Handoff)
- Kết thúc phiên làm việc bằng cách in ra khối thông tin **Bàn giao (Next steps)**.
- Liệt kê cụ thể danh sách các ticket đã unblocked tiếp theo để Kỹ sư hoặc Agent của phiên kế tiếp có thể copy-paste chạy song song hoặc tuần tự.
- **Tiêu chí hoàn thành:** Khối lệnh bàn giao "Next steps" được in rõ ràng ở cuối phiên hội thoại.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
