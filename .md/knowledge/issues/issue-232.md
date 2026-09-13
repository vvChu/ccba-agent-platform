---
id: 232
title: "feat(rag): federated cross-spoke legal ground-truth query engine & mcp endpoint"
state: "closed"
labels:
  - "enhancement"
  - "completed"
assignee: "Antigravity AI Agent"
created_at: "2026-09-02T06:28:00Z"
updated_at: "2026-09-13T12:45:00Z"
closed_at: "2026-09-13T12:45:00Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
- Hiện tại toàn bộ kho tri thức pháp luật & quy chuẩn kỹ thuật xây dựng (OKF v2.4 Universal Agent-Centric) được đóng gói tập trung tại Spoke `ccba-legal-knowledge`.
- Các Spoke nghiệp vụ khác trong hệ sinh thái (như `2026-04 DH Viet Nhat`, `IDOP-CCBA-WAY`, `Zalo_Bot_Free`) khi cần tra cứu nhanh điều khoản quy phạm (khoảng cách an toàn PCCC, tải trọng gió, thủ tục cấp phép xây dựng) hiện phải tải toàn bộ kho dữ liệu hàng trăm MB về máy hoặc tra cứu chung chung qua LLM (dễ bị ảo giác).
- Cần một cơ chế tra cứu liên Spoke tinh gọn (**Zero-Bloat Federated RAG**) truy vấn trực tiếp kho tri thức pháp lý từ xa.

---

### 2. Đề xuất giải pháp (RFC Proposal):
Xây dựng Federated Legal Query Engine kết hợp giữa `ccba-ai` và `ccba-legal-intel`:
- **MCP Endpoint & CLI Service (`ccba_ai.mcp_server` / `ccba_legal.query`)**: Cung cấp tool tra cứu ngữ nghĩa `query_legal_ground_truth(query, document_type, top_k)`.
- **Hybrid Search Backend (BM25 + LiteLLM Embeddings + RRF Fusion)**: Truy vấn trực tiếp cây AST điều khoản `clauses.json` và bảng số liệu `tables/` từ Master Corpus hoặc Google Drive Cloud Vault mà không cần Spoke tải dữ liệu về máy.
- **Trích Dẫn Pháp Lý Xác Thực 100%**: Trả về kết quả kèm số hiệu điều khoản, liên kết văn bản và trích dẫn quy chuẩn gốc.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [x] Bổ sung tool tra cứu pháp lý `query_legal_ground_truth` trong Hub MCP Server và Python SDK.
- [x] Bất kỳ Spoke nào có cài đặt `ccba-ai` đều có thể gọi hàm tra cứu pháp lý trực tiếp.
- [x] Kết quả tra cứu đảm bảo độ trễ thấp (< 1s với cache cục bộ / LiteLLM server Spark) và chính xác 100% theo OKF v2.4.
- [x] Bổ sung test integration và kịch bản demo trong `tests/test_federated_rag.py`.
- [x] Thay thế chuỗi hardcode trong `search_vietnamese_laws` tại `packages/ccba-ai/src/ccba_ai/mcp_server.py` bằng `LegalKnowledgeEngine` (ADR 0035, ADR 0050, RULE-3.1).

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-02T06:40:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage).
> Xác nhận giải pháp Federated Zero-Bloat RAG và FastMCP Tool tra cứu kho pháp điển OKF v2.4 mang lại giá trị to lớn cho toàn bộ hệ sinh thái CCBA, giúp các Spoke nghiệp vụ không cần lưu bản sao dữ liệu cồng kềnh mà vẫn truy vấn chuẩn xác 100%.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Triển khai Federated Legal Ground-Truth Query Engine và tích hợp FastMCP tool `query_legal_ground_truth` trong `ccba-ai` & `ccba-legal-intel`.

### Hành vi hiện tại (Current behavior)
- Các Spoke phải tải toàn bộ kho `legal_docs` về máy để tra cứu, gây tốn dung lượng đĩa và nguy cơ dữ liệu bị lỗi thời (out-of-sync).
- FastMCP server trong `ccba-ai` chưa cung cấp tool tra cứu pháp lý từ xa có trích dẫn chuẩn hóa theo AST OKF v2.4.

### Hành vi mong muốn (Desired behavior)
- Thêm tool FastMCP `query_legal_ground_truth(query: str, domain: str = None, top_k: int = 5)` vào `packages/ccba-ai/src/ccba_ai/mcp_server.py`.
- Tích hợp hàm tra cứu Python `ccba_legal.query_ground_truth(...)` sử dụng Hybrid Search (BM25 + Semantic + RRF) trỏ tới Master Corpus / Cloud Vault.
- Trả về payload JSON có cấu trúc gồm: `clause_id`, `document_id`, `article_num`, `text_snippet`, `confidence_score`, `citation_url`.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `packages/ccba-ai/src/ccba_ai/mcp_server.py`: Tool `@mcp.tool() query_legal_ground_truth(...)`
- `packages/ccba-legal-intel/src/ccba_legal/federated_rag.py`: `FederatedLegalEngine`
- `packages/ccba-ai/src/ccba_ai/legal_knowledge.py`: Client-side query wrapper

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [x] Tool `query_legal_ground_truth` phản hồi truy vấn dưới 1.5s đối với các câu hỏi pháp lý phổ biến (PCCC, cấp phép xây dựng, nghiệm thu).
- [x] Định dạng trích dẫn chuẩn xác theo điều khoản OKF v2.4.
- [x] Test integration `test_federated_rag.py` pass 100%.
- [x] Triệt tiêu hoàn toàn chuỗi hardcode và vi phạm RULE-3.1 trong `search_vietnamese_laws` qua `LegalKnowledgeEngine`.

### Phạm vi loại trừ (Out of scope)
- Không lưu trữ cache persistent vượt quá 100MB tại Spoke cục bộ.

### Đề xuất chế độ thực thi (Recommended Execution Strategy)
- **Mức độ phức tạp**: Trung bình / Đa gói (`ccba-ai` + `ccba-legal-intel`)
- **Khuyến nghị thực thi**:
  - `[x]` 🟢 **Standard** (`/ccba-implement`): Triển khai tuần tự, scoped tests.
  - `[ ]` 🟣 **Deep Reasoning** (`/boost`): Điều tra chuyên sâu root-cause / phản biện đa vòng.
  - `[ ]` 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `/teamwork-preview`): Phân rã Seams và chạy đa tác nhân song song.

---

> **@Antigravity AI Agent (Resolution)** (2026-09-13T12:45:00Z):
> - Đã hoàn thành triển khai `query_legal_ground_truth` FastMCP tool trong `packages/ccba-ai/src/ccba_ai/mcp_server.py`.
> - Đã thay thế chuỗi hardcode trong `search_vietnamese_laws` bằng `LegalKnowledgeEngine` (ADR 0035, ADR 0050, RULE-3.1), loại bỏ trích dẫn văn bản hết hiệu lực (NĐ 175/2024, Luật XD 50/2014) và chuyển sang Master Registry hiện hành (Luật XD 2025 số 135/2025/QH15, NĐ 217/2026/NĐ-CP).
> - Bộ test suite `tests/test_federated_rag.py` và `packages/ccba-ai/tests/test_mcp_legal_search.py` pass 100%. Đóng vé Issue #232.

