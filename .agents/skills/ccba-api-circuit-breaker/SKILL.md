---
name: ccba-api-circuit-breaker
description: Rate limiter + Circuit Breaker pattern cho LLM API calls trong batch
  pipelines. Tránh quota exhaustion, cascade failures, và infinite retry loops khi
  gọi AI Gateway hàng loạt.
applies_to:
- Phần mềm
- Kiểm định
bundle: _software
scope: universal
posture: package-bound
tier: kernel
command: /ccba-api-circuit-breaker
metadata:
  version: "1.4.0"
  author: "CCBA Hub"
dependencies:
- ccba-ai-gateway-sdk
gpi:
  s: 3.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- circuit breaker
- rate limit
- rpm
- throttle
- batch api
- api protection
- quota
- retry
- auto downgrade
- soft cooldown
---

# API Circuit Breaker

Rate limiter + Circuit Breaker 3-trạng-thái cho LLM API calls. Thiết kế cho các pipeline gọi AI Gateway **hàng loạt** (batch QC, wiki healing, domain enrichment) và các kiến trúc Multi-Endpoint tự phục hồi (Self-Healing).

> **Nguồn**: VvC Wiki Health v7.4 → LLM OS v8.15 (2026) — giải quyết lỗi quota exhaustion khi wiki healer gọi LLM cho 300+ concept stubs liên tiếp không throttle, và cơ chế Soft Cooldown tự động giáng cấp (Auto-Downgrade) khi Cổng Proxy chuyên biệt đạt giới hạn tài khoản.

---

## Cách sử dụng trong CCBA Batch Pipeline

Khởi tạo 1 instance `CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)` từ `ccba_ai.circuit_breaker`, kiểm tra `breaker.allow_request()` trước mỗi call `ai.chat(..., model=choose_model("general"))`, và cập nhật `record_success()` / `record_failure(exc)`. Xem code mẫu đầy đủ trong `references/circuit_breaker_recipes.md`.

---

## Tự động kiểm soát và sửa lỗi (Self-Healing)

Khi Circuit Breaker mở hoặc gặp lỗi API, `ccba_ai` xuất cấu trúc JSON ra `stderr` (`status="error"`, `error_code="CIRCUIT_BREAKER_OPEN"`, `recovery_suggestion`) để LLM Agent đọc `recovery_suggestion`, chuyển sang model dự phòng hoặc tạm dừng luồng an toàn.

### Cơ chế Kháng lỗi Ngân sách LiteLLM & Local Fallback (RULE-2.12)
LiteLLM Gateway v1.83+ trả về lỗi ngân sách dưới cả JSON `{"type": "budget_exceeded"}` lẫn chuỗi `Budget has been exceeded! ...` (khớp `"budget" in str(e).lower() and "exceeded" in str(e).lower()`):
- **Fast-Fail tức thì:** Ngắt ngay sang `CircuitState.OPEN` không chờ đủ `failure_threshold`.
- **Cảnh báo chuẩn:** Xuất `CCBAErrorCode.CIRCUIT_BREAKER_OPEN` ra `stderr`, chuyển sang mô hình cục bộ via `choose_model("local")`.
- **Chống Retry vô hạn:** Kết hợp `cache_rejected()` bỏ qua item lỗi ở các vòng sau.

---

## Centralized Gateway (:8090) & Soft Cooldown Auto-Downgrade Pattern

Toàn bộ archetypes tập trung tại Gateway duy nhất `:8090` (`http://${CCBA_AI_GATEWAY_HOST}:8090/v1`, bỏ `:8045`). Khi upstream trả `503`/`429` trên task `reasoning`:

```
Request (task="reasoning") -> [In 30s Cooldown?]
  ├── Yes -> [Auto-Downgrade to Fallback General (:8090), was_downgraded=True]
  └── No  -> Gateway :8090
               ├── HTTP 200 -> Result (was_downgraded=False)
               └── HTTP 503/429 -> Set 30s cooldown -> Fallback General (:8090)
```

- **Transparency UI Callout Invariant:** Khi `was_downgraded == True`, chèn callout `[!info]` thông báo minh bạch đang dùng mô hình dự phòng (xem mẫu & implementation `call_gateway_with_meta` tại `references/circuit_breaker_recipes.md`).
- **Rejected Items Caching:** Lưu item lỗi vào `.rejected_items.json` qua `load_rejected_cache()` / `cache_rejected()` để tránh infinite retry.

---

## Sơ đồ Trạng thái (3-State Diagram)

```
          success (HALF_OPEN)
    ┌────────────────────────────────┐
    │                                ▼
[CLOSED] ──fail×N──► [OPEN] ──30s──► [HALF_OPEN]
    ▲                                    │
    └────────── success ─────────────────┘
                         fail → back to OPEN
```

## Tiêu chí hoàn thành & Progressive Disclosure (Level 3)

- **Tiêu chí hoàn thành:** Thay đổi pipeline/skill phải vượt qua `python -m ccba_harness verify-patch` với exit code 0, xử lý ngoại lệ tường minh và giữ `tests/` không suy giảm.

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/circuit_breaker_recipes.md` | Code mẫu `CircuitBreaker` batch loop, Soft Cooldown Auto-Downgrade (`:8090`), UI callout và Rejected Items Caching |
