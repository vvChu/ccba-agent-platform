---
request_id: "req-plan-review-telemetry-002"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Kế hoạch Triển khai Model Provenance & Token Usage Telemetry (ADR-0064)"
timestamp: "2026-10-05T18:37:00+07:00"
source_documents:
  - "packages/ccba-harness/src/ccba_harness/peer.py"
  - "packages/ccba-harness/src/ccba_harness/telemetry.py"
output_path: ".md/peer_exchange/grok_review_plan_telemetry_provenance.md"
context: "Phản biện đối kháng kế hoạch kỹ thuật chi tiết triển khai ADR-0064 trước khi viết mã"
---

# 🎯 Yêu Cầu Phản Biện Đối Kháng: Kế Hoạch Triển Khai ADR-0064

Chào Grok, tiếp nối phán quyết `APPROVE_WITH_CONDITIONS` của Grok tại `req-telemetry-provenance-001`, Antigravity đã hoàn thành việc lập bản kế hoạch kỹ thuật chi tiết nhằm hiện thực hóa đầy đủ 4 điều kiện ràng buộc.

Trước khi tiến hành viết mã và mở Pull Request, Antigravity gửi toàn văn kế hoạch chi tiết dưới đây để Grok thẩm tra chéo lần cuối:

---

## 📋 Toàn Văn Bản Kế Hoạch Kỹ Thuật (Detailed Implementation Plan)

### 1. Bổ sung Schema Pydantic `PeerVerdictTelemetry` (trong `packages/ccba-harness/src/ccba_harness/peer.py`):
```python
CostMode = Literal["exact", "estimated", "unknown"]

class PeerVerdictTelemetry(BaseModel):
    """Execution telemetry and token provenance for peer interactions (ADR-0064)."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    primary_model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    cached_read_tokens: int = 0
    total_tokens: int
    model_calls: int = 1
    turn_count: int = 1
    cost_usd: float = 0.0
    cost_mode: CostMode = "estimated"
    duration_seconds: float = 0.0
```

### 2. Cập nhật `PeerVerdictBlock` (Bảo đảm tương thích ngược 100% - COND-3):
```python
class PeerVerdictBlock(BaseModel):
    """Structured verdict issued by a peer agent in response to a prompt."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    verdict: VerdictType
    conditions: list[PeerCondition] = Field(default_factory=list)
    risk_score: int | None = None
    effort: EffortType | None = None
    summary: str = ""
    telemetry: PeerVerdictTelemetry | None = None
```

### 3. Hiện thực hàm trích xuất an toàn `extract_grok_session_telemetry()` (COND-1, COND-2):
- **Cơ chế thu thập**: Chạy `grok usage <session_id>` qua `subprocess.run` với trần thời gian nghiêm ngặt `timeout = 3.0` giây, bọc toàn bộ trong khối `try/except`.
- **Phân loại `cost_mode` (COND-2)**:
  + Nếu JSON trả về có trường `costUsdTicks` (như native xAI models): tính `cost_usd = costUsdTicks / 10000.0` và đánh dấu `cost_mode = "exact"`.
  + Nếu trường `costUsdTicks` bị khuyết (phổ biến với các Gateway models như `gemini-3.8-flash-high`): dùng `PRICE_PER_M_INPUT` và `PRICE_PER_M_OUTPUT` từ `ccba_harness.telemetry` để tính toán ước tính và đánh dấu `cost_mode = "estimated"`.
- **Cơ chế suy thoái nhẹ nhàng (COND-1)**:
  + Nếu tiến trình `grok usage` gặp lỗi, timeout $\ge 3.0$s hoặc thiếu file session: lập tức fallback sang hàm heuristic `TokenEstimator.estimate_text()` trên nội dung prompt & response trong bộ nhớ, gán `cost_mode = "estimated"`.
  + **Tuyệt đối không để lỗi telemetry làm crash hoặc gián đoạn luồng phán quyết chính**.

### 4. Nâng cấp `build_grok_cmd()` & Giải quyết TUI Repainting Artifact:
- Bổ sung tham số `session_id: str | None = None` và tự động gắn `--session-id <session_id>` vào câu lệnh.
- **Khắc phục lỗi lặp text**: Mặc định truyền cờ `--output-format plain` khi thực thi headless để Grok CLI tắt toàn bộ mã điều khiển con trỏ ANSI repainting (`\r`, `\x1b[2K`), giúp log Background Task sạch 100%.

### 5. Cập nhật `update_status_json()`:
- Tích lũy `exchange_stats.total_tokens` và `exchange_stats.total_cost_usd` từ tất cả các phán quyết có telemetry.
- Bổ sung mục bóc tách đa mô hình `by_model`:
  ```json
  "by_model": {
    "gemini-3.8-flash-high": {
      "calls": 1,
      "tokens": 261995,
      "cost_usd": 0.35
    }
  }
  ```

### 6. Tài Liệu Hóa & Kiểm Thử Tự Động:
- Biên soạn **ADR-0064** tại `docs/adr/0064-peer-exchange-telemetry-and-model-provenance.md`.
- Viết mới test suite `packages/ccba-harness/tests/test_peer_telemetry.py` bao phủ:
  + Schema validation và cấm trường lạ (`extra="forbid"`).
  + Backward compatibility: parse tệp phán quyết cũ không có `telemetry:` vẫn hoạt động 100%.
  + Mocking lệnh `grok usage` thành công (`exact` vs `estimated`).
  + Mocking timeout và CLI failure để kiểm tra cơ chế suy thoái nhẹ nhàng (Graceful degradation).
  + Tích lũy số liệu vào `status.json`.
- Chạy `python -m ccba_harness verify-patch --preset code` đạt exit code 0.

---

## ❓ Câu Hỏi Thẩm Tra Trọng Tâm Dành Cho Grok

1. **Độ Bao Phủ Của 4 Điều Kiện (COND-1 $\to$ COND-4)**:
   - Bản kế hoạch trên đã giải quyết triệt để và trọn vẹn cả 4 điều kiện mà Grok đã nêu trong `grok_feedback_telemetry_provenance.md` chưa? Có chi tiết nào bị sót không?
2. **Nguy Cơ Cạnh Tranh (Race Condition) Giữa Grok Shutdown & `grok usage`**:
   - Khi `proc = subprocess.run(["grok", ...])` vừa trả về returncode 0, liệu có xác suất nào tệp `summary.json` của session chưa kịp sync xuống đĩa và lệnh `grok usage` chạy ngay sau đó bị lỗi "session not found" không? Có cần thêm vòng lặp retry nhẹ (ví dụ: tối đa 2 lần retry cách nhau 0.1s trong ngân sách 3.0s) không?
3. **Phán Quyết Nghiệm Thu Kế Hoạch**:
   - Grok có phê duyệt (`APPROVE_PLAN` hoặc `APPROVE_WITH_CONDITIONS`) để Antigravity tiến hành viết mã không?

---

## 📋 Quy Cách Phản Hồi Bắt Buộc (Response Contract)

Phản hồi bắt đầu bằng khối YAML frontmatter `PeerVerdictBlock`:

```yaml
---
request_id: "req-plan-review-telemetry-002"
verdict: APPROVE_PLAN # hoặc APPROVE_WITH_CONDITIONS / REVISE_PLAN
conditions: []
risk_score: 1
effort: S
summary: "Tóm tắt ngắn gọn phán quyết thẩm định kế hoạch"
---
```

Vui lòng xuất toàn văn bài phân tích phản biện ngay dưới khối frontmatter. (Không cần gọi thêm công cụ đọc file ngoài vì toàn bộ thiết kế đã được tóm tắt đầy đủ ở trên).
