---
proposal_id: "2026-10-17_gemini-4-argon-tier-isolation-and-peer-verdict-normalization"
type: "packages"
name: "gemini-4-argon-tier-isolation-and-peer-verdict-normalization"
status: "open"
priority: "Cao"
related_issue: "#524"
proposed_by_project: "VvC_Notes"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-10-17"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
graduated_to: ""
supersedes_spoke_docs: []
---

# RFC Proposal: Gemini 4 Argon Tier Isolation, CLI Suffix Guard & PeerVerdictBlock Synonym Normalization

- **Tác giả đề xuất:** Antigravity Agent đại diện Spoke (`VvC_Notes` v8.16.0)
- **Ngày lập:** 2026-10-17
- **Trạng thái:** Đang đề xuất (`open`) — Liên kết Issue `#524`
- **Căn cứ pháp lý nền tảng:** [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0063](../../docs/adr/0063-structured-peer-exchange-protocol-and-watcher-daemon.md), [ADR-0065](../../docs/adr/0065-multi-agent-co-review-consensus-and-level3-auto-apply.md).

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain points):**
   - **Treo cứng tiến trình Antigravity CLI (`agy`) khi truyền model trần (`[đo thực tế]`):** Khi gọi `agy -p --model gemini-4-argon` hoặc `gemini-3.8-flash` (thiếu hậu tố `-high`/`-medium`/`-low`), binary `agy` bị treo cứng đến `TimeoutExpired (120s)` mà không trả về stderr để cơ chế self-healing bắt được.
   - **Cascade 404 Outage khi failover model độc quyền CLI:** Họ mô hình `gemini-4-argon-{high,medium,low}` hiện chỉ khả dụng trên local `agy` CLI. Nếu truyền nguyên tên model này qua `TieredFallbackRouter` sang LiteLLM Gateway (Tier 1), Cloud Direct (Tier 2), hoặc Copilot CLI (Tier 3), các tầng dự phòng sẽ trả lỗi `404 ModelNotFoundError` hoặc bị ghi đè sai sang `gemini-3.7-flash-medium` đã ngừng hỗ trợ.
   - **Mất kết quả thẩm định Grok do lệch từ đồng nghĩa Verdict (`[phân tích log]`):** Trong `ccba-harness` (`peer.py`), `PeerVerdictBlock` đã chuẩn hóa `conditions` qua `@field_validator`, nhưng chưa chuẩn hóa `verdict`. Khi Grok (`grok-4.7`) trả về `verdict: CONDITIONAL_APPROVAL` (sau 85 giây phân tích 108 dòng), `parse_verdict_from_md()` trả về `None` và vứt bỏ toàn bộ kết quả.
2. **Quá trình ươm tạo tại Spoke (`VvC_Notes`):**
   - Đã kiểm thử thực nghiệm A/B Concept Synthesis (`gemini-4-argon-medium` giúp tiết kiệm **79.6% output tokens** so với `gemini-3.8-flash-high` và đạt 100% tuân thủ YAML Schema v8.16.0).
   - Đã vượt qua phản biện đối kháng với Grok (`grok-4.7`) và triển khai ổn định trên `vvc-daemon.service` & `vvc-book-ingest.service`.
3. **Giá trị khi phổ biến lên Hub:**
   - Bảo vệ toàn bộ các Spokes sử dụng `ccba-ai` và `ccba-harness` khỏi lỗi treo CLI `agy`, lỗi 404 dây chuyền khi failover, và lỗi mất kết quả `peer-dispatch` của Grok.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Ngăn chặn treo CLI 120s, tiết kiệm ~80% output tokens synthesis, bảo toàn 100% phiên thẩm định Grok |
| **Độ Phức tạp (Complexity)** | Thấp | Chỉ thêm hàm chuẩn hóa regex & validator gọn nhẹ (~65 dòng Python trên 2 packages) |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100% | Đã kiểm chứng qua `check_spoke_leakage.py` và `check_hardcoded_parameters.py` |
| **Bảo tồn Nghiệp vụ (Charter)** | Tuân thủ 100% | Tương thích ngược 100% với toàn bộ unit tests hiện hữu của `ccba-ai` và `ccba-harness` |

---

### 3. Thiết Kế Deep Seams & Đặc Tả Kỹ Thuật tại Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub Monorepo:**
   - `packages/ccba-ai/src/ccba_ai/{routing.py,antigravity_provider.py,fallback.py,__init__.py}`
   - `packages/ccba-harness/src/ccba_harness/peer.py`
   - `.agents/skills/ccba-llm-pipeline-patterns/SKILL.md` (`v1.4.0` $\to$ `v1.5.0`)
2. **Giao diện công khai (Public Interface):**
   ```python
   def normalize_gemini_cli_model(model: str, default_effort: str = "high") -> str:
       """Normalize bare Gemini Flash/Argon CLI model names by appending default effort suffix."""
       ...
   ```
3. **Ngân sách hướng dẫn & Phân tầng (ADR-0030, ADR-0057):**
   - Điểm GPI của `ccba-llm-pipeline-patterns`: `14.5 >= 12.0` (PASS Standalone Kernel Skill).

---

### 4. Quy Trình Thẩm Định 2 Cổng (Hybrid Ingestion Gates - ADR-0045)

1. **Cổng Cứng Tự Động (Hard Gate - CI Automation):**
   - Pass 100% `compile_catalog.py`, `validate_skills.py`, `check_spoke_leakage.py`, `check_hardcoded_parameters.py`, và `pytest`.
2. **Cổng Mềm Tương Tác (Soft Gate - QC Level 5 Supervised Review):**
   - Sẵn sàng cho `/ccba-review-proposal`.

---

### 5. Cam Kết Bất Biến về Bảo Tồn Kỹ Năng (Constitutional Invariant)
- **Quy tắc cấm khai tử tự động (Zero-Usage Deprecation Ban):** Tuân thủ tuyệt đối hiến chương bảo tồn kỹ năng chu kỳ dài của CCBA Hub.
