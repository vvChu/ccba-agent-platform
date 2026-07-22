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

Mỗi bản đồ và ticket đều có tên gọi cụ thể. Trong mọi báo cáo hoặc nhật ký giao tiếp, **bắt buộc** phải gọi tên đầy đủ của ticket (nhúng liên kết tương ứng) thay vì chỉ dùng số hiệu hoặc mã định danh (Ví dụ: dùng `[Đóng gói Mutex Lock](file:///...)` hoặc link GitHub `#42` thay vì chỉ viết ngắn gọn).

---

## Cấu trúc Bản đồ (The Map)

Bản đồ có thể lưu dưới dạng file Markdown cục bộ (mặc định tại `.md/knowledge/issues/<feature>/map.md`) hoặc dạng Issue trên Issue Tracker của kho lưu trữ (gắn nhãn `wayfinder:map`). Cấu trúc bản đồ gồm các phần chính:

1. **Điểm đích (Destination):** Mô tả cụ thể trạng thái hoàn thành của toàn bộ bài toán. Điểm đích này cố định phạm vi (scope) của bản đồ.
2. **Ghi chú (Notes):** Các lưu ý đặc biệt, các kỹ năng bổ trợ cần nạp.
3. **Quyết định đã chốt (Decisions so far):** Nhật ký ghi nhận kết quả của các ticket đã giải quyết (chứa tên ticket, link và tóm tắt 1 dòng).
4. **Sương mù chiến trận / Chưa xác định rõ (Not yet specified):** Bản đồ cố tình không đầy đủ: không vẽ những gì chưa thể nhìn thấy. Nơi ghi nhận sơ lược các quyết định dự kiến sẽ tới nhưng chưa đủ sắc nét để tạo ticket (do phụ thuộc vào các ticket khác đang mở).
5. **Ngoài phạm vi (Out of scope):** Danh sách các tác vụ hoặc quyết định đã bị chủ động loại trừ khỏi phạm vi nỗ lực hiện tại. Nếu một ticket đang chạy bị phát hiện là nằm ngoài điểm đích, **đóng ticket đó lại** và ghi nhận lý do tại đây kèm link ticket.

---

## Phân loại Ticket (Ticket Types)

Mỗi ticket con đại diện cho một câu hỏi cần làm rõ, tương ứng với một phiên làm việc khoảng 100K tokens của Agent. Mỗi ticket thuộc loại **HITL** (cộng tác trực tiếp với con người) hoặc **AFK** (Agent tự chủ thực hiện):

*   **Research (Nghiên cứu) [AFK]:** Đọc tài liệu, API bên ngoài, hoặc tri thức cục bộ. Đầu ra là tệp Markdown tóm tắt. Dùng khi cần tri thức nằm ngoài codebase hiện tại.
*   **Prototype (Mẫu thử) [HITL]:** Tạo nhanh một mẫu thử thô qua kỹ năng `/prototype` để phản hồi trực quan. Dùng khi câu hỏi cốt lõi là "giao diện trông như thế nào" hoặc "hành vi hoạt động ra sao".
*   **Grilling (Chất vấn) [HITL]:** Phỏng vấn chuyên sâu từng câu hỏi một với Kỹ sư sử dụng kỹ năng `/ccba-grilling` và `/domain-modeling`.
*   **Task (Tác vụ) [HITL hoặc AFK]:** Các công việc thực thi thủ công cần phải hoàn thành để unblock một quyết định (ví dụ: xin quyền truy cập, config tài khoản, dump dữ liệu mẫu). Đây là loại duy nhất thực thi hành động ("do") chứ không phải chốt quyết định ("decide"). Agent tự chạy (AFK) hoặc cung cấp checklist cụ thể cho người dùng (HITL).

---

## Quy trình Vận hành (Workflow)

### Bước 1: Khởi lập bản đồ (Chart the map)
- Khi nhận yêu cầu mơ hồ, thực hiện phỏng vấn `/ccba-grilling` để xác định **Điểm đích (Destination)**.
- Phác thảo bản đồ đầu tiên: Liệt kê các quyết định cần làm rõ, xác định các ticket unblocked ở biên giới (Frontier), đưa các phần chưa rõ ràng vào mục **Chưa xác định rõ (Not yet specified)**. **Nếu quá trình này không phát hiện vùng mờ (fog) nào** — lộ trình đến đích đã hoàn toàn rõ ràng — bạn không cần lập bản đồ Wayfinder. Hãy dừng lại và đề xuất thực hiện trực tiếp.
- Tạo các ticket con unblocked. Nếu sử dụng tracker thật, hãy thiết lập liên kết chặn bản địa (native dependency) của tracker (ví dụ: native blocking của GitHub/GitLab). Chỉ fallback sang ghi văn bản `Blocked by: #ID` khi tracker không hỗ trợ.
- **Tiêu chí hoàn thành:** Đã phác thảo xong bản đồ Wayfinder đầu tiên với đầy đủ các mục (Destination, Notes, Decisions so far, Not yet specified, Out of scope) và khởi tạo các ticket unblocked ở biên giới.

### Bước 2: Thực thi giải quyết Ticket (Work through the map)
- Chọn ticket unblocked đầu tiên ở **Biên giới (Frontier)** — là các ticket mở, chưa có assignee và không bị chặn bởi bất kỳ ticket mở nào khác.
- **Đăng ký nhận việc (Claiming):** Bắt buộc tự gán mình làm Assignee trên ticket **trước khi làm bất kỳ việc gì** để các Agent chạy song song khác biết và bỏ qua. Ticket mở và không có assignee được coi là chưa được nhận.
- Thực thi giải quyết ticket (chạy tối đa 1 ticket mỗi phiên).
- Sau khi có câu trả lời: post bình luận chứa câu trả lời lên ticket, **đóng (close)** ticket, cập nhật kết quả vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ, đồng thời chuyển các phần sương mù đã rõ ràng ở mục *Not yet specified* thành các ticket unblocked mới.
- **Tiêu chí hoàn thành:** Đã gán Assignee, giải quyết xong ticket chọn lựa, cập nhật kết quả vào mục Decisions so far và cập nhật các ticket mới trên bản đồ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
