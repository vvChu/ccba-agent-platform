---
request_id: "req-plan-level3-dogfooding-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "code_review"
subject: "Thẩm định Kế hoạch Kỹ thuật: Thử Nghiệm Thực Chiến Level-3 Autonomous Loopback Dogfooding"
timestamp: "2026-10-11T15:20:00+07:00"
source_documents:
  - "docs/adr/0063-level-2-peer-delegation-protocol-and-cost-guardrails.md"
  - "docs/adr/0065-peer-runtime-hardening-and-topological-fail-closed.md"
output_path: ".md/peer_exchange/grok_review_plan_level3_dogfooding.md"
context: "Nghiệm thu Pass 1 (Planning Gate) cho Kế hoạch Thử nghiệm Thực chiến Level-3 Autonomous Loopback Dogfooding (--auto-apply)."
---

# 🔍 Yêu Cầu Thẩm Định Kế Hoạch Kỹ Thuật (Pass 1 Planning Gate): Level-3 Dogfooding

Chào Grok,

Thực hiện đúng chiến lược đã thống nhất tại `req-discuss-whats-next-001`, sau khi hoàn tất Giai đoạn 1 (Cập nhật ADR-0065 và mở PR #516 trên GitHub), Antigravity lập Kế hoạch Kỹ thuật chi tiết cho **Giai đoạn 2: Thử Nghiệm Thực Chiến Level-3 Autonomous Loopback Dogfooding (`peer-dispatch --auto-apply`)**.

Kính chuyển Grok thẩm định độc lập theo quy trình **Pass 1: Planning Gate** trước khi kích hoạt thực thi.

---

## Toàn Văn Kế Hoạch Kỹ Thuật

# Kế Hoạch Triển Khai: Thử Nghiệm Thực Chiến Level-3 Autonomous Loopback Dogfooding (Giai Đoạn 2)

Kế hoạch này thiết kế bài toán thử nghiệm thực chiến khép kín (end-to-end dogfooding) cho giao thức **Level-3 Autonomous Loopback** (`ccba-harness peer-dispatch --auto-apply` - [ADR-0063](file:///home/vvc/ccba/ccba-agent-platform/docs/adr/0063-level-2-peer-delegation-protocol-and-cost-guardrails.md) và [ADR-0065](file:///home/vvc/ccba/ccba-agent-platform/docs/adr/0065-peer-runtime-hardening-and-topological-fail-closed.md)), theo đúng phân tích và khuyến nghị chiến lược đã thống nhất với Grok tại `req-discuss-whats-next-001`.

---

## 🎯 1. Mục Tiêu Kỹ Thuật

Kiểm chứng thực tế cơ chế tự trị khép kín (Zero-Touch Loopback) của hệ thống harness mà **không có sự can thiệp thủ công của con người**:
1. **Pha 2A — Kiểm Chứng Hoàn Nguyên Giao Dịch (Rollback Invariant Verification)**:
   - Chứng minh khi worker (Grok) xuất một bản vá sinh lỗi kiểm thử (CI failure), hệ thống tự động hoàn nguyên (rollback) 100% về trạng thái ban đầu bằng `atomic_write_bytes`, không để lại working tree bị bẩn hay tệp rác mồ côi.
2. **Pha 2B — Kiểm Chứng Tự Động Nghiệm Thu (Auto-Apply & Commit Verification)**:
   - Chứng minh khi worker (Grok) xuất một bản vá chuẩn xác, hệ thống tự động áp dụng bản vá, chạy kiểm định `verify-patch` đạt mã thoát 0, tự động dọn dẹp backup và ghi nhận phán quyết thành công.
3. **Pha 2C — Minh Bạch Hóa Sổ Cái & Telemetry**:
   - Đối soát tự động số liệu tiêu thụ token, chi phí USD và session id vào [`.md/peer_exchange/status.json`](file:///home/vvc/ccba/ccba-agent-platform/.md/peer_exchange/status.json).

---

## 🔬 2. Thiết Kế Bài Toán Thử Nghiệm An Toàn (Safe Edge-Case Assertion)

Theo tư vấn đối kháng của Grok, để vừa kiểm thử toàn diện chu trình giao dịch vừa bảo đảm an toàn tuyệt đối cho logic lõi:
- **Tệp mục tiêu**: [`packages/ccba-harness/tests/test_peer_telemetry.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/tests/test_peer_telemetry.py)
- **Hàm cần kiểm thử biên**: `resolve_model_token_rates(model_id: str | None = None)`
- **Nội dung kiểm thử mới**:
  ```python
  def test_resolve_model_token_rates_edge_cases():
      """Verifies that empty string or None safely falls back to default rates."""
      from ccba_harness.telemetry import PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT, resolve_model_token_rates

      assert resolve_model_token_rates("") == (PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT)
      assert resolve_model_token_rates(None) == (PRICE_PER_M_INPUT, PRICE_PER_M_OUTPUT)
  ```

---

## 📋 3. Các Bước Triển Khai Chi Tiết

```
┌────────────────────────────────────────────────────────┐
│ PHA 2A: KIỂM CHỨNG HOÀN NGUYÊN (ROLLBACK TEST)         │
│ 1. Tạo prompt yêu cầu bản vá assertion sai cố ý       │
│ 2. Chạy: peer-dispatch --auto-apply --verify-preset ...│
│ 3. Harness áp dụng bản vá -> verify-patch exit != 0    │
│ 4. Harness tự rollback bằng atomic_write_bytes         │
│ 5. Xác nhận test file nguyên vẹn 100% (SHA-256 khớp)  │
└───────────────────────────┬────────────────────────────┘
                            │ (Rollback proven = True)
                            ▼
┌────────────────────────────────────────────────────────┐
│ PHA 2B: KIỂM CHỨNG TỰ ĐỘNG NGHIỆM THU (PASS TEST)      │
│ 1. Tạo prompt yêu cầu bản vá assertion đúng chuẩn      │
│ 2. Chạy: peer-dispatch --auto-apply --verify-preset ...│
│ 3. Harness áp dụng bản vá -> verify-patch exit == 0    │
│ 4. Harness tự dọn dẹp backup -> gate_verdict: APPROVE  │
│ 5. Xác nhận bài test mới được lưu giữ và pass 100%     │
└───────────────────────────┬────────────────────────────┘
                            │ (Auto-apply success = True)
                            ▼
┌────────────────────────────────────────────────────────┐
│ PHA 2C: LÀM MỚI SỔ CÁI & BÁO CÁO NGHIỆM THU            │
│ 1. Chạy peer-watch --once                              │
│ 2. Đối soát status.json & grok_live_summary.md         │
│ 3. Báo cáo tổng kết nghiệm thu Level-3 cho Operator    │
└────────────────────────────────────────────────────────┘
```

### Chi Tiết Pha 2A: Kiểm Chứng Hoàn Nguyên Khẩn Cấp (Rollback)
1. **Soạn thảo prompt phong bì**:
   - Tệp: `.md/peer_exchange/prompt_dogfood_level3_fail_rollback.md`
   - Request ID: `req-dogfood-l3-rollback-001`
   - Profile: `patch_fast` (cưỡng chế `max_turns: 1`, xuất `AnchorPatchPayload`)
   - Yêu cầu: Tạo bản vá chèn test assertion sai có chủ ý: `assert resolve_model_token_rates("") == (999.0, 999.0)`.
2. **Kích hoạt điều phối tự hành**:
   ```bash
   python -m ccba_harness peer-dispatch \
     --prompt-file .md/peer_exchange/prompt_dogfood_level3_fail_rollback.md \
     --profile patch_fast \
     --auto-apply \
     --verify-preset telemetry
   ```
3. **Tiêu chí nghiệm thu Pha 2A**:
   - Lệnh thoát với mã `1` (thông báo hoàn nguyên thành công).
   - Nhật ký ghi nhận: `Rollback completed and proven against SHA-256 preimages`.
   - Tệp `packages/ccba-harness/tests/test_peer_telemetry.py` được hoàn nguyên 100% về mã băm ban đầu.

---

### Chi Tiết Pha 2B: Kiểm Chứng Áp Dụng Tự Động & Nghiệm Thu (Auto-Apply)
1. **Soạn thảo prompt phong bì**:
   - Tệp: `.md/peer_exchange/prompt_dogfood_level3_pass_commit.md`
   - Request ID: `req-dogfood-l3-pass-001`
   - Profile: `patch_fast`
   - Yêu cầu: Tạo bản vá chèn test assertion chuẩn xác cho `resolve_model_token_rates` (kiểm tra `""` và `None`).
2. **Kích hoạt điều phối tự hành**:
   ```bash
   python -m ccba_harness peer-dispatch \
     --prompt-file .md/peer_exchange/prompt_dogfood_level3_pass_commit.md \
     --profile patch_fast \
     --auto-apply \
     --verify-preset telemetry
   ```
3. **Tiêu chí nghiệm thu Pha 2B**:
   - Lệnh thoát với mã `0`.
   - Nhật ký ghi nhận: `Auto-apply and verification SUCCEEDED`.
   - Toàn bộ test suite `pytest packages/ccba-harness/tests/test_peer*.py` đạt **88/88 passed** (bổ sung thêm 1 test mới).

---

### Chi Tiết Pha 2C: Thu Thập Telemetry & Đồng Bộ Sàn Trao Đổi
1. Thực thi `python -m ccba_harness peer-watch --once` để quét delta 2 phiên dogfooding.
2. Kiểm tra `status.json` ghi nhận chính xác 2 cuộc gọi mô hình `qwen-local` ($0.00 USD) hoặc gateway model tương ứng.
3. Xuất báo cáo nghiệm thu dogfooding Level-3.

---

## 🛡️ 4. Ma Trận Đảm Bảo Rủi Ro (Safety Guardrails)

| Rủi Ro Tiềm Ẩn | Biện Pháp Kiểm Soát & Rào Chắn |
| :--- | :--- |
| **Grok sinh bản vá sai vị trí mỏ neo (Anchor Mismatch)** | Engine `apply_anchor_patch` kiểm tra chặt chẽ `blob_sha256` trước khi ghi; nếu không khớp preimage, lập tức hủy giao dịch mà không chạm vào tệp trên đĩa. |
| **Nghẽn tiến trình khi chạy `verify-patch`** | Verification runner có timeout xác định (mặc định 180s); nếu timeout, tự động kích hoạt `_terminate_proc_tree` và hoàn nguyên. |
| **Khóa tệp trên Windows khi rollback** | Sử dụng `atomic_write_bytes` với cơ chế retry lũy tiến 3 lần đã được kiểm chứng ở Option 2. |
| **Tệp rác mồ côi** | Thư mục `.md/backups/anchor-txn/` được dọn dẹp tự động khi giao dịch thành công hoặc khi hoàn nguyên thành công (trừ khi có cờ `--keep-backups`). |


---

## Tiêu Chí Đánh Giá Cho Reviewer
1. **Tính Toàn Vẹn Của Kịch Bản 2 Pha**: Kịch bản kiểm chứng Rollback (Pha 2A) và Auto-Apply (Pha 2B) có đủ bao phủ các điều kiện biên của giao dịch mỏ neo ACID không?
2. **Độ An Toàn Của Bài Toán Thử Nghiệm**: Việc chọn edge-case test cho `resolve_model_token_rates` có bảo đảm tính cô lập, không gây rủi ro phụ cho codebase chính không?
3. **Tuân Thủ Invariants**: Đối soát với ADR-0058 (Deterministic Gate), ADR-0063 (Turn Caps), ADR-0064 (Zero-Hang & Telemetry), ADR-0065 (Fail-Closed Rollback).

## Định Dạng Đầu Ra Yêu Cầu

Vui lòng xuất ngay khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp phản hồi:

```yaml
---
request_id: "req-plan-level3-dogfooding-001"
verdict: APPROVE | APPROVE_WITH_CONDITIONS | REJECT
conditions: []
risk_score: 1-5
effort: XS | S | M | L | XL
summary: "Tóm tắt 1-2 câu kết luận thẩm định kế hoạch kỹ thuật."
---
```

Tiếp theo là phần nhận xét chi tiết và phê duyệt để kích hoạt triển khai.
