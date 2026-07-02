# CCBA R&D Seminar 005: Xây dựng Kỹ năng AI Agent Chất lượng cao (Writing Great Agent Skills)

*   **Mã tài liệu:** `CCBA_RD_SEMINAR_005_Rev00-02.07.26-Writing_Great_Agent_Skills`
*   **Chủ đề:** Áp dụng Framework của Matt Pocock vào thiết kế & tối ưu hóa hệ thống kỹ năng trên CCBA Agent Services Platform.
*   **Ngày thực hiện:** 02.07.2026
*   **Người biên soạn:** AI Agent CCBA

---

## 1. Giới thiệu & Bối cảnh thảo luận

Khi số lượng kỹ năng (**skills**) trong hệ thống AI Agent tăng lên (CCBA hiện tại đã có hơn 40+ skills khác nhau), chúng ta đối mặt với hiện tượng **"Skill Hell"** (sự hỗn loạn về kỹ năng). Nếu không có một cấu trúc và bộ quy tắc chặt chẽ:
1.  Agent sẽ bị quá tải ngữ cảnh (**context bloat**), dẫn đến suy giảm trí thông minh và tăng chi phí token.
2.  Hành vi của Agent sẽ trở nên thiếu nhất quán và khó đoán định (**unpredictability**).
3.  Xuất hiện các bước trùng lặp, hướng dẫn dư thừa không làm thay đổi hành vi (**no-ops**).

Seminar này phân tích framework thiết kế kỹ năng của Matt Pocock để tìm ra các giải pháp tối ưu cho CCBA Agent Platform.

---

## 2. Tóm tắt Framework "Writing Great Agent Skills" (Matt Pocock)

Framework của Matt Pocock tập trung vào 4 trụ cột cốt lõi nhằm tối ưu tính **Predictability** (Khả năng dự đoán quy trình thực hiện của Agent):

```
                   ┌───────────────┐
                   │ PREDICTABILITY│
                   └───────▲───────┘
                           │
      ┌────────────┬───────┴────────┬────────────┐
      │            │                │            │
┌─────┴─────┐┌─────┴─────┐    ┌─────┴─────┐┌─────┴─────┐
│  TRIGGER  ││ STRUCTURE │    │ STEERING  ││  PRUNING  │
└───────────┘└───────────┘    └───────────┘└───────────┘
```

### A. Trigger (Cơ chế Kích hoạt)
Đánh giá chi phí ngữ cảnh (**context load**) so với chi phí nhận thức của người dùng (**cognitive load**):
*   **Model-invoked (Mô hình tự gọi):** Cần có `description` rõ ràng trong frontmatter để Agent tự nhận biết. Tốn context load vì mô tả luôn được nạp vào cửa sổ ngữ cảnh.
*   **User-invoked (Người dùng gọi):** Tắt khả năng tự gọi của mô hình bằng cách set `disable-model-invocation: true`. Tiết kiệm context load về 0, nhưng bắt buộc người dùng phải tự nhớ tên lệnh để gọi.
*   **Giải pháp Router Skill:** Khi số lượng user-invoked skills quá lớn, sử dụng một kỹ năng định tuyến (Router Skill) duy nhất làm cổng vào để Agent tự quét và hướng dẫn gọi các skill khác khi cần.

### B. Structure (Cấu trúc & Phân cấp thông tin)
Phân tách rõ ràng giữa hai loại thông tin trong một skill:
1.  **Steps (Các bước thực thi):** Quy trình hành động theo thứ tự tuần tự. Mỗi bước bắt buộc phải đi kèm với một **Completion Criterion** (tiêu chí hoàn thành) rõ ràng, có thể định lượng hoặc kiểm chứng cụ thể để tránh lỗi Agent kết thúc sớm (**premature completion**).
2.  **References (Tham chiếu):** Các quy tắc, bảng biểu, tài liệu tĩnh bổ trợ.
    *   *In-skill reference:* Đặt trực tiếp trong file `SKILL.md` (nếu ngắn gọn và cần thiết).
    *   *External reference:* Đẩy ra các tệp tin độc lập bên ngoài và sử dụng **Context Pointer** (đường dẫn liên kết) để Agent chỉ tải và đọc khi thực sự cần thiết, giữ cho file skill chính cực kỳ tối giản.

### C. Steering (Điều hướng & Dẫn dắt hành vi)
*   Sử dụng **Leading Words** (từ dẫn dắt mạnh mẽ) trong phần hướng dẫn để ép Agent suy nghĩ mạch lạc.
*   Bắt Agent phải thực hiện nhiều công việc điều tra thực tế (**legwork**) bằng cách chia nhỏ quy trình phức tạp thành các kỹ năng độc lập, che giấu các bước tiếp theo đằng sau tiêu chí hoàn thành của bước hiện tại.

### D. Pruning (Cắt tỉa & Tối ưu)
*   Duy trì duy nhất một nguồn sự thật (Single Source of Truth) để tránh trùng lặp thông tin giữa các file.
*   Thường xuyên rà soát cắt bỏ các hướng dẫn rác ("sediment") và các hướng dẫn thừa thãi không làm thay đổi hành vi thực tế của Agent ("no-ops").

---

## 3. Đối chiếu & Đánh giá Hiện trạng CCBA Agent Platform

### 3.1. Các điểm mạnh đã triển khai
1.  **Sử dụng mô hình Router Skill xuất sắc:** File [platform-loader/SKILL.md](../../.agents/skills/platform-loader/SKILL.md) và [catalog.yaml](../../.agents/skills/platform-loader/catalog.yaml) là ví dụ điển hình cho Router Skill. Nó giúp Agent biết được tất cả 40+ skills đang có mà không cần nạp toàn bộ chúng vào context ngay từ đầu.
2.  **Phân tách External Reference tốt:** Hệ thống CCBA đã chia thông tin thành các thư mục chuyên biệt như `.md/knowledge/` cho tài liệu nghiên cứu, `.md/legal_docs/` cho văn bản pháp lý thô và `.agents/rules/` cho các hiến pháp quy chuẩn. Agent liên kết đến chúng bằng context pointers dạng Markdown link `[tên](../../.md/legal_docs/)`.
3.  **Tách biệt Logic và Documentation:** Các kỹ năng phức tạp như `api-circuit-breaker` hay `append-only-logger` tách mã nguồn Python ra thư mục `resources/` hoặc `scripts/`, giữ cho file `SKILL.md` tập trung vào hướng dẫn sử dụng và nguyên lý vận hành.

### 3.2. Những điểm hạn chế cần cải tiến
1.  **Mô tả Kích hoạt (Descriptions) của các Skill còn dài dòng:**
    Nhiều skill của CCBA có phần `description` trong frontmatter rất dài và mang tính mô tả chung chung cho người dùng đọc thay vì hướng mục tiêu tối ưu cho LLM Parser. Điều này làm tăng context load không đáng có khi nạp catalog.
2.  **Thiếu Tiêu chí Hoàn thành (Completion Criteria) định lượng:**
    Các quy trình nghiệp vụ phức tạp của CCBA (như quét bản vẽ PCCC, lập danh mục checklist nghiệm thu) có ghi các bước thực hiện nhưng tiêu chí hoàn thành ở cuối mỗi bước còn mơ hồ (ví dụ: *"Kiểm tra lại toàn bộ bản vẽ và ghi nhận"*). Điều này dễ khiến Agent bị hoàn thành sớm hoặc bỏ sót chi tiết.
3.  **Hành vi Model-Invoked vs. User-Invoked chưa được phân loại triệt để:**
    Nhiều kỹ năng công cụ (utility skills) như `docx`, `pptx`, `excalidraw-diagram` hiện tại vẫn đang bật mặc định tự động kích hoạt bởi model (không có `disable-model-invocation: true`). Điều này khiến Agent bị phân tâm hoặc tự ý gọi chúng trong các tác vụ không liên quan.

---

## 4. Đề xuất Nâng cấp Hệ thống Kỹ năng CCBA

Nhóm nghiên cứu R&D đề xuất triển khai các hành động sau để tối ưu hóa CCBA Agent Platform:

### Đề xuất 1: Áp dụng Quy chuẩn Viết Mô tả tinh gọn (Pruning Descriptions)
*   **Hành động:** Thiết kế lại toàn bộ frontmatter `description` cho 40+ skills hiện có.
*   **Quy chuẩn mới:** Mô tả tối đa 150 ký tự, đưa "leading words" và trigger chính lên đầu. Gom tất cả các nhánh kích hoạt tương đương.
*   **Ví dụ cải tiến:**
    *   *Cũ:* "Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch pipelines. Tránh quota exhaustion, cascade failures, và infinite retry loops khi gọi AI Gateway hàng loạt." (185 ký tự)
    *   *Mới:* `circuit-breaker: Rate limiter + Circuit Breaker cho batch LLM API. Dùng khi gọi AI Gateway hàng loạt tránh quota exhaustion.` (118 ký tự)

### Đề xuất 2: Cưỡng chế Completion Criteria rõ ràng trong mọi Workflow & Skill Steps
*   **Hành động:** Bổ sung trường `## Tiêu chí hoàn thành (Completion Criteria)` ở cuối mỗi bước hoặc cuối file skill.
*   **Yêu cầu:** Tiêu chí phải kiểm chứng được (ví dụ: file log phải được ghi nhận, mã lỗi JSON phải xuất ra stderr, phải chạy lệnh kiểm định `validate_docs.py`...).

### Đề xuất 3: Phân loại triệt để User-Invoked và Model-Invoked
*   **Hành động:**
    *   Set `disable-model-invocation: true` cho toàn bộ các công cụ thuần túy định dạng (`docx`, `pptx`, `pdf`, `excalidraw-diagram`). Các công cụ này chỉ được kích hoạt khi người dùng gõ lệnh hoặc thông qua Router.
    *   Chỉ bật model-invoked cho các kỹ năng cốt lõi (như `ai-gateway-sdk`, `hybrid-rag-search`) mà Agent thực sự cần tự động gọi chéo trong logic xử lý của mình.

---

## 5. Câu hỏi Thảo luận mở (Brainstorming Prompts)

Để hoàn thiện kiến trúc kỹ năng thế hệ mới cho CCBA, chúng tôi kính đề xuất các vấn đề thảo luận sau:

1.  **Về việc chuyển đổi sang User-Invoked:** Chúng ta nên áp dụng `disable-model-invocation: true` cho những skill nào khác ngoài bộ công cụ định dạng? Việc này có ảnh hưởng đến khả năng "tự động hóa hoàn toàn" mà không cần người dùng can thiệp không?
2.  **Về Router Skill:** Hiện tại `platform-loader` đang là router thủ công. Chúng ta có nên xây dựng một Router Daemon tự động nạp/nhả ngữ cảnh (dynamic context swapping) để giải phóng hoàn toàn context window cho các tác vụ dài hơi không?
3.  **Về Completion Criteria:** Chúng ta có nên viết một script QC tự động quét các file `SKILL.md` để đảm bảo mỗi bước trong skill đều có thẻ checklist `- [ ]` hoặc tiêu chí hoàn thành được định nghĩa trước khi cho phép commit lên Hub không?

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
