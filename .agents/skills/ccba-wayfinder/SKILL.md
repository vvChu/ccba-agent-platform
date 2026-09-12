---
name: ccba-wayfinder
description: Lập bản đồ định hướng để giải quyết các bài toán lớn/mơ hồ thông qua
  danh sách các ticket công việc.
bundle: _core
tier: kernel
disable-model-invocation: true
user-invocable: true
command: /ccba-wayfinder
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-wayfinder
- vạch đường
- bài toán mơ hồ
- foggy
- chia nhỏ bài toán
---
# Kỹ năng Định hướng Giải quyết Bài toán Mơ hồ (Wayfinder)

> **Nguồn gốc & Tham chiếu:** Kỹ năng được phát triển dựa trên mô hình *Wayfinder* của **Matt Pocock** (Latent Space interview: [The /wayfinder Skill: Navigating the “Fog of War” of Planning](https://www.latent.space/p/wayfinder-skill)) và được bản địa hóa, nâng cấp cho hệ sinh thái CCBA Agent Platform.

Kỹ năng này giúp thiết lập và vận hành **Bản đồ định hướng (Wayfinding Map)** để chia nhỏ một ý tưởng lớn, mơ hồ thành các ticket điều tra cụ thể, giải quyết từng vấn đề một theo cơ chế *Sương mù chiến trận (Fog of War)* cho đến khi lộ trình đến đích hoàn toàn rõ ràng.

---

## 🧭 Phân Định Ranh Giới: `/ccba-grilling` vs `/ccba-wayfinder`

* **Dùng `/ccba-grilling`:** Khi bài toán có thể giải quyết trọn vẹn trong **một phiên duy nhất (Single Session)**, lộ trình cơ bản đã thấy trước mắt, chỉ cần chất vấn Socrates để chốt chi tiết thiết kế.
* **Dùng `/ccba-wayfinder`:** Khi con đường phía trước còn **hoàn toàn mờ mịt (Multi-session Fog of War)**, chưa biết bắt đầu từ đâu, cần chia nhỏ thành các phiên độc lập để nghiên cứu, thử nghiệm và giải mã dần dần.

---

## 🗣️ Ngôn Ngữ Dẫn Đường (Leading Words & Ubiquitous Language)

Để tránh Agent bị ảo giác và nhầm lẫn ngữ cảnh, kỹ năng này quy chuẩn 3 thực thể dẫn đường chính xác:

1. **`Map` (Bản đồ tổng thể):** Tệp tài liệu duy nhất lưu trữ toàn bộ trạng thái bài toán: các quyết định đã chốt, rìa biên giới, và các vùng còn nằm trong sương mù.
2. **`Ticket` (Công việc cụ thể):** Một đơn vị câu hỏi sắc nét, được đóng gói độc lập để giao cho đúng một phiên làm việc.
3. **`Session` (Phiên làm việc con):** Một phiên ~100K token giải quyết trọn vẹn 1 Ticket mà không làm ô nhiễm bộ nhớ của bản đồ tổng thể.

---

## 🎯 Nguyên tắc Hoạch định (Plan, don't do)

Wayfinder mặc định là quá trình lập kế hoạch (planning): mỗi ticket nhằm giải quyết một quyết định, và bản đồ hoàn thành khi lộ trình đã hoàn toàn rõ ràng — không còn gì cần quyết định thêm trước khi bắt tay vào thực hiện dự án. Mong muốn nhảy vào viết code/triển khai trực tiếp thường là tín hiệu cho thấy bạn đã chạm đến biên giới của bản đồ và đã đến lúc bàn giao (handoff). Một dự án có thể ghi đè nguyên tắc này trong phần Ghi chú (Notes) của bản đồ (kết hợp cả thực thi và định hướng) — nhưng nếu không có ghi chú đó, hãy tập trung tạo ra các Quyết định (decisions) chứ không phải Thành phẩm (deliverables).

---

## 🏷️ Nguyên tắc Tham chiếu theo Tên (Refer by name)

Mỗi bản đồ và ticket đều có tên gọi cụ thể. Trong mọi báo cáo hoặc nhật ký giao tiếp, **bắt buộc** phải gọi tên đầy đủ của ticket (nhúng liên kết tương ứng) thay vì chỉ dùng số hiệu hoặc mã định danh (Ví dụ: dùng `[Đóng gói Mutex Lock](https://github.com/...)` hoặc link GitHub `#42` thay vì chỉ viết ngắn gọn).

---

## 🗺️ Cấu trúc Bản đồ (The Map)

Bản đồ có thể lưu dưới dạng file Markdown cục bộ (mặc định tại `.md/wayfinder/<feature>/map.md` hoặc `.md/knowledge/issues/<feature>/map.md`) hoặc dạng Issue trên Issue Tracker của kho lưu trữ (gắn nhãn `wayfinder:map`). Cấu trúc bản đồ gồm các phần chính:

1. **Điểm đích (Destination):** Mô tả cụ thể trạng thái hoàn thành của toàn bộ bài toán. Điểm đích này cố định phạm vi (scope) của bản đồ.
2. **Ghi chú (Notes):** Các lưu ý đặc biệt, các kỹ năng bổ trợ cần nạp.
3. **Quyết định đã chốt (Decisions so far):** Nhật ký ghi nhận kết quả của các ticket đã giải quyết (chứa tên ticket, link và tóm tắt 1 dòng).
4. **Sương mù chiến trận / Chưa xác định rõ (Not yet specified):** Bản đồ cố tình không đầy đủ: không vẽ những gì chưa thể nhìn thấy. Nơi ghi nhận sơ lược các quyết định dự kiến sẽ tới nhưng chưa đủ sắc nét để tạo ticket (do phụ thuộc vào các ticket khác đang mở).
   - **Quy tắc Kiểm thử Sương mù (Fog vs. Ticket Test):** Tiêu chí phân định là *khả năng phát biểu câu hỏi sắc nét* chứ không phải *khả năng trả lời ngay*. Nếu câu hỏi đã có thể phát biểu chính xác $\rightarrow$ Tạo Ticket ngay (dù đang bị chặn); Nếu chỉ mới dừng lại ở vùng mờ chưa rõ dạng câu hỏi $\rightarrow$ Ghi nhận ở mục *Not yet specified*.
5. **Ngoài phạm vi (Out of scope):** Danh sách các tác vụ hoặc quyết định đã bị chủ động loại trừ khỏi phạm vi nỗ lực hiện tại. Nếu một ticket đang chạy bị phát hiện là nằm ngoài điểm đích, **đóng ticket đó lại** và ghi nhận lý do tại đây kèm link ticket.

---

## 🎫 Phân loại Ticket (Ticket Types)

Mỗi ticket con đại diện cho một câu hỏi cần làm rõ, tương ứng với một phiên làm việc khoảng 100K tokens của Agent. Mỗi ticket thuộc loại **HITL** (cộng tác trực tiếp với con người) hoặc **AFK** (Agent tự chủ thực hiện):

* **Research (Nghiên cứu) [AFK]:** Đọc tài liệu, API bên ngoài, hoặc tri thức cục bộ. Đầu ra là tệp Markdown tóm tắt. Dùng khi cần tri thức nằm ngoài codebase hiện tại.
* **Prototype (Mẫu thử) [HITL]:** Tạo nhanh một mẫu thử thô qua kỹ năng `/ccba-implement` để phản hồi trực quan. Dùng khi câu hỏi cốt lõi là "giao diện trông như thế nào" hoặc "hành vi hoạt động ra sao".
* **Grilling (Chất vấn) [HITL]:** Phỏng vấn chuyên sâu từng câu hỏi một với Kỹ sư sử dụng kỹ năng `/ccba-grilling`.
* **Task (Tác vụ) [HITL hoặc AFK]:** Các công việc thực thi thủ công cần phải hoàn thành để unblock một quyết định (ví dụ: xin quyền truy cập, config tài khoản, dump dữ liệu mẫu). Đây là loại duy nhất thực thi hành động ("do") chứ không phải chốt quyết định ("decide"). Agent tự chạy (AFK) hoặc cung cấp checklist cụ thể cho người dùng (HITL).

---

## 🔄 Quy trình Vận hành (Workflow)

### Bước 1: Khởi lập bản đồ (Chart the map)
- Khi nhận yêu cầu mơ hồ, thực hiện phỏng vấn `/ccba-grilling` để xác định **Điểm đích (Destination)**.
- Phác thảo bản đồ đầu tiên: Liệt kê các quyết định cần làm rõ, xác định các ticket unblocked ở biên giới (Frontier), đưa các phần chưa rõ ràng vào mục **Chưa xác định rõ (Not yet specified)**. **Nếu quá trình này không phát hiện vùng mờ (fog) nào** — lộ trình đến đích đã hoàn toàn rõ ràng — bạn không cần lập bản đồ Wayfinder. Hãy dừng lại và đề xuất thực hiện trực tiếp qua `/ccba-implement` hoặc `/ccba-tdd`.
- Tạo các ticket con unblocked. Nếu sử dụng tracker thật, hãy thiết lập liên kết chặn bản địa (native dependency) của tracker (ví dụ: native blocking của GitHub/GitLab).
- **Kích hoạt Sub-agent nghiên cứu song song (Parallel Research Dispatch):** Đối với các ticket loại `Research [AFK]` vừa khởi tạo tại Biên giới, Agent khởi chạy ngay sub-agent `/ccba-research` dưới nền để tự động thu thập tài liệu/API song song trong khi hoàn tất phác thảo bản đồ.
- **Tiêu chí hoàn thành:** Đã phác thảo xong bản đồ Wayfinder đầu tiên với đầy đủ các mục (Destination, Notes, Decisions so far, Not yet specified, Out of scope), khởi tạo các ticket unblocked ở biên giới và kích hoạt sub-agent nghiên cứu ngầm nếu có.

### Bước 2: Thực thi giải quyết Ticket (Work through the map)
- Chọn ticket unblocked đầu tiên ở **Biên giới (Frontier)** — là các ticket mở, chưa có assignee và không bị chặn bởi bất kỳ ticket mở nào khác.
- **Đăng ký nhận việc (Claiming):** Bắt buộc tự gán mình làm Assignee trên ticket **trước khi làm bất kỳ việc gì** để các Agent chạy song song khác biết và bỏ qua.
- Thực thi giải quyết ticket (chạy tối đa 1 ticket mỗi phiên).
- Sau khi có câu trả lời: post bình luận chứa câu trả lời lên ticket, **đóng (close)** ticket, cập nhật kết quả vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ, đồng thời chuyển các phần sương mù đã rõ ràng ở mục *Not yet specified* thành các ticket unblocked mới.
- **Tiêu chí hoàn thành:** Đã gán Assignee, giải quyết xong ticket chọn lựa, cập nhật kết quả vào mục Decisions so far và cập nhật các ticket mới trên bản đồ.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
