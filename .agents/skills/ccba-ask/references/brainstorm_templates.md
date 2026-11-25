# ccba-brainstorm — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Khung mẫu quy trình động não phát tán ý tưởng (Hybrid Rhythm, Deferred Judgment, Party Mode) và hội tụ có kiểm chứng cho Chế độ B của `/ccba-ask`.

---

# CCBA Brainstorming & Ingestion Workflow

> **Nguồn gốc:** Cấu trúc tương tác luân phiên (Hybrid Rhythm, Deferred Judgment, Party Mode) được thích ứng từ nguyên tắc của `brainstorm-coach` bởi Lưu Trọng Hiếu (Adapted patterns only).

Quy trình này khởi chạy phiên thảo luận ý tưởng có cấu trúc, tiếp nhận linh hoạt nguồn đầu vào (URL YouTube, tệp ghi chú ngoài, hoặc thư mục tùy chọn `input_documents/`), nạp kỹ năng chuyên đề và xuất *Session Document* sau khi người dùng xác nhận.

> **Ngoại lệ ghi tệp duy nhất:** Tuân thủ khóa chỉ đọc của `/ccba-ask`, trong toàn bộ Chế độ B Agent **chỉ được ghi tệp *Session Document* tại Bước 5 sau khi người dùng xác nhận chuyển sang tổng hợp**.

## Các bước thực hiện của Agent

### Bước 1: Đọc cấu hình & Nhận diện Đầu vào Trực tiếp (Config & Inline Input Routing)
Agent bắt buộc đọc và gộp cấu hình chủ đề từ hai nguồn:
1. **Mặc định từ Hub:** Đọc cấu hình mặc định tại [brainstorm_topics.yaml](../resources/brainstorm_topics.yaml).
2. **Cục bộ từ Spoke:** Kiểm tra tệp `.md/knowledge/brainstorm_topics.yaml`. Nếu có, đọc và gộp (tệp cục bộ được ghi đè các chủ đề trùng `topic_id` hoặc bổ sung chủ đề mới).

**Xử lý đầu vào trực tiếp & tham số Bypass:**
* **URL YouTube trong câu lệnh:** Điều phối bóc tách nội dung qua [`/ccba-youtube-learn`](../../ccba-youtube-learn/SKILL.md) (đúng seam video; **không** nạp URL YouTube vào `input_documents/` hay `/ccba-markdown-document-processing`), sau đó chuyển thẳng sang **Bước 4** với chủ đề phù hợp nhất.
* **Đường dẫn ghi chú/tài liệu `.md` hoặc `.txt` bên ngoài:** Đọc trực tiếp tại chỗ để nắm ngữ cảnh (không bắt buộc sao chép vào `input_documents/`), sau đó chuyển thẳng sang **Bước 4**.
* **Tham số sau ký tự `--` trùng `topic_id`:** Bypass Bước 2, đi thẳng sang **Bước 3** (nếu có tài liệu văn phòng cần chuyển đổi) hoặc **Bước 4**. Nếu không trùng khớp, in cảnh báo `⚠️ Chủ đề '[tham-so]' không tồn tại trong cấu hình.` và chạy Bước 2.
* **Không có đầu vào trực tiếp và không có tham số:** Chạy **Bước 2**.

- **Tiêu chí hoàn thành:** Agent đã nạp cấu hình chủ đề, định tuyến đúng nguồn đầu vào (YouTube / note tại chỗ / `input_documents/`), và xác định rõ bước kế tiếp.

---

### Bước 2: Quét `input_documents/` (Tùy chọn) & Chọn Chủ đề
Chỉ thực hiện khi phiên chưa có đầu vào trực tiếp từ Bước 1 (hoặc người dùng yêu cầu quét thư mục nháp):
* Nếu thư mục `input_documents/` tồn tại và có tệp: in bảng danh sách tệp kèm dung lượng (KB/MB), đọc lướt để khớp `keywords` và đề xuất chủ đề phù hợp nhất.
* Nếu không có `input_documents/`: bỏ qua bước quét tệp mà không báo lỗi; hiển thị danh sách chủ đề khả dụng để người dùng chọn (hoặc nhận thẳng chủ đề người dùng nêu).

- **Tiêu chí hoàn thành:** Chủ đề brainstorm đã được người dùng xác nhận (hoặc tự định danh rõ ràng từ đầu vào trực tiếp ở Bước 1).

---

### Bước 3: Chuyển đổi Tài liệu Văn phòng/PDF & Nạp Kỹ năng (Ingestion & Skill Activation)
Chỉ chạy phần chuyển đổi tệp khi có tài liệu văn phòng (`.docx`, PDF) hoặc tệp `.txt` nằm trong lượt quét tùy chọn `input_documents/` cần chuẩn hóa sang Markdown:
1. **Chuyển đổi tài liệu:** Áp dụng quy trình [`/ccba-markdown-document-processing`](../../ccba-markdown-document-processing/SKILL.md) theo `project.mode`:
   * Tệp nhẹ `< 5MB` (`.docx`, `.txt` trong `input_documents/`): tự động chuyển đổi sang Markdown.
   * Tệp nặng `> 5MB` (PDF bản vẽ, Excel lớn): in cảnh báo, lập bảng tóm tắt metadata và chỉ xử lý sâu khi thảo luận chạm tới tệp đó.
   *(Nhắc lại: URL YouTube đi qua `/ccba-youtube-learn`; đường dẫn note `.md`/`.txt` ngoài đọc trực tiếp tại chỗ.)*
2. **Nạp Kỹ năng:** Đọc lướt/nạp các kỹ năng nghiệp vụ liên quan trong `required_skills` của chủ đề khi bối cảnh phiên thực sự cần.

- **Tiêu chí hoàn thành:** Tài liệu văn phòng trong `input_documents/` (nếu có) đã sẵn sàng ở dạng Markdown và các kỹ năng nền tảng của chủ đề đã được định vị.

---

### Bước 4: Áp dụng Guidelines & Khởi động Brainstorming
In ra danh sách các chỉ dẫn thảo luận đặc thù (`guidelines`) của chủ đề đã chọn, sau đó khởi chạy phiên trao đổi hai chiều:

* **Gợi ý kỹ thuật:** Tham khảo [brainstorm_techniques.md](./brainstorm_techniques.md) để đề xuất 1–2 kỹ thuật phù hợp (SCAMPER, Reversal, **Problem-First** nếu người dùng đưa giải pháp định sẵn, **Reframe** nếu cần nâng cấp hệ thuật ngữ chuyên gia).

**Quy tắc tương tác (Hybrid Rhythm):** Mỗi vòng brainstorm tuân thủ 4 nhịp:
1. **Prompt** — Agent đặt **đúng 1 câu hỏi mở** liên quan đến chủ đề để kích thích tư duy.
2. **User first** — Chờ người dùng trả lời. Bắt buộc giữ **nguyên văn** (verbatim) câu chữ của người dùng với tag `(user)`.
3. **AI Build** — Agent bổ sung 2–4 ý tưởng mới với tag `(AI)`, xây dựng nối tiếp ý tưởng người dùng (`yes-and`), không thay thế.
4. **Return floor** — Kết thúc bằng **đúng 1 câu hỏi mở tiếp theo** để trả quyền điều khiển cho người dùng.

* **Deferred Judgment:** Trong pha phát tán, ghi nhận bình đẳng mọi ý tưởng; giữ lại việc chấm điểm và loại trừ đến Bước 5 (trừ khi người dùng chủ động chọn kỹ thuật *Problem-First* để kiểm chứng giả định trước).
* **Energy Checkpoint:** Sau mỗi 3–4 vòng, chủ động hỏi: tiếp tục hướng hiện tại, đổi kỹ thuật/bật Party Mode, hay chuyển sang Bước 5 tổng hợp?
* **Nghiên cứu bổ sung:** Khi cần đối chiếu sâu tài liệu lớn, API ngoài hoặc VBPL, kích hoạt [`/ccba-research`](../../ccba-research/SKILL.md) ở chế độ chỉ đọc.

- **Tiêu chí hoàn thành:** Đã hiển thị guidelines + gợi ý kỹ thuật và đặt đúng 1 câu hỏi mở đầu tiên theo Hybrid Rhythm.

---

### Bước 5: Tổng hợp & Ghi nhận Phiên (Convergence & Session Document)
Chỉ chuyển sang bước này khi người dùng yêu cầu tổng hợp (hoặc chọn "tổng hợp" tại Energy Checkpoint):
1. **Nhóm phân loại:** Gom toàn bộ ý tưởng thành 3–5 nhóm chủ đề tự nhiên.
2. **Xếp hạng:** Mời người dùng chọn 3–5 ý tưởng ưu tiên nhất (Agent không tự xếp hạng thay).
3. **Action items:** Chuyển các ý tưởng được chọn thành bước hành động cụ thể kèm gợi ý kỹ năng kế tiếp ([`/ccba-wayfinder`](../../ccba-wayfinder/SKILL.md), [`/ccba-grilling`](../../ccba-grilling/SKILL.md), hoặc [`/ccba-to-spec`](../../ccba-to-spec/SKILL.md)).
4. **Session Document (Ngoại lệ ghi tệp sau khi user xác nhận):** Tạo tệp Markdown trong `.md/knowledge/` (hoặc artifact phiên) ghi nhận đầy đủ:
   - **Intake:** Chủ đề, nguồn đầu vào, ràng buộc, ngày tháng
   - **Ý tưởng phát tán:** Nguyên văn gắn tag `(user)` hoặc `(AI)`
   - **Nhóm phân loại & Ưu tiên:** Bảng gom nhóm và Top lựa chọn của người dùng
   - **Action items:** Bước chuyển tiếp cụ thể
5. **Khung Cược Trước & Chuyển tiếp Phản biện (Pre-Flight Conviction Handoff):** Ở cuối bản tổng hợp, xuất kèm khối 3 dòng cho phương án ưu tiên số 1 làm đầu vào trực tiếp cho [`/ccba-grilling`](../../ccba-grilling/SKILL.md), [`/ccba-wayfinder`](../../ccba-wayfinder/SKILL.md), hoặc [`/ccba-to-spec`](../../ccba-to-spec/SKILL.md):
   ```markdown
   🎯 Cược của tôi: [Giả thuyết / quyết định cốt lõi và mức độ tin tưởng X%]
   💣 Điểm gãy: [Điều kiện thực tế hoặc dữ liệu nào xảy ra sẽ chứng minh cược này sai]
   🔍 Câu hỏi ép cung AI: [Câu hỏi yêu cầu AI phản biện tìm lỗ hổng lớn nhất]
   ```

- **Tiêu chí hoàn thành:** Artifact Session Document đã được tạo (sau khi user xác nhận) kèm Khung Cược Trước 3 dòng trung lập.

---

### Bước 6: Party Mode (Tùy chọn — Multi-role Ideation)
Khi người dùng yêu cầu *"nhiều góc nhìn"*, *"phản biện ý tưởng"*, hoặc *"party mode"*:
1. Tạo 2–3 persona ảo phù hợp với chủ đề (ví dụ: khách hàng, kỹ sư skeptic, chuyên gia pháp lý/vận hành).
2. Mỗi vòng: mỗi persona phát biểu ngắn gọn, gắn tag rõ ràng (ví dụ: `(Khách hàng)`, `(Skeptic)`).
3. Người dùng vẫn giữ vai trò trung tâm — persona bổ sung góc nhìn, không thay thế quyết định.
4. Kết thúc Party Mode khi người dùng yêu cầu hoặc sau Energy Checkpoint.

> **Phân biệt với [`/ccba-grilling`](../../ccba-grilling/SKILL.md):** Party Mode phát tán ý tưởng từ nhiều vai trò; Grilling phỏng vấn xoáy để khóa thiết kế của một phương án đã chọn.

- **Tiêu chí hoàn thành:** Ít nhất 2 persona đã đóng góp góc nhìn và được ghi nhận vào phiên, hoặc người dùng chuyển sang Bước 5.

---

## Tiêu chí hoàn thành (Completion Criteria)

* [x] Cấu hình chủ đề đã nạp và nguồn đầu vào đã định tuyến đúng seam (YouTube $\to$ `/ccba-youtube-learn`, note ngoài $\to$ đọc tại chỗ, `.docx`/PDF $\to$ `/ccba-markdown-document-processing`).
* [x] Guidelines và quy tắc Hybrid Rhythm đã hiển thị, phiên động não đã bắt đầu.
* [x] Khi kết thúc phiên (sau xác nhận của người dùng): Session Document đã được tạo với đầy đủ ý tưởng gắn tag `(user)` / `(AI)` và Khung Cược Trước 3 dòng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
