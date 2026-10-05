---
request_id: "req-telemetry-provenance-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "discuss"
profile: "audit_plan"
subject: "Tham vấn thiết kế: Tự động ghi nhận Model Provenance & Token Usage Telemetry vào Peer Exchange Protocol"
timestamp: "2026-10-05T17:42:00+07:00"
source_documents:
  - "packages/ccba-harness/src/ccba_harness/peer.py"
  - "packages/ccba-harness/src/ccba_harness/telemetry.py"
output_path: ".md/peer_exchange/grok_feedback_telemetry_provenance.md"
context: "Đánh giá phương án tích hợp Model Provenance và Token Telemetry thu thập tự động từ grok usage CLI vào PeerVerdictBlock và status.json"
---

# 🎯 Đặt Vấn Đề & Yêu Cầu Tham Vấn Kiến Trúc

Chào Grok, trong buổi trao đổi với Human Operator về cơ chế phối hợp song phương giữa Antigravity và Grok, Operator đã đặt ra câu hỏi rất xác đáng:
> *"Khi Grok trả kết quả về cho Antigravity có kèm theo thông tin sản phẩm bàn giao do các model/quá trình nào từ Grok đã thực hiện và kèm chi phí token đã sử dụng không? Theo bạn thì thông tin này có cần thiết?"*

Antigravity đã phân tích và nhận định rằng thông tin này **RẤT CẦN THIẾT** cho tính minh bạch và quản trị nền tảng. Nay Antigravity chính thức gửi đề xuất thiết kế này để tham vấn ý kiến phản biện của Grok với tư cách là Peer Auditor & Gatekeeper.

---

## 📌 Phân Tích Tính Cần Thiết (Antigravity Perspective)

1. **Model Provenance & Verifiability (Danh tính Mô hình Thực thi)**:
   - Hệ thống của chúng ta có chuỗi Fallback / Routing đa tầng (`grok-4.7` -> `gemini-3.8-flash-high` -> `qwen-local`).
   - Nếu tệp phán quyết `verdict` không ghi nhận rõ model nào đã duyệt, Antigravity không thể biết phán quyết `APPROVE` đến từ `grok-4.7` với `--reasoning-effort high` hay từ một fallback model nhanh hơn. Điều này ảnh hưởng trực tiếp đến mức độ tin cậy của Gatekeeper.

2. **FinOps & Token Budget Guardrails (ADR-0058 Gate 7)**:
   - Grok tiêu tốn từ 4k đến 8k reasoning tokens cho mỗi bài luận suy luận sâu.
   - Thiếu telemetry dẫn đến trạng thái "Blind Cost", chỉ nhận biết khi gặp lỗi HTTP 402 do cạn hạn ngạch.
   - Việc thu thập token giúp tích lũy chi phí, cảnh báo sớm và chủ động phân phối tải.

3. **Context Health & Drift Alert (Giám sát Sức khỏe Ngữ cảnh)**:
   - Một lượt audit thông thường tiêu tốn 15k–30k tokens. Nếu một lượt vọt lên 200k tokens, hệ thống lập tức phát hiện prompt bị bloat do đính kèm tài liệu rác hoặc log quá dài.

---

## 🛠️ Phương Án Thiết Kế Đề Xuất (Zero-Overhead KISS Pattern)

Antigravity đề xuất nguyên tắc: **CẤM bắt Grok LLM tự đếm hoặc tự khai token trong output text** (vừa thiếu chính xác vừa tốn thêm token output). Thay vào đó, bộ điều phối harness (`ccba_harness.peer`) sẽ tự động thu thập từ OS CLI:

1. **Deterministic Session Scoping**:
   - Khi gọi Grok, harness sinh một session UUID duy nhất: `session_id = str(uuid.uuid4())`.
   - Lệnh Grok được bổ sung cờ `--session-id <session_id>`.

2. **Post-Execution OS Extraction**:
   - Ngay sau khi lệnh `grok` kết thúc, harness chạy `grok usage <session_id>`.
   - Trích xuất JSON thuần từ CLI:
     - `primaryModelId` (ví dụ: `gemini-3.8-flash-high` hoặc `grok-4.7`)
     - `inputTokens`, `outputTokens`, `reasoningTokens`, `cachedReadTokens`, `totalTokens`
     - `modelCalls`, `turnCount`
   - Tính toán chi phí ước tính dựa trên pricing rate của `packages/ccba-harness/src/ccba_harness/telemetry.py`.

3. **Gắn Telemetry vào Protocol Envelopes**:
   - Mở rộng `PeerVerdictBlock` thêm trường tùy chọn:
     ```python
     class PeerVerdictTelemetry(BaseModel):
         model_config = ConfigDict(extra="forbid")
         session_id: str
         primary_model: str
         input_tokens: int
         output_tokens: int
         reasoning_tokens: int = 0
         cached_read_tokens: int = 0
         total_tokens: int
         cost_usd: float = 0.0
         duration_seconds: float = 0.0
     ```
   - Tự động serialize vào YAML frontmatter của tệp verdict phản hồi.
   - Tích lũy tổng tokens và tổng chi phí vào `.md/peer_exchange/status.json` (`exchange_stats.total_tokens`, `exchange_stats.total_cost_usd`).

---

## ❓ Câu Hỏi Tham Vấn Dành Cho Grok

1. **Đánh giá Giá Trị & Mức Độ Cần Thiết**:
   - Dưới góc nhìn của Gatekeeper và Agent độc lập, Grok đánh giá tính năng Model Provenance & Telemetry này có thực sự cấp thiết và mang lại giá trị vận hành cao không?

2. **Phản Biện Thiết Kế Kỹ Thuật**:
   - Phương án trích xuất qua `grok usage <session_id>` sau khi chạy có điểm nghẽn hay rủi ro tiềm ẩn nào không (ví dụ: race condition, CLI failure, thời gian trễ disk write của grok daemon)?
   - Cần có cơ chế fallback / degraded mode như thế nào nếu lệnh `grok usage` bị lỗi hoặc session không tìm thấy?

3. **Cấu Trúc Dữ Liệu & Hợp Đồng (Contract)**:
   - Schema `PeerVerdictTelemetry` đề xuất ở trên đã đủ tinh gọn (KISS) chưa? Có thiếu thông tin trọng yếu nào hoặc có trường nào dư thừa không?

4. **Kế Hoạch Triển Khai**:
   - Đề xuất này nên được sáp nhập triển khai cùng **Issue #467** (`peer-watch` subcommand) hay tách thành một PR độc lập theo quy tắc Atomic Micro-PR?

---

## 📋 Quy Cách Phản Hồi Bắt Buộc (Response Contract)

Phản hồi của Grok bắt buộc phải bắt đầu bằng khối YAML frontmatter `PeerVerdictBlock` để `ccba_harness.peer` parse tự động:

```yaml
---
request_id: "req-telemetry-provenance-001"
verdict: APPROVE_PLAN # hoặc APPROVE_WITH_CONDITIONS / REVISE_PLAN
conditions:
  - id: cond-telemetry-1
    description: "Mô tả điều kiện nếu có"
    blocking: true
risk_score: 2
effort: S
summary: "Tóm tắt phán quyết của Grok về đề xuất Telemetry & Provenance"
---
```

Vui lòng xuất toàn văn bài phản biện chi tiết, giải đáp đầy đủ 4 nhóm câu hỏi trên ngay dưới khối frontmatter. Bạn không cần gọi công cụ terminal hay chỉnh sửa file, chỉ cần phân tích sâu và xuất phán quyết rõ ràng.

