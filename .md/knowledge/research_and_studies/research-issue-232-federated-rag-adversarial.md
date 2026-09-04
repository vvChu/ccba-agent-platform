# Báo cáo Nghiên cứu: Phản biện Kép cho Implementation Plan Issue #232

> **Phương pháp:** Dual-Agent Adversarial (ADR 0035)
> **Subagent A:** Solution Explorer & Proponent
> **Subagent B:** Risk & Boundary Challenger
> **Ngày:** 2026-09-04

---

## 1. Tóm tắt Thực thi (Executive Summary)

Bản Implementation Plan cho Issue #232 có **nền tảng kỹ thuật khả thi** (Subagent A xác nhận) nhưng chứa **3 vi phạm kiến trúc nghiêm trọng** và **2 rủi ro hiệu năng** cần khắc phục triệt để trước khi triển khai (Subagent B phát hiện). Cụ thể:

1. 🔴 **Vi phạm ADR 0044 (Tier 0 Boundary):** Nhúng module nghiệp vụ pháp lý (`legal_knowledge.py`) vào package Tier 0 (`ccba-ai`).
2. 🔴 **Vi phạm ADR 0010 (HITL Guardrail):** FastMCP tool tự động trigger RAG không cần xác nhận người dùng.
3. 🔴 **Data Plane Starvation:** Hub chỉ có 1 bundle mẫu, Master Corpus thực tế nằm ở Spoke.
4. 🟡 **Vietnamese Tokenization:** BM25 tokenizer dùng `re.findall(r'\w+')` — phá nát từ ghép tiếng Việt.
5. 🟡 **Embedding Latency:** Gọi AI Gateway qua Tailscale VPN có nguy cơ vượt SLA 1.5s.

Tất cả 5 vấn đề đều có **phương án khắc phục rõ ràng** được đề xuất bên dưới.

---

## 2. Kết quả Nghiên cứu Chi tiết (Key Findings)

### Ma trận Đánh giá Đồng thuận / Xung đột

| # | Vấn đề | Explorer (A) | Challenger (B) | Đồng thuận | Mức độ |
|:--|:-------|:-------------|:---------------|:-----------|:-------|
| 1 | Tạo mới `federated_rag.py` thay vì extend `LegalHybridRAG` | ✅ Đồng ý (KISS) | — | Đồng thuận | Thiết kế |
| 2 | `AIClient.embed()` dùng native `embeddings.create()` | ✅ Khả thi | ⚠️ Latency risk | Đồng thuận có điều kiện | Kỹ thuật |
| 3 | `legal_knowledge.py` KHÔNG nằm trong `ccba-ai` | ✅ Dynamic Import | 🔴 Vi phạm ADR 0044 | **Đồng thuận mạnh** | 🔴 Kiến trúc |
| 4 | HITL Guardrail cho MCP tool | — | 🔴 Vi phạm ADR 0010 | Challenger đúng | 🔴 Governance |
| 5 | Data Plane — Hub thiếu corpus | — | 🔴 Starvation risk | Challenger đúng | 🔴 Dữ liệu |
| 6 | Vietnamese tokenizer cần nâng cấp | — | 🟡 BM25 vô hiệu | Challenger đúng | 🟡 Hiệu năng |
| 7 | Embedding cache strategy | ✅ Đề xuất `.npy` | — | Explorer đề xuất | Tối ưu |

### Chi tiết Phân tích

#### 🔴 Vi phạm 1: ADR 0044 — Tier 0 Boundary Breach
- **Vấn đề:** Plan đưa `legal_knowledge.py` vào `ccba-ai` (Tier 0 — Core Platform). Theo ADR 0044, `ccba-ai` chỉ chứa AI Gateway SDK, Circuit Breaker — **generic không phụ thuộc domain**.
- **Hậu quả:** Mọi Spoke (kể cả Spoke BIM, Spoke IDOP) đều load module legal không cần thiết.
- **Cả hai subagent đồng thuận** loại bỏ `legal_knowledge.py` khỏi `ccba-ai`.

#### 🔴 Vi phạm 2: ADR 0010 — HITL Bypass
- **Vấn đề:** ADR 0010 quy định: *"Agent không tự ý spawn subagent nghiên cứu... chỉ chạy khi có sự xác nhận tường minh của người dùng."*
- **Plan hiện tại:** Đăng ký `query_legal_ground_truth` làm MCP tool tự do gọi → Auto-trigger RAG.

#### 🔴 Vi phạm 3: Data Plane Starvation
- **Vấn đề:** Hub chỉ có 1 bundle demo. Toàn bộ kho OKF v2.4 (~50+ văn bản) nằm ở Spoke `ccba-legal-knowledge`.
- **Hậu quả:** Engine chạy trên Hub sẽ trả kết quả gần trống.

#### 🟡 Rủi ro 4: Vietnamese Tokenization
- **Tokenizer hiện tại:** `re.findall(r'\w+')` tách ký tự, không hiểu từ ghép ("thẩm duyệt" → `["thẩm", "duyệt"]`).
- **Đánh giá:** Whitespace splitting đủ dùng cho văn bản pháp luật chính quy, nhưng mất precision cho compound terms.

#### 🟡 Rủi ro 5: Embedding Latency
- OpenAI SDK hỗ trợ `embeddings.create()` trực tiếp qua LiteLLM proxy.
- Gọi qua Tailscale VPN: ~200-500ms/call [ước lượng lý thuyết — chưa đo thực tế].
- Cần cache embedding vectors để tránh gọi API mỗi lần query.

---

## 3. Khuyến nghị Triển khai (Implementation Recommendations)

### Điều chỉnh 1: Kiến trúc Module — Loại bỏ `legal_knowledge.py` khỏi `ccba-ai`

```
SAU (Kiến trúc sửa đổi — Tuân thủ ADR 0044):
┌─────────────────────┐     ┌────────────────────────────┐
│ ccba-ai (Tier 0)    │     │ ccba-legal-intel (Tier 1)  │
│ ├─ client.py        │     │ ├─ federated_rag.py [NEW]  │
│ │   + embed()       │     │ │   FederatedLegalEngine   │
│ └─ mcp_server.py    │     │ │   + query_ground_truth() │
│     + tool (dynamic) │←···│ ├─ hybrid_rag.py (giữ nguyên)│
└─────────────────────┘     │ └─ registry.py             │
  ↑ Dynamic import only     └────────────────────────────┘
```

### Điều chỉnh 2: HITL Guardrail
- Tool chỉ trả kết quả (read-only search), không trigger pipeline.
- Khi cần đối chiếu sâu → đề xuất lệnh `/ccba-research` cho người dùng xác nhận.

### Điều chỉnh 3: Configurable Corpus Path
- `FederatedLegalEngine.__init__()` nhận `corpus_paths: list[Path]`.
- Hỗ trợ cấu hình đường dẫn corpus qua biến môi trường. Corpus rỗng → trả kết quả trống, không crash.

### Điều chỉnh 4: Bigram Enhancement cho Tokenizer
- Giữ `text.lower().split()` (KISS). Bổ sung bigram: `["phòng", "cháy", "phòng_cháy"]`.
- Không thêm dependency nặng.

### Điều chỉnh 5: Embedding Cache
- Lưu tại `<bundle_dir>/embeddings.npy`. Cache freshness qua SHA-256.
- Offline/mock mode → skip embedding, fallback 100% BM25.

---

## 4. Tài liệu Tham chiếu (References)

| Nguồn | Phát hiện |
|:-------|:----------|
| [ADR 0044](../../../docs/adr/0044-spoke-hub-package-bootstrap-standard.md) | Tier 0/1/2 boundary rules |
| [ADR 0010](../../../docs/adr/0010-skills-integration-and-rag-boundaries.md) | HITL guardrail for RAG |
| [ADR 0049](../../../docs/adr/0049-okf-v2-4-universal-agent-centric-specification-and-cloud-vault.md) | OKF v2.4 bundle structure |
| [hybrid_rag.py](../../../packages/ccba-legal-intel/src/ccba_legal/hybrid_rag.py) | BM25 tokenizer analysis |
| [client.py](../../../packages/ccba-ai/src/ccba_ai/client.py) | AIClient API surface |
| [registry.py](../../../packages/ccba-legal-intel/src/ccba_legal/registry.py) | Corpus discovery via registry |

---

## 5. Câu hỏi Chưa Làm Rõ (Unresolved Questions)

1. **Auth cho MCP Endpoint:** Cơ chế xác thực cross-Spoke cho FastMCP tool?
2. **Embedding Cost Budget:** ~10,000 embedding calls cho full corpus — chi phí/quota?
3. **Cache Invalidation:** Spoke cập nhật văn bản mới → `embeddings.npy` stale. Cơ chế rebuild?
