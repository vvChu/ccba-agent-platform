# ccba-to-questionnaire — Reference Guide (Async Discovery Questionnaire)

> **Mục đích & Ngữ cảnh sử dụng:** Chuyển hóa một quyết định hoặc vùng thông tin mà người dùng không thể tự trả lời một mình thành một **Bảng câu hỏi khảo sát bất đồng bộ (`to-questionnaire-<slug>.md`)** để gửi cho người nắm giữ tri thức còn thiếu.
> **Nguồn gốc:** Thích ứng từ `to-questionnaire` (`v1.3.2`) của Matt Pocock (MIT License), địa phương hóa theo quy ước lưu trữ `.md/knowledge/questionnaires/` của CCBA Platform.

---

## 1. Nguyên Tắc Cốt Lõi: "Grill the send, not the subject"

Khi người dùng vướng một quyết định thiết kế, pháp lý hoặc nghiệp vụ mà chỉ một người khác (chủ đầu tư, PM, chuyên gia bộ môn, kỹ sư vận hành) mới nắm câu trả lời:

- **Grill the send, not the subject (Phỏng vấn việc gửi, không phỏng vấn chủ đề):**
  - Chỉ phỏng vấn người dùng về **việc gửi bảng câu hỏi** — điều mà người dùng luôn trả lời được ngay: *Bảng câu hỏi này gửi cho ai?* và *Bạn cần thu về quyết định/dữ kiện gì từ họ?*
  - Các câu hỏi bên trong tài liệu xuất ra sẽ nhắm thẳng vào **khoảng trống (the gap)** giữa những gì người nhận biết và những gì người dùng cần để hành động tiếp.

---

## 2. Quy Trình Thực Hiện 3 Bước (Process)

### Bước 1: Hỏi Về Người Nhận (`Who is it going to?` — Đúng 1 Lượt)
- Hỏi người dùng trong **một lượt trao đổi duy nhất**: vai trò, lĩnh vực chuyên môn, và mối quan hệ công việc của người nhận đối với người dùng.
- Thông tin này quyết định giọng điệu (tone), thuật ngữ sử dụng và lượng bối cảnh tối thiểu cần đính kèm vào đầu bảng câu hỏi.
- **Tiêu chí hoàn thành:** Xác định rõ người nhận là ai và vùng tri thức nào họ đang nắm giữ mà người dùng chưa có.

### Bước 2: Hỏi Về Kết Quả Cần Thu Về (`What do you need back?` — Đúng 1 Lượt)
- Hỏi người dùng trong **một lượt trao đổi duy nhất**: danh sách cụ thể các quyết định hoặc dữ kiện mà người dùng không thể tự chốt và bắt buộc phải có từ người nhận.
- **Tiêu chí hoàn thành:** Có danh sách cụ thể các quyết định/dữ kiện mà sau khi nhận được phản hồi, người dùng có thể lập tức triển khai công việc tiếp theo.

### Bước 3: Soạn Thảo & Lưu Bảng Câu Hỏi (`Write the questionnaire`)
- Soạn các câu hỏi nhắm trúng khoảng trống từ Bước 1 và Bước 2 theo cấu trúc chuẩn bên dưới.
- Lưu tệp tại đường dẫn chuẩn của dự án: **`.md/knowledge/questionnaires/to-questionnaire-<slug>.md`** (với `<slug>` rút trích từ chủ đề) và báo cáo đường dẫn tệp cho người dùng.
- **Tiêu chí hoàn thành:** Tệp `.md/knowledge/questionnaires/to-questionnaire-<slug>.md` được tạo thành công và mọi hạng mục người dùng nêu ở Bước 2 đều được bao phủ bởi ít nhất một câu hỏi rõ ràng.

---

## 3. Cấu Trúc Chuẩn Của Tài Liệu Bảng Câu Hỏi (Document Structure)

1. **Sắp xếp câu hỏi quan trọng nhất lên đầu (Most-important-first):** Vì trao đổi bất đồng bộ thường chỉ có một lượt phản hồi duy nhất, hãy đặt các câu hỏi có tính quyết định (blocking decisions) lên trên cùng; khi có nhiều hơn 4–5 câu, gom nhóm dưới các tiêu đề `##` theo chủ đề.
2. **Tự đóng gói bối cảnh (Self-contained context):** Viết bằng ngôn ngữ nghiệp vụ của người nhận; đính kèm vừa đủ bối cảnh ở đầu mỗi câu hỏi kèm các lựa chọn/đánh đổi rõ ràng để người nhận có thể trả lời ngay mà không phải hỏi ngược lại.
3. **Mẫu trình bày (Template):**
   ```markdown
   # Bảng Câu Hỏi Làm Rõ: <Chủ đề>

   **Kính gửi:** <Vai trò / Tên người nhận>
   **Mục đích:** <1-2 câu nêu rõ quyết định hoặc công việc đang cần thông tin này để triển khai tiếp>

   ---

   ## 1. <Nhóm chủ đề ưu tiên cao nhất>

   ### Câu hỏi 1.1: <Câu hỏi ngắn gọn, đi thẳng vào quyết định cần chốt>
   - **Bối cảnh:** <1-2 câu giải thích tại sao cần chốt điểm này và các phương án đang cân nhắc>
   - **Phương án gợi ý (nếu có):**
     - [ ] Phương án A: ...
     - [ ] Phương án B: ...
   - **Phản hồi của anh/chị:**
     > *(Điền câu trả lời tại đây)*
   ```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
