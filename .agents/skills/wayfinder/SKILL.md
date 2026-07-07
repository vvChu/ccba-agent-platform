---
name: wayfinder
description: Lập bản đồ định hướng để giải quyết các bài toán lớn/mơ hồ thông qua danh sách các ticket công việc.
disable-model-invocation: true
---

# Kỹ năng Định hướng Giải quyết Bài toán Mơ hồ (Wayfinder)

Kỹ năng này giúp thiết lập và vận hành Bản đồ định hướng (Wayfinding Map) để chia nhỏ một ý tưởng lớn, mơ hồ thành các ticket điều tra cụ thể, giải quyết từng vấn đề một cho đến khi lộ trình đến đích hoàn toàn rõ ràng.

## Nguyên tắc Hoạch định (Plan, don't do)

Wayfinder mặc định là quá trình lập kế hoạch (planning): mỗi ticket nhằm giải quyết một quyết định, và bản đồ hoàn thành khi lộ trình đã hoàn toàn rõ ràng — không còn gì cần quyết định thêm trước khi bắt tay vào thực hiện dự án. Mong muốn nhảy vào viết code/triển khai trực tiếp thường là tín hiệu cho thấy bạn đã chạm đến biên giới của bản đồ và đã đến lúc bàn giao (handoff). Một dự án có thể ghi đè nguyên tắc này trong phần Ghi chú (Notes) của bản đồ (kết hợp cả thực thi và định hướng) — nhưng nếu không có ghi chú đó, hãy tập trung tạo ra các Quyết định (decisions) chứ không phải Thành phẩm (deliverables).

---

## Nguyên tắc Tham chiếu theo Tên (Refer by name)

Mỗi bản đồ và ticket đều có tên gọi cụ thể. Trong mọi báo cáo hoặc nhật ký giao tiếp, **bắt buộc** phải gọi tên đầy đủ của ticket (nhúng liên kết tương ứng) thay vì chỉ dùng số hiệu hoặc mã định danh (Ví dụ: dùng `[Đóng gói Mutex Lock](https://github.com)` thay vì chỉ viết `#42`).

---

## Cấu trúc Bản đồ (The Map)

Bản đồ có thể lưu dưới dạng file Markdown cục bộ (mặc định) hoặc dạng Issue trên Issue Tracker của kho lưu trữ (nếu kho chứa được cấu hình). Cấu trúc bản đồ gồm các phần chính:

1. **Điểm đích (Destination):** Mô tả cụ thể trạng thái hoàn thành của toàn bộ bài toán (ví dụ: một bộ thông số spec, một quyết định kiến trúc cốt lõi đã chốt).
2. **Ghi chú (Notes):** Các lưu ý đặc biệt, kỹ năng cần nạp cho phiên làm việc.
3. **Quyết định đã chốt (Decisions so far):** Nhật ký lưu trữ kết quả của các ticket đã giải quyết (chứa tên ticket, link và tóm tắt 1 dòng).
4. **Chưa xác định rõ (Not yet specified):** Danh sách các vấn đề dự kiến sẽ phát sinh nằm trong phạm vi đích đến, nhưng chưa thể làm sắc nét thành ticket ở thời điểm hiện tại.
5. **Ngoài phạm vi (Out of scope):** Danh sách các tác vụ hoặc quyết định đã bị chủ động loại trừ khỏi phạm vi nỗ lực hiện tại (kèm lý do loại trừ và liên kết ticket đã đóng nếu có).

---

## Phân loại Ticket (Ticket Types)

Mỗi ticket thuộc loại **HITL** (Human-in-the-loop — cộng tác trực tiếp với con người để thảo luận/chốt phương án) hoặc **AFK** (Agent tự chủ thực hiện). Một ticket HITL chỉ được giải quyết thông qua tương tác trao đổi trực tiếp; Agent tuyệt đối không tự đóng vai người dùng để tự trả lời các câu hỏi chất vấn (hành vi Agent tự hỏi tự trả lời trong Grilling loop được coi là vi phạm nghiêm trọng nguyên tắc này).

*   **Research (Nghiên cứu) [AFK]:** Đọc tài liệu, API bên ngoài, hoặc tri thức cục bộ. Đầu ra là tệp Markdown tóm tắt. Dùng khi cần tri thức nằm ngoài thư mục làm việc hiện tại.
*   **Prototype (Mẫu thử) [HITL]:** Tạo nhanh một mockup, outline, hoặc logic code thô qua kỹ năng `/prototype` để phản hồi trực quan. Dùng khi câu hỏi cốt lõi là "giao diện trông như thế nào" hoặc "hành vi hoạt động ra sao".
*   **Grilling (Chất vấn) [HITL]:** Phỏng vấn chuyên sâu từng câu hỏi một với Kỹ sư sử dụng kỹ năng `/grilling` và `/domain-modeling`.
*   **Task (Tác vụ) [HITL hoặc AFK]:** Các công việc thực thi thủ công cần phải hoàn thành trước khi chốt một quyết định — không có gì cần quyết định hay nghiên cứu, nhưng quá trình thảo luận bị chặn (blocked) cho đến khi tác vụ này xong (ví dụ: đăng ký dịch vụ, phân quyền, di chuyển dữ liệu). Đây là loại duy nhất thực thi hành động ("do") thay vì chốt quyết định ("decide") — và mục tiêu của nó là gỡ chặn quyết định, chứ không phải bàn giao thành phẩm cuối cùng. Agent tự chạy nếu có thể (AFK), hoặc cung cấp checklist cụ thể cho người dùng thực hiện (HITL). Sau khi xong, cập nhật kết quả và các thông tin phụ thuộc (credential, URL, số lượng dòng...).

---

## Chỉ dẫn thực hiện quy trình

### Bước 1: Khởi lập bản đồ (Chart the map)
- Khi nhận yêu cầu mơ hồ, thực hiện phỏng vấn `/grilling` để xác định **Điểm đích (Destination)**.
- Phác thảo bản đồ đầu tiên: Liệt kê các quyết định cần làm rõ, xác định các ticket unblocked ở biên giới tri thức (Frontier), đưa các phần chưa rõ ràng vào mục **Chưa xác định rõ (Not yet specified)**. **Nếu quá trình này không phát hiện vùng mờ (fog) nào** — lộ trình đến đích đã hoàn toàn rõ ràng và quy mô dự án đủ nhỏ để giải quyết trong một phiên làm việc — bạn không cần lập bản đồ Wayfinder. Hãy dừng lại và hỏi ý kiến người dùng về cách tiếp cận trực tiếp.
- **Phân công (Claiming):** Đăng ký gán (assign) các ticket unblocked cho Agent thực hiện để tránh chạy trùng lặp.
- **Tiêu chí hoàn thành:** Tệp bản đồ được khởi tạo thành công (cục bộ hoặc trên tracker) chứa ít nhất một ticket unblocked và danh sách chưa xác định rõ ban đầu.

### Bước 2: Thực thi giải quyết Ticket (Work through the map)
- Nạp toàn bộ nội dung Bản đồ vào ngữ cảnh làm việc.
- Chọn ticket unblocked đầu tiên theo thứ tự hoặc theo chỉ định của người dùng. Cập nhật trạng thái ticket thành `in-progress` (hoặc tự assign trên tracker) để xác nhận quyền sở hữu.
- Sử dụng các kỹ năng cần thiết để giải quyết ticket.
- Nếu trong quá trình giải quyết, phát hiện ticket nằm ngoài Điểm đích (Destination), thực hiện đóng (close) ticket và di chuyển thông tin vào vùng **Ngoài phạm vi (Out of scope)** kèm giải trình ngắn.
- Ghi nhận câu trả lời vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ, chuyển trạng thái ticket thành `resolved` (hoặc `closed`), đồng thời cập nhật làm sắc nét các vùng chưa xác định rõ lân cận thành ticket mới nếu đã đủ thông tin.
- **Tiêu chí hoàn thành:** Ticket mục tiêu được chuyển sang trạng thái hoàn thành hoặc ngoài phạm vi, ghi nhận chi tiết kết quả xử lý và cập nhật bản đồ thành công.

### Bước 3: Bàn giao phiên (Handoff)
- Kết thúc phiên làm việc bằng cách in ra khối thông tin **Bàn giao (Next steps)**.
- Liệt kê cụ thể danh sách các ticket đã unblocked tiếp theo để Kỹ sư hoặc Agent của phiên kế tiếp có thể copy-paste chạy song song hoặc tuần tự.
- **Tiêu chí hoàn thành:** Khối lệnh bàn giao "Next steps" được in rõ ràng ở cuối phiên hội thoại.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
