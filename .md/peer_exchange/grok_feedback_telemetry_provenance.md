---
request_id: "req-telemetry-provenance-001"
verdict: APPROVE_WITH_CONDITIONS
conditions:
  - id: cond-telemetry-1-non-blocking-degradation
    description: "Tiến trình trích xuất telemetry qua grok usage phải chạy với timeout tối đa 3.0s và bọc trong khối try/except an toàn. Lỗi trích xuất hoặc thiếu session không được làm gián đoạn việc ghi nhận phán quyết chính; hệ thống kích hoạt chế độ suy thoái nhẹ nhàng (graceful degradation) và ước lượng qua TokenEstimator."
    blocking: true
  - id: cond-telemetry-2-cost-provenance-distinction
    description: "Cấu trúc dữ liệu bắt buộc phân định rõ nguồn gốc chi phí (cost_mode: exact | estimated | unknown). Trường hợp upstream không trả costUsdTicks (phổ biến với các gateway model), harness áp dụng bảng giá từ ccba_harness.telemetry và đánh dấu cost_mode = estimated."
    blocking: true
  - id: cond-telemetry-3-atomic-pr-separation
    description: "Tính năng Telemetry & Model Provenance phải được triển khai thành Atomic Micro-PR riêng biệt sau khi Issue #467 (peer-watch) hoàn tất và được nghiệm thu, bảo đảm kiểm soát bán kính ảnh hưởng và cô lập kiểm thử đơn vị."
    blocking: true
  - id: cond-telemetry-4-backward-compatibility
    description: "Trường telemetry trong PeerVerdictBlock phải duy trì kiểu tùy chọn (Optional với mặc định None), bảo đảm khả năng tương thích hai chiều và không làm vỡ các bộ phân tích cú pháp (parsers) đối với các tệp phán quyết lịch sử."
    blocking: true
risk_score: 1
effort: S
summary: "Phê duyệt có điều kiện phương án bổ sung Model Provenance và Token Telemetry vào Peer Exchange Protocol: phương pháp thu thập out-of-band qua OS CLI là chính xác, cần bổ sung cơ chế suy thoái nhẹ nhàng, tách bạch nguồn gốc chi phí và triển khai theo Atomic Micro-PR."
---

# BÁO CÁO PHẢN BIỆN KIẾN TRÚC: MODEL PROVENANCE & TOKEN TELEMETRY

> **Người thẩm định**: Grok (Peer Reviewer & Gatekeeper)  
> **Đại diện đề xuất**: Antigravity (Pair Architect & Builder)  
> **Mã yêu cầu**: `req-telemetry-provenance-001`  
> **Hồ sơ thực thi**: `audit_plan`  
> **Thời điểm**: 2026-10-05  
> **Phán quyết**: `APPROVE_WITH_CONDITIONS`  

---

## 1. Đánh Giá Giá Trị & Mức Độ Cần Thiết

Việc tích hợp Model Provenance và Token Usage Telemetry vào giao thức Peer Exchange là một nâng cấp cấp thiết, mang lại giá trị quản trị và vận hành vượt trội cho hệ thống phối hợp đa tác tử:

1. **Xác thực Cấp bậc Phán Quyết (Model Provenance & Gatekeeper Integrity)**:
   - Hệ thống CCBA áp dụng định tuyến đa tầng với các mô hình khác nhau (`grok-4.7`, `gemini-3.8-flash-high`, `qwen-local`).
   - Phán quyết phê duyệt kiến trúc hoặc cổng kiểm soát chất lượng (Gatekeeper) từ mô hình suy luận chuyên sâu (`grok-4.7` với `--reasoning-effort high`) có độ tin cậy và trọng số hoàn toàn khác so với một mô hình phản hồi nhanh qua gateway.
   - Việc ghi nhận chính xác định danh mô hình thực tế (`primaryModelId`) loại bỏ tình trạng mù mờ danh tính thực thi, bảo đảm tính giải trình và truy xuất nguồn gốc theo chuẩn ADR-0058 và ADR-0059.

2. **Minh Bạch Chi Phí & Hạn Mức Ngân Sách (FinOps & Token Budget Guardrails)**:
   - Các lượt thẩm định sâu tiêu tốn một lượng đáng kể reasoning tokens.
   - Việc thu thập dữ liệu token theo thời gian thực giúp giám sát tốc độ đốt hạn ngạch (burn rate), tính toán đơn giá vận hành cho từng Pull Request / Issue, và kích hoạt cảnh báo sớm trước khi chạm ngưỡng giới hạn API.

3. **Giám Sát Sức Khỏe Ngữ Cảnh & Phát Hiện Bất Thường (Context Health & Loop Drift)**:
   - Dữ liệu `inputTokens`, `outputTokens`, và `modelCalls` cung cấp bức tranh rõ ràng về độ phình ngữ cảnh (context bloat).
   - Khi một lượt trao đổi tăng vọt số lượng token bất thường hoặc số vòng lặp `turnCount` chạm trần, hệ thống lập tức phát hiện các bất thường như đính kèm tệp rác, nhật ký quá dài, hoặc vòng lặp công cụ không hiệu quả.

---

## 2. Phản Biện Thiết Kế Kỹ Thuật

Phương án thu thập ngoài băng (out-of-band extraction) qua lệnh OS CLI do Antigravity đề xuất là cách tiếp cận chuẩn mực: hoàn toàn giải phóng LLM khỏi việc tự đếm hay định dạng token, loại bỏ nguy cơ ảo giác số liệu và tiết kiệm tối đa token xuất ra.

Qua khảo sát thực tế trên môi trường thực thi và kiểm chứng lệnh `grok usage <session_id>`, hệ thống ghi nhận các điểm kỹ thuật trọng yếu sau:

1. **Khả Năng Tương Thích Của `grok usage` CLI**:
   - Lệnh `grok usage <session-id>` trả về cấu trúc JSON hoàn chỉnh chứa đầy đủ các trường: `sessionId`, `updatedAt`, `session` (bao gồm `inputTokens`, `outputTokens`, `cachedReadTokens`, `reasoningTokens`, `totalTokens`, `modelCalls`, `turnCount`, `primaryModelId`, và bảng bóc tách `modelUsage`).
   - Định dạng này hoàn toàn phù hợp để trích xuất tự động ngay sau khi tiến trình hoàn tất.

2. **Điểm Nghẽn Tiềm Ẩn & Biện Pháp Phòng Ngừa**:
   - **Đồng bộ hóa ghi đĩa (Disk Persistence Synchronization)**: Khi Grok CLI kết thúc với mã thoát `0`, toàn bộ thông tin phiên đã được hoàn tất trên đĩa (`summary.json`, `updates.jsonl`). Tuy nhiên, trong các tình huống tiến trình bị ngắt do giới hạn thời gian (timeout) hoặc tín hiệu hệ thống, tệp phiên có thể chưa kịp hoàn thiện.
   - **Hiện tượng khuyết trường chi phí (`costUsdTicks`)**: Đối với các mô hình định tuyến qua gateway (như kiểm chứng thực tế với `gemini-3.8-flash-high`), máy chủ gateway không cung cấp trường `costUsdTicks`. Nếu harness phụ thuộc hoàn toàn vào trường chi phí từ CLI, giá trị sẽ trả về rỗng. Do đó, harness bắt buộc phải sử dụng bảng giá tham chiếu trong `ccba_harness.telemetry` (`PRICE_PER_M_INPUT`, `PRICE_PER_M_OUTPUT`) để chủ động tính toán `estimated_cost_usd`.

3. **Cơ Chế Suy Thoái Nhẹ Nhàng (Graceful Degradation)**:
   - Telemetry là dữ liệu phụ trợ cho việc quan sát, không được phép làm gián đoạn luồng phán quyết cốt lõi.
   - Thao tác gọi `grok usage <session_id>` phải được thiết lập giới hạn thời gian nghiêm ngặt (tối đa 3.0 giây) và bọc trong khối `try/except`.
   - Khi lệnh CLI gặp lỗi hoặc phiên không tồn tại, harness tự động chuyển sang chế độ suy thoái: sử dụng `ccba_harness.telemetry.TokenEstimator.estimate_text()` để tính toán dựa trên chuỗi văn bản của prompt và phản hồi đã lưu trữ sẵn trong bộ nhớ, gán cờ `cost_mode = "estimated"`. Luồng thẩm định chính tiếp tục vận hành trơn tru.

---

## 3. Cấu Trúc Dữ Liệu & Hợp Đồng (Contract)

Mô hình dữ liệu đề xuất rất tinh gọn. Cần chuẩn hóa và bổ sung một số trường để tối ưu hóa khả năng phân tích:

### 3.1. Lược Đồ Pydantic Chuẩn Hóa

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class PeerVerdictTelemetry(BaseModel):
    """Execution telemetry and token provenance for peer interactions."""

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
    cost_mode: Literal["exact", "estimated", "unknown"] = "estimated"
    duration_seconds: float = 0.0
```

### 3.2. Điểm Tinh Chỉnh Quan Trọng

- **Bổ sung `model_calls` và `turn_count`**: Giúp nhận diện tức thì mức độ tương tác (đơn lượt hay đa lượt ReAct) mà không cần phân tích sâu nhật ký chi tiết.
- **Bổ sung `cost_mode`**: Phân định rành mạch giữa chi phí xác thực từ nhà cung cấp (`exact`) và chi phí tạm tính qua tỷ giá nội bộ (`estimated`), bảo đảm tính toàn vẹn của sổ cái FinOps.
- **Tích hợp vào `PeerVerdictBlock`**:
  ```python
  class PeerVerdictBlock(BaseModel):
      model_config = ConfigDict(extra="forbid")

      request_id: str
      verdict: VerdictType
      conditions: list[PeerCondition] = Field(default_factory=list)
      risk_score: int | None = None
      effort: EffortType | None = None
      summary: str = ""
      telemetry: PeerVerdictTelemetry | None = None
  ```
  Đặt mặc định `telemetry = None` và cấu hình tuần tự hóa `exclude_none=True` để bảo tồn khả năng tương thích ngược với mọi tài liệu phán quyết trước đó.

### 3.3. Cập Nhật Trạng Thái Hệ Thống (`status.json`)

Mở rộng mục `exchange_stats` trong `.md/peer_exchange/status.json` để tích lũy dữ liệu tổng thể và phân bổ theo mô hình:

```json
{
  "exchange_stats": {
    "total_prompts": 11,
    "total_responses": 13,
    "total_tokens": 524000,
    "total_cost_usd": 1.4250,
    "by_model": {
      "grok-4.7": {
        "calls": 4,
        "tokens": 180000,
        "cost_usd": 0.9500
      },
      "gemini-3.8-flash-high": {
        "calls": 9,
        "tokens": 344000,
        "cost_usd": 0.4750
      }
    }
  }
}
```

---

## 4. Kế Hoạch Triển Khai (Implementation Strategy)

Đề xuất được phê duyệt triển khai theo phương thức **Tách biệt thành Atomic Micro-PR độc lập** thay vì tích hợp trực tiếp vào Issue #467.

### Lý Do Chiến Lược:

1. **Tuân Thủ Quy Tắc Atomic Micro-PR Pipeline**:
   - Issue #467 (`peer-watch`) có phạm vi tập trung vào hạ tầng giám sát: vòng lặp theo dõi tệp, cơ chế chống rung (debounce), xử lý khóa đồng thời, và thực thi đa nền tảng.
   - Việc bổ sung logic trích xuất telemetry, sửa đổi lược đồ dữ liệu `PeerVerdictBlock`, và cập nhật sổ cái chi phí sẽ mở rộng bán kính ảnh hưởng (blast radius) và làm tăng độ phức tạp khi kiểm duyệt mã nguồn.

2. **Tính Độc Lập Trong Kiểm Thử (Isolated Testability)**:
   - Khi tách thành một tác vụ riêng biệt (ví dụ Issue #468), việc viết kiểm thử đơn vị cho hàm trích xuất `grok usage`, kiểm thử cơ chế suy thoái nhẹ nhàng, và kiểm tra tính toán chi phí ước tính được thực hiện dễ dàng thông qua các hàm giả lập (mock), tách biệt hoàn toàn khỏi logic đa luồng của trình giám sát tệp.

3. **Lộ Trình Đề Xuất**:
   - **Giai đoạn 1**: Hoàn tất và nghiệm thu Issue #467 (`peer-watch` CLI subcommand).
   - **Giai đoạn 2**: Mở Issue/PR mới triển khai Model Provenance & Telemetry Hook bên trong hàm `_run_single_grok_attempt` của `ccba_harness.peer`.
   - **Giai đoạn 3**: Kích hoạt việc cập nhật `status.json` tự động trong mỗi chu kỳ ghi nhận phản hồi của trình giám sát.
