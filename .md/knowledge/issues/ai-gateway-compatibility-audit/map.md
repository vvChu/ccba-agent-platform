# Wayfinder Map: AI Gateway Client Contract Compatibility & Standardization

> **Issue Path**: `.md/knowledge/issues/ai-gateway-compatibility-audit/map.md`  
> **Trạng thái**: Hoàn thành (Resolved)  
> **Chủ đề**: Đánh giá & Chuẩn hóa Tương thích Toàn bộ Codebase với Hợp đồng AI Gateway Client Integration Guide (4 Model Archetypes, Timeout >= 30-60s, Fallback Cascade, Zero-config Thinking)

---

## 🎯 Điểm đích (Destination)

Toàn bộ hệ sinh thái **CCBA Platform** (bao gồm core package `ccba-ai`, các packages phụ trợ `mdconverter`, `ccba-legal-intel`, `ccba-pdf-prep`, 50+ Agent Skills, Workflows và tài liệu cấu hình môi trường) tuân thủ 100% **AI Gateway Client Integration Contract**:
1. **HTTP Timeout**: Tất cả HTTP client/SDK gọi AI Gateway đều cấu hình `timeout >= 30.0s` (mặc định chuẩn: `60.0s`).
2. **Model Archetypes**: Chuẩn hóa định tuyến theo 4 Archetypes chuẩn (`ocr-primary`, `gemini-3.7-flash`, `gemini-3.7-flash-high`, `rag-core`/`qwen-local-primary`).
3. **Zero-Config Thinking**: Loại bỏ các cấu trúc cấu hình thinking thủ công ở tầng client, tận dụng bộ tiền xử lý tự động của Gateway.
4. **Tài liệu & ADR**: Cập nhật đồng bộ `ai-gateway-sdk`, `client-setup-guide.md`, và ban hành ADR-0029.

---

## 📝 Ghi chú (Notes)

- **Reuse-First Gate**: Tuân thủ Layer 1 Constitution, kế thừa và mở rộng `packages/ccba-ai`.
- **Deep Modules**: Tách module `ccba_ai/routing.py` để giữ `client.py` tập trung vào HTTP I/O.
- **Không hardcode secrets**: Mọi template `.env` và config giữ nguyên cấu trúc biến môi trường an toàn.

---

## 📍 Quyết định đã chốt (Decisions so far)

- [x] `[Quyết định Hợp đồng Client]` Thống nhất sử dụng Tailscale VPN `http://100.83.192.30:8090/v1` và Auth Bearer `sk-spark-secure-key-2026` làm chuẩn kết nối liên Hub/Spoke.
- [x] `[Quyết định 4 Archetypes]` Phân định rõ 4 nhóm mô hình: (1) OCR & Vision Ingestion, (2) Standard General / Coding, (3) Deep Reasoning / Complex Audit, (4) Local Private / Zero-Cost.
- [x] `[TICKET-01: Audit Inventory]` [ticket-01-audit-codebase-skills.md](ticket-01-audit-codebase-skills.md) — Rà soát toàn bộ codebase.
- [x] `[TICKET-02: Core SDK]` [ticket-02-standardize-ccba-ai-sdk.md](ticket-02-standardize-ccba-ai-sdk.md) — Hỗ trợ `timeout=60.0` và `routing.py`.
- [x] `[TICKET-03: Skills & Docs]` [ticket-03-sync-skills-and-docs.md](ticket-03-sync-skills-and-docs.md) — Đồng bộ `SKILL.md` và `client-setup-guide.md`.
- [x] `[TICKET-04: Specialized Packages & Skills]` [ticket-04-align-specialized-skills.md](ticket-04-align-specialized-skills.md) — Cập nhật `mdconverter`, `ccba-legal-intel`, `ccba-pdf-prep`, `discovery_engine`, `orchestrator`, `llm_adapter`.
- [x] `[TICKET-05: ADR]` [ticket-05-publish-adr.md](ticket-05-publish-adr.md) — Ban hành ADR-0029.

---

## 🚀 Danh sách Ticket Biên giới (Frontier Tickets)

1. ✅ `[TICKET-01]` [Audit Codebase & Skills Inventory](ticket-01-audit-codebase-skills.md) — Closed
2. ✅ `[TICKET-02]` [Chuẩn hóa Timeout & Archetypes trong ccba-ai SDK](ticket-02-standardize-ccba-ai-sdk.md) — Closed
3. ✅ `[TICKET-03]` [Đồng bộ Skill ai-gateway-sdk & Client Setup Guide](ticket-03-sync-skills-and-docs.md) — Closed
4. ✅ `[TICKET-04]` [Rà soát & Điều chỉnh Model Routing trong Specialized Skills](ticket-04-align-specialized-skills.md) — Closed
5. ✅ `[TICKET-05]` [Ban hành ADR Kiến trúc Client Gateway Contract](ticket-05-publish-adr.md) — Closed
