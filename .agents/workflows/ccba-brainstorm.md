---
description: Khởi động phiên thảo luận ý tưởng và chuẩn bị tài liệu đầu vào tại input_documents/
command: /ccba-brainstorm [-- <topic_id>]
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
disable-model-invocation: true
---
# CCBA Brainstorming & Ingestion Workflow

> **Nguồn gốc:** Cấu trúc tương tác luân phiên (Hybrid Rhythm, Deferred Judgment, Party Mode) được học hỏi từ nguyên tắc của `brainstorm-coach` bởi Lưu Trọng Hiếu (License: All Rights Reserved - Adapted patterns only).

Workflow này giúp khởi chạy một phiên thảo luận ý tưởng, tự động quét và phân loại tài liệu đầu vào tại thư mục nháp `input_documents/`, đồng thời kích hoạt các hướng dẫn phân tích đặc thù theo từng chủ đề nghiệp vụ.

## Các bước thực hiện của Agent

### 1. Đọc cấu hình và Xử lý tham số (Config & Routing)
Agent bắt buộc phải đọc và gộp cấu hình các chủ đề từ hai nguồn:
1. **Mặc định từ Hub:** Đọc cấu hình mặc định tại [brainstorm_topics.yaml](resources/brainstorm_topics.yaml).
2. **Cục bộ từ Spoke:** Kiểm tra sự tồn tại của tệp cấu hình cục bộ tại `.md/knowledge/brainstorm_topics.yaml`. Nếu có, đọc và gộp (merge) với cấu hình mặc định (tập tin cục bộ được phép ghi đè các chủ đề trùng `topic_id` hoặc khai báo thêm chủ đề mới).

**Xử lý tham số Bypass:** Agent phân tích câu lệnh kích hoạt để phát hiện tham số truyền sau ký tự `--`:
* **Nếu có tham số trùng khớp `topic_id`:** Bypass — lập tức di chuyển sang **Bước 3** để nạp Kỹ năng và chuyển đổi tài liệu, bỏ qua Bước 2 (Quét) và Menu chọn.
* **Nếu tham số không trùng khớp:** In cảnh báo `⚠️ Chủ đề '[tham-so]' không tồn tại trong cấu hình.` và chuyển sang **Bước 2**.
* **Nếu không có tham số:** Chạy tiếp **Bước 2** thông thường.

*Tiêu chí hoàn thành:* Agent đã nạp cấu hình từ ít nhất một nguồn, in ra cấu trúc các chủ đề khả dụng, và quyết định rẽ nhánh chính xác.

---

### 2. Quét tài liệu và Chọn chủ đề (Scan & Select)
Quét toàn bộ danh sách tệp tin nằm trong thư mục [input_documents/](../../input_documents/):
* In bảng danh sách tệp tin phát hiện được kèm dung lượng (KB/MB).
* Đọc lướt nội dung (skimming) và so khớp từ khóa của các tệp với danh sách `keywords` của các chủ đề trong cấu hình để tự động đề xuất chủ đề phù hợp nhất.
* Hiển thị danh sách tất cả các chủ đề khả dụng cho người dùng lựa chọn. Chờ người dùng xác nhận chủ đề hoặc yêu cầu đổi sang chủ đề khác.

*Tiêu chí hoàn thành:* Người dùng đã phản hồi lựa chọn chủ đề từ danh sách và Agent đã xác nhận chủ đề được kích hoạt.

---

### 3. Chuyển đổi định dạng và Nạp Kỹ năng (Ingestion & Skill Activation)
Sau khi chủ đề được xác nhận, Agent tiến hành:
1. **Chuyển đổi tài liệu:** Chuyển đổi theo quy trình `/ccba-convert-markdown` — tham khảo skill [markdown-document-processing](../skills/markdown-processing/SKILL.md) cho quy tắc routing theo `project.mode`.
   * Đối với các tệp nhẹ `< 5MB` (`.docx`, `.txt`): Tự động chuyển đổi sang Markdown.
   * Đối với các tệp nặng `> 5MB` (PDF bản vẽ, Excel lớn): In cảnh báo, lập bảng tóm tắt metadata và chỉ convert chi tiết khi thảo luận đi sâu vào tệp đó.
2. **Nạp Kỹ năng:** Nạp toàn bộ các kỹ năng nghiệp vụ được chỉ định trong thuộc tính `required_skills` của chủ đề được chọn.

*Tiêu chí hoàn thành:* Toàn bộ các tệp nhẹ đã được chuyển đổi sang Markdown, và các kỹ năng nghiệp vụ tương ứng đã được nạp thành công.

---

### 4. Áp dụng Guidelines và Khởi động Brainstorming
In ra danh sách các chỉ dẫn thảo luận đặc thù (`guidelines`) của chủ đề đã chọn, sau đó bắt đầu phiên trao đổi hai chiều tuân thủ các quy tắc tương tác dưới đây.

*   **Gợi ý kỹ thuật:** Tham khảo [brainstorm_techniques.md](resources/brainstorm_techniques.md) để đề xuất kỹ thuật brainstorm phù hợp với chủ đề (SCAMPER, Reversal, Question Storming, v.v.). Để người dùng chọn hoặc đề xuất 1-2 technique kèm lý do.

**Quy tắc tương tác (Hybrid Rhythm):** Mỗi vòng brainstorm tuân thủ 4 nhịp:
1. **Prompt** — Agent đặt **đúng 1 câu hỏi** mở liên quan đến chủ đề. Luôn hỏi duy nhất 1 câu mỗi lượt để kích thích sự sáng tạo.
2. **User first** — Chờ người dùng trả lời. Bắt buộc giữ **nguyên văn** (verbatim) mọi câu chữ của người dùng với tag `(user)`.
3. **AI Build** — Agent bổ sung 2-4 ý tưởng mới với tag `(AI)`, xây dựng trên ý tưởng người dùng vừa nêu (yes-and), không thay thế.
4. **Return floor** — Kết thúc bằng **đúng 1 câu hỏi tiếp theo** để trả quyền điều khiển về người dùng.

*   **Deferred Judgment:** Trong giai đoạn phát tán ý tưởng, Agent chỉ đóng vai trò ghi nhận và mở rộng ý tưởng; bảo lưu toàn bộ việc đánh giá tính khả thi và xếp hạng cho đến giai đoạn Tổng hợp (mọi ý tưởng được ghi nhận bình đẳng).
*   **Energy Checkpoint:** Sau mỗi 3-4 vòng trao đổi, Agent chủ động hỏi: tiếp tục hướng hiện tại, đổi góc nhìn/kỹ thuật, hay chuyển sang tổng hợp kết quả?
*   **Nghiên cứu bổ sung:** Khi phát sinh nhu cầu nghiên cứu chuyên sâu (tài liệu lớn, API bên thứ ba, so sánh VBPL), kích hoạt `/ccba-research` chạy song song.

*Tiêu chí hoàn thành:* Các chỉ dẫn và quy tắc tương tác đã hiển thị đầy đủ, phiên brainstorming đã bắt đầu với vòng Hybrid Rhythm đầu tiên (Agent đặt câu hỏi mở đầu tiên).

---

### 5. Tổng hợp và Ghi nhận Phiên (Convergence & Session Document)
Khi người dùng yêu cầu tổng hợp (hoặc sau Energy Checkpoint chọn "tổng hợp"), Agent chuyển sang giai đoạn convergence:
1. **Nhóm phân loại:** Gom các ý tưởng đã thu thập thành 3-5 nhóm chủ đề tự nhiên.
2. **Xếp hạng:** Yêu cầu người dùng chọn 3-5 ý tưởng ưu tiên nhất. Agent không tự xếp hạng thay.
3. **Action items:** Chuyển các ý tưởng được chọn thành bước hành động cụ thể.
4. **Session Document:** Tạo artifact Markdown trong thư mục workspace hiện tại ghi nhận toàn bộ phiên với cấu trúc:
   - **Intake:** Chủ đề, ràng buộc, ngày tháng
   - **Ý tưởng phát tán:** Liệt kê mọi ý tưởng với tag `(user)` hoặc `(AI)`, giữ nguyên văn
   - **Nhóm phân loại:** Bảng phân nhóm
   - **Ưu tiên:** Top ý tưởng được chọn
   - **Action items:** Bước tiếp theo

*Tiêu chí hoàn thành:* Artifact Session Document đã được tạo và hiển thị cho người dùng.

---

### 6. Party Mode (Tùy chọn — Multi-role Ideation)
Khi người dùng yêu cầu "nhiều góc nhìn", "phản biện ý tưởng", hoặc "party mode", Agent chuyển sang chế độ brainstorm đa vai:
1. Tạo 2-3 persona ảo phù hợp với chủ đề (ví dụ: khách hàng, đối thủ cạnh tranh, kỹ sư skeptic, nhà đầu tư).
2. Mỗi vòng: Agent phát biểu từ góc nhìn của từng persona, gắn tag rõ ràng (ví dụ: `(Khách hàng)`, `(Skeptic)`).
3. Người dùng vẫn giữ vai trò chính — persona bổ sung góc nhìn, không thay thế.
4. Kết thúc Party Mode khi người dùng yêu cầu hoặc sau Energy Checkpoint.

> **Phân biệt với `/ccba-grilling`:** Party Mode sinh ý tưởng từ nhiều góc nhìn. Grilling stress-test một kế hoạch đã có. Mục đích khác nhau.

*Tiêu chí hoàn thành:* Ít nhất 2 persona đã phát biểu và ý tưởng được ghi nhận vào Session Document, hoặc người dùng yêu cầu dừng/chuyển giai đoạn.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Config đã nạp và chủ đề đã được xác nhận.
*   [x] Tài liệu đầu vào đã chuyển đổi Markdown (nếu có).
*   [x] Guidelines và quy tắc Hybrid Rhythm đã hiển thị, phiên brainstorming đã bắt đầu.
*   [x] Khi kết thúc phiên: Session Document artifact đã được tạo với đầy đủ ý tưởng tagged `(user)` / `(AI)`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
