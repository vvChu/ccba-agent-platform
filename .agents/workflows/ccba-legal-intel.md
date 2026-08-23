---
description: Workflow tư vấn và rà soát pháp luật xây dựng Việt Nam với RAG và Grounding
  Gate
disable-model-invocation: true
bundle: _consulting
command: /ccba-legal-intel
triggers:
- ccba-legal-intel
- crawl law
- diff law
- legal checklist
- thuvienphapluat
- tvpl
---
# Workflow: Tư Vấn & Rà Soát Pháp Luật Xây Dựng (/ccba-legal-intel)

> **Mô tả:** Workflow tự động cào, tra cứu RAG, đối chiếu và tư vấn giải đáp thắc mắc pháp lý xây dựng Việt Nam với cơ chế kiểm định trích dẫn nguồn bắt buộc (Grounding Gate).

## Các bước thực hiện của Agent

### 1. Tiếp nhận Câu hỏi & Nạp Sổ bộ (`legal_registry.yaml`)
- Nạp module `scripts/legal_rag_indexer.py` và đọc cơ sở dữ liệu pháp lý tại `.agents/skills/legal-document-tracker/resources/legal_registry.yaml`.
- Phân tích câu hỏi của người dùng để xác định các từ khóa trọng tâm (Luật Xây dựng, Nghị định QLCL, Giấy phép xây dựng, PCCC, Hợp đồng...).

---

### 2. Tra cứu RAG & Trích xuất Văn bản
- Chạy hàm `search_legal_registry(query, registry_path)` để tìm 3-5 văn bản pháp lý phù hợp nhất.
- Kiểm tra trạng thái vòng đời văn bản (Văn bản còn hiệu lực `current`, Hết hiệu lực `superseded`, hay Dự thảo `draft`).
- Trích xuất chính xác Điều, Khoản, Điểm điều luật liên quan.

---

### 3. Kiểm định Grounding Gate (`scripts/legal_grounding_gate.py`)
- Kiểm tra câu trả lời tư vấn với hàm `verify_legal_grounding(response_text, retrieved_docs)`.
- **Rào chắn:** Nếu câu trả lời thiếu trích dẫn nguồn dạng `[Short Name - Doc Number]` hoặc suy diễn không có căn cứ, Agent bắt buộc phải bổ sung trích dẫn hoặc gắn cảnh báo ungrounded.

---

### 4. Định dạng Đầu ra & Đính kèm Disclaimer
- Đặt trích dẫn nguồn chi tiết tại từng ý kiến tư vấn.
- Đính kèm tự động disclaimer chuẩn CCBA:

```markdown
---
⚠️ **Disclaimer:** Nội dung tư vấn trên được tự động trích xuất và kiểm định bằng AI Agent dựa trên Sổ bộ Pháp lý CCBA (`legal_registry.yaml`). Đây là thông tin tham khảo kỹ thuật, KHÔNG phải văn bản tư vấn pháp lý chính thức. Luôn cần chuyên gia pháp lý hoặc Luật sư xác nhận trước khi áp dụng vào dự án thực tế.
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
