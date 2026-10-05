# HUB-ADR 0064: Peer Exchange Model Provenance, Token Usage Telemetry, and Zero-Hang Execution Lifecycle

- **Trạng thái**: ✅ ACCEPTED
- **Ngày quyết định**: 2026-10-05
- **Tác giả**: CCBA Core Architecture & Antigravity Agent
- **Người phản biện**: Grok Peer Reviewer (`APPROVE_PLAN`, req-plan-review-telemetry-002)
- **Tương thích**: ADR-0007 (Peer Exchange), ADR-0009 (Pstack Disciplines), ADR-0030 (Telemetry), ADR-0058 (Live Collaboration), ADR-0061 (Platform-Aware KISS v2), ADR-0062 (Declarative Sync Registry), ADR-0063 (Level-2 Peer Delegation Protocol)

---

## 1. Bối Cảnh (Context)

Trong quá trình vận hành giao thức trao đổi đồng đẳng hai chiều (**Peer Exchange Protocol**) giữa **Antigravity (Pair Architect & Builder)** và **Grok (Auditor & Gatekeeper)** theo các chuẩn ADR-0007, ADR-0062 và ADR-0063, hệ thống ghi nhận hai lỗ hổng vận hành trọng yếu:

1. **Hiện tượng mù danh tính mô hình thực thi (Blind Model Provenance)**:
   - Hệ thống áp dụng chuỗi định tuyến đa tầng (`grok-4.7` trên xAI Cloud $\rightarrow$ `gemini-3.8-flash-high` trên Spark Gateway $\rightarrow$ `qwen-local` trên DGX GB10).
   - Trước ADR-0064, tệp phán quyết `PeerVerdictBlock` không ghi nhận định danh mô hình thực tế đã xử lý yêu cầu. Antigravity không thể phân biệt phán quyết đến từ mô hình suy luận sâu chuyên sâu (`grok-4.7` với `--reasoning-effort xhigh`) hay từ mô hình phản hồi nhanh dự phòng qua Gateway, làm suy giảm tính toàn vẹn của cổng kiểm soát chất lượng (Gatekeeper Integrity).

2. **Hiện tượng mù chi phí vận hành (Blind Cost & Token Quota Risk - ADR-0058 Gate 7)**:
   - Grok CLI tiêu tốn hàng nghìn reasoning tokens cho mỗi lượt suy luận. Thiếu telemetry thời gian thực dẫn đến nguy cơ chạm trần hạn ngạch đột ngột (lỗi HTTP 402) mà không có cảnh báo sớm.

3. **Sự cố treo tiến trình tương tác (Interactive Terminal Hang)**:
   - Khi Grok Runner nhận đối số câu hỏi dạng chuỗi vị trí (`grok [OPTIONS] "prompt"`), Grok CLI kích hoạt vòng lặp TUI tương tác và không tự động thoát (`exit 0`). Antigravity ở trạng thái ngủ hướng sự kiện (event-driven idle) bị đóng băng cho tới khi con người can thiệp.

---

## 2. Quyết Định Kiến Trúc (Decision)

Hệ thống thiết lập chuẩn **ADR-0064** với 4 trụ cột kỹ thuật:

### 2.1. Lược Đồ Dữ Liệu Pydantic `PeerVerdictTelemetry`

Mở rộng `packages/ccba-harness/src/ccba_harness/peer.py`:

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

Tích hợp vào `PeerVerdictBlock` với giá trị mặc định `None` để bảo đảm **100% tương thích ngược (COND-4)**:
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

### 2.2. Cơ Chế Thu Thập Out-of-band & Bounded Retry (COND-1, COND-2)

- Tuyệt đối không bắt LLM tự đếm hoặc tự khai token trong văn bản (tiêu tốn đúng 0 token LLM phụ trội).
- Lệnh gọi Grok được gán `--session-id <uuid>`. Sau khi tiến trình Grok hoàn tất, harness gọi `grok usage <session_id>`.
- **Bounded Retry Loop**: Thử lại tối đa 2 lần (khoảng cách 100ms) trong ngân sách 3.0 giây để phòng ngừa độ trễ I/O đóng tệp của Grok daemon trên các hệ thống tệp có tải cao.
- **Phân định nguồn gốc chi phí (COND-2)**:
  + Nếu có trường `costUsdTicks` (native models): tính `cost_usd = costUsdTicks / 10000.0`, gán `cost_mode = "exact"`.
  + Nếu khuyết `costUsdTicks` (gateway models): áp dụng biểu giá từ `ccba_harness.telemetry` (`PRICE_PER_M_INPUT`, `PRICE_PER_M_OUTPUT`), gán `cost_mode = "estimated"`.
- **Cơ chế suy thoái nhẹ nhàng (COND-1)**: Nếu lệnh CLI gặp lỗi, timeout $\ge 3.0$s hoặc phiên không tồn tại, tự động fallback sang `TokenEstimator.estimate_text()` trên nội dung prompt & response trong bộ nhớ, gán `cost_mode = "estimated"`. Tuyệt đối không làm gián đoạn luồng phán quyết chính.

### 2.3. Cưỡng Chế Vòng Đời Headless & Triệt Tiêu Treo Terminal (Zero-Hang Invariant)

- **Cấm Positional Prompt**: Cưỡng chế 100% lệnh gọi Grok phải đi qua `--prompt-file <path>`, cấm tuyệt đối chuỗi đối số vị trí trần.
- **Mặc định `--output-format plain`**: Triệt tiêu toàn bộ mã ANSI escape repainting (`\r`, `\x1b[2K`), giữ nhật ký tiến trình nền sạch sẽ và không bị lặp dòng.
- **Đóng luồng đầu vào (`stdin=subprocess.DEVNULL`)**: Chặn đứng mọi khả năng tiến trình con dừng chờ tương tác bàn phím.
- **Chuyển sang `subprocess.Popen` & Watchdog polling**: Thay thế `subprocess.run` đồng bộ bằng vòng lặp kiểm tra `proc.poll()` kết hợp giám sát tệp `output_path`. Khi tệp phán quyết hoàn tất và hợp lệ trên đĩa, harness chủ động giải phóng tiến trình.

### 2.4. Phân Tầng Suy Luận Sâu: `xhigh` Cho Thẩm Định Kiến Trúc

- Cập nhật profile `AUDIT_PLAN`: cấu hình mặc định **`reasoning_effort: "xhigh"`** khi chạy với `grok-4.7` trên xAI Cloud để phát huy tối đa năng lực bắt lỗi kiến trúc tinh vi.
- Profile `AGENTIC_CODE` và review code duy trì `reasoning_effort: "high"` để cân bằng tốc độ và chi phí.

---

## 3. Hệ Quả & Đánh Giá (Consequences)

### 3.1. Điểm Tích Cực
- **Minh Bạch 100% Cấp Bậc Phán Quyết**: Hệ thống và kỹ sư lập tức nhận biết phán quyết do model nào duyệt, loại bỏ nguy cơ ngộ nhận độ tin cậy.
- **Sổ Cái FinOps Tự Động**: Bảng `.md/peer_exchange/status.json` liên tục tích lũy tổng số token, chi phí USD và thống kê bóc tách theo từng mô hình (`by_model`).
- **Khôi Phục Chuỗi Tự Động Hóa Không Ngắt Quãng**: Loại bỏ hoàn toàn tình trạng Grok treo terminal, bảo đảm pipeline Antigravity $\leftrightarrow$ Grok diễn ra trơn tru từ đầu đến cuối mà không cần con người nhắc nhở.

### 3.2. Rủi Ro & Cơ Chế Giảm Thiểu
- *Độ trễ khi gọi thêm `grok usage`*: Giới hạn cứng trong 3.0s với bounded retry 100ms; nếu quá hạn lập tức fallback sang `TokenEstimator`.
- *Khác biệt giá giữa các Gateway model*: Tách bạch rõ `cost_mode = "estimated"` để không gây hiểu nhầm với số liệu quyết toán thực tế của nhà cung cấp.

---

## 4. Kiểm Chứng Tuân Thủ (Compliance Verification)

- **Unit Tests (TDD)**:
  + `packages/ccba-harness/tests/test_peer_telemetry.py`: 100% test coverage cho schema validation, backward compatibility, mock `grok usage` (exact vs estimated), fallback graceful degradation, và status.json aggregation.
- **Deterministic Hard Completion Lock (ADR-0058)**:
  + `python -m ccba_harness verify-patch --preset code` exit code 0.
- **Catalog Seam Governance (ADR-0061)**:
  + `python scripts/governance/compile_catalog.py --check` exit code 0.
