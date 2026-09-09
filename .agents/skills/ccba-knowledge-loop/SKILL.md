---
name: ccba-knowledge-loop
description: Quy trình Vòng lặp Tri thức & Định hướng toàn trình (Recon → Brainstorm
  → Wayfinder → Exec)
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
bundle: _core
command: /ccba-knowledge-loop
triggers:
- knowledge-loop
- vòng lặp tri thức
- trinh sát thảo luận hoạch định
---
# Quy trình Vòng lặp Tri thức & Định hướng (/ccba-knowledge-loop)

Quy trình này hướng dẫn Agent cách kết hợp đồng bộ 4 kỹ năng cốt lõi của CCBA Agent Services Platform: [YouTube-Learn](../ccba-youtube-learn/SKILL.md) (Trinh sát tri thức video), [Research](../ccba-research/SKILL.md) (Nghiên cứu ngầm), [Brainstorm](../ccba-ask/references/brainstorm_templates.md) (Hội chẩn giải pháp) và [Wayfinder](../ccba-wayfinder/SKILL.md) (Lập lộ trình) để giải quyết một bài toán kỹ thuật/nghiệp vụ lớn và mơ hồ (Foggy Problem) mà không gây block phiên làm việc hoặc làm tràn ngữ cảnh (token bloating).

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)

Quy trình chỉ được coi là thực thi thành công khi đáp ứng:
1. [x] Đã trinh sát và ingest tri thức nền tảng (Video/VBPL/Code) vào Knowledge Base của dự án.
2. [x] Đã tổ chức brainstorm để thống nhất giải pháp thô và tạo Session Document chứa các Action Items.
3. [x] Đã lập Bản đồ định hướng (`map.md`) thông qua Wayfinder với Điểm đích (Destination) và các Frontier Tickets.
4. [x] Các ticket Research được giao cho subagent chạy ngầm tự động và cập nhật kết quả ngược lại bản đồ tuần tự.

## 🔒 Giao thức Tác quyền Duy nhất (Single-Writer Protocol — ADR 0053)
- **Tác tử Nhạc trưởng (Orchestrator):** Agent chính là thực thể duy nhất có quyền ghi nhận tài liệu chính thức vào Knowledge Base và cập nhật bản đồ định hướng `map.md`.
- **Tác tử Nghiên cứu (Subagents):** Hoạt động ở chế độ Read-Only Sandbox, chỉ xuất kết quả nháp và báo cáo vào thư mục scratch (`.md/knowledge/research_and_studies/` hoặc `.system_generated/scratch/`). Tuyệt đối không can thiệp vào các tệp quy trình hoặc cấu hình hệ thống.

---

## 🛠️ Hướng dẫn thực thi các Phase

### Phase 1: Trinh sát & Thu thập Tri thức Sơ cấp (Reconnaissance)
Khi đối mặt với yêu cầu mới hoặc vùng tri thức chưa được định hình rõ ràng:
1. **Bóc tách video/bài giảng:** Agent chạy [/ccba-youtube-learn](../ccba-youtube-learn/SKILL.md) trên các video hướng dẫn của chuyên gia, webinar công nghệ hoặc seminar tập huấn liên quan để thu thập tri thức thực hành và các slide tĩnh.
   * *Đầu ra:* `notes_concept_[video_id].md` và thế giới quan `notes_worldview_[video_id].md`.
2. **Nghiên cứu ngầm tài liệu sơ cấp:** Agent chính kích hoạt [/ccba-research](../ccba-research/SKILL.md) để spawn subagent chạy ngầm quét các văn bản pháp lý (VBPL), API docs của bên thứ ba, hoặc cấu trúc code hiện có.
   * *Đầu ra:* File báo cáo `.md/knowledge/research_and_studies/research_[chủ_đề]_[timestamp].md`.
3. **Đọc và nạp ngữ cảnh:** Agent chính nạp các tài liệu được sinh ra ở trên vào thư mục tri thức nháp của dự án để chuẩn bị làm ngữ cảnh cho Phase tiếp theo.

- **Tiêu chí hoàn thành:** Toàn bộ tài liệu bóc tách từ video (`notes_concept_[video_id].md`) và báo cáo nghiên cứu ngầm (`research_[chủ_đề]_[timestamp].md`) hiện diện đầy đủ trong thư mục dự án và được nạp vào ngữ cảnh của Agent chính.

---

### Phase 2: Hội chẩn & Sáng tạo Phương án (Brainstorming)
Sau khi có dữ liệu trinh sát, Agent cùng User thống nhất phương án triển khai thô:
1. **Nạp tri thức:** Kích hoạt [/ccba-ask (brainstorm)](../ccba-ask/references/brainstorm_templates.md). Đảm bảo các ghi chú và báo cáo nghiên cứu ở Phase 1 nằm trong thư mục `input_documents/` để làm nền tảng tri thức.
2. **Hybrid Rhythm:** Thực hiện thảo luận hai chiều tuân thủ nghiêm ngặt 4 nhịp:
   * **Prompt:** Agent đặt đúng 1 câu hỏi mở.
   * **User first:** Chờ user trả lời, giữ nguyên văn với tag `(user)`.
   * **AI Build:** AI bổ sung 2-4 ý tưởng mới với tag `(AI)` xây dựng trên ý tưởng của user (Yes-and).
   * **Return floor:** Trả quyền điều khiển kèm đúng 1 câu hỏi mở tiếp theo.
3. **Party Mode (Phản biện đa vai):** Kích hoạt Party Mode. Sử dụng thông tin từ tệp `notes_worldview.md` của diễn giả ở Phase 1 để tạo Persona ảo phản biện sắc nét các điểm yếu của phương án (ví dụ: *Persona "Kỹ sư Skeptic"* phản biện về tính khả thi, *Persona "Cảnh sát PCCC"* phản biện về tính pháp lý).
4. **Hội tụ:** Gom nhóm ý tưởng, nhờ user xếp hạng và ghi nhận Session Document chứa các **Action Items**.

- **Tiêu chí hoàn thành:** Người dùng đã xếp hạng các ý tưởng ưu tiên và Agent đã tạo thành công tệp Session Document ghi nhận Action Items trong thư mục dự án.

---

### Phase 3: Hoạch định & Thiết lập Bản đồ (Wayfinder Mapping)
Tổ chức các Action Items rời rạc thành một lộ trình có cấu trúc:
1. **Thiết lập bản đồ:** Kích hoạt [/ccba-wayfinder](../ccba-wayfinder/SKILL.md) để khởi tạo bản đồ định hướng tại `.md/knowledge/issues/<feature>/map.md`.
2. **Cấu trúc bản đồ:**
   * **Điểm đích (Destination):** Xác định rõ tiêu chí nghiệm thu hoàn thành của bài toán.
   * **Frontier Tickets:** Các ticket mở, sẵn sàng thực thi ngay và độc lập với các ticket khác. Phân loại rõ: *Research [AFK]*, *Prototype [HITL]*, *Grilling [HITL]*, *Task [HITL/AFK]*.
   * **Sương mù chiến trận / Chưa xác định rõ (Not yet specified):** Chỉ ghi nhận các vùng thông tin và quyết định đã rõ ràng; các phần chưa thể nhìn thấy sẽ được giữ lại trong mục này dưới dạng ghi chú phác thảo cho đến khi đủ thông tin unblock.
3. **Tham chiếu theo tên:** Mọi ticket đều phải có tên gọi và link Markdown cụ thể (Ví dụ: `[Đóng gói Mutex Lock](../ccba-wayfinder/SKILL.md)`).

- **Tiêu chí hoàn thành:** Bản đồ định hướng `map.md` được khởi tạo với mục Điểm đích (Destination) rõ ràng và ít nhất một Frontier ticket được tạo lập.

---

### Phase 4: Vận hành Thực thi Song song & Đóng gói Quyết định
Giải quyết các Frontier Tickets và mở rộng bản đồ:
1. **Phân phối AFK:** Với các ticket thuộc loại **Research [AFK]**, Agent chính kích hoạt [/ccba-research](../ccba-research/SKILL.md) để spawn subagent chạy ngầm xử lý, đồng thời tiếp tục nhận các yêu cầu khác từ người dùng trong khi subagent đang chạy.
2. **Tự động cập nhật:** Khi subagent nghiên cứu hoàn thành và xuất báo cáo (xác nhận file báo cáo thực sự tồn tại), Agent chính hấp thụ kết quả, đóng (close) ticket tương ứng, cập nhật vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ.
3. **Mở rộng biên giới:** Dựa trên kết quả vừa chốt, chuyển đổi các vùng mờ trong mục *Not yet specified* thành các ticket Frontier mới.
4. **Giải quyết vùng mờ đột xuất:** Nếu biên giới bản đồ gặp sương mù quá dày không thể tự quyết, Agent đề xuất chạy một phiên [/ccba-ask (brainstorm)](../ccba-ask/references/brainstorm_templates.md) mini với User để thống nhất hướng đi tiếp theo.

- **Tiêu chí hoàn thành:** Mọi ticket trên bản đồ được chuyển sang trạng thái đóng (closed), không còn Frontier ticket nào chưa giải quyết và lộ trình đạt tới Điểm đích hoàn toàn.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
