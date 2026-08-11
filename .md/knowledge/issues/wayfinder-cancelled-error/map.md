# Wayfinder Navigation Map: Khắc phục lỗi "User cancelled agent execution" liên tục

**Mã vấn đề**: `issue-wayfinder-cancelled-execution`
**Trạng thái bản đồ**: ✅ **Hoàn thành** — Ticket 1+2+3+4+5 hoàn thành
**Cập nhật**: 2026-07-22T11:33 — Hoàn tất Ticket 3 (Retry & Circuit Breaker cho ccba-ai SDK)

---

## 🎯 Điểm đích (Destination)

Agent CCBA Platform chạy ổn định toàn bộ các tác vụ nặng (Evaluations, Pytest suite, `/ccba-implement` loop) mà không bị ngắt giữa chừng bởi message misleading "User cancelled agent execution" khi người dùng **không hề thao tác cancel**.

---

## 📝 Ghi chú (Notes)

- **KISS**: Không thêm các thư viện phức tạp nếu cấu hình timeout đơn giản có thể giải quyết được.
- **Tránh Parallel Run**: Khi phát hiện lỗi quá tải, ép chạy tuần tự các test case.
- **Lưu ý gỡ lỗi**: Đọc trực tiếp file `transcript.jsonl` khi có lỗi xảy ra để định vị tool call cuối cùng trước khi bị ngắt.

---

## 📊 Phân Tích Forensic (Bằng chứng từ Log)

### Tổng quan 9 phiên gần nhất (21-22/07/2026)

| Session ID | Thời lượng | "User cancelled" | Server restart | Nguyên nhân chính |
| :--- | :--- | :--- | :--- | :--- |
| `dba19019` | 440 phút | 7 lần | **4 lần** (14:16, 14:17, 14:23, 14:24) | ⚡ Server Daemon Restart |
| `95cd16c2` | ~15 phút | 1 lần | 2 lần | ⚡ Server Daemon Restart |
| `7b5cab45` | ~75 phút | 0 | 4 lần | ⚡ Server Daemon Restart |
| `4f56855a` | ~9 phút | 6 lần | 0 | 🧠 Context Budget Exhaustion |
| `9be0891d` | ~65 phút | 15 lần | 0 | 🧠 Context Budget + Wayfinder nặng |
| `8ddf33a3` | ~25 phút | 1 lần | 0 | 🧠 Context Budget (CHECKPOINT truncation) |
| `1800601c` | 18 phút | 0 | 0 | 🧠 Context Budget (145 steps, 6 bg tasks, 4 errors) |

### Hai Root Cause đã xác nhận

#### Root Cause 1: ⚡ Server Daemon Restart (Ngoài tầm kiểm soát)

**Bằng chứng trực tiếp** từ `SYSTEM_MESSAGE` trong log:
```
[Notice] All your subagents and background tasks have been stopped due to server restart.
```
- Xảy ra ở sessions: `dba19019`, `95cd16c2`, `7b5cab45`
- Tần suất: 4 lần restart trong khoảng 8 phút (14:16 → 14:24) → Server không ổn định
- **Tác động**: Tất cả background tasks (pytest) bị kill → client hiển thị "User cancelled"

#### Root Cause 2: 🧠 Context Budget / Turn Limit Exhaustion

**Bằng chứng**:
- Session `1800601c` (phiên screenshot): 145 steps, 6 background tasks pytest, 4 error messages, 26 pytest references → agent liên tục lặp edit→test→edit→test cho đến khi hết budget
- Session `4f56855a`: 6 "User cancelled" nhưng **0 server restart** → không phải daemon issue
- Dấu hiệu `CHECKPOINT` truncation: Conversation quá dài, hệ thống cắt bớt context cũ
- Pattern: Agent chạy pytest full suite (`packages/ccba-legal-intel/tests`) thay vì scoped file → sinh nhiều output → đốt context nhanh

### Chuỗi sự kiện điển hình dẫn đến crash

```
[Agent bắt đầu /ccba-implement]
  → Viết code → pytest (FAIL) → Sửa code → pytest (FAIL) → Sửa code → ...
  → Mỗi vòng lặp tiêu tốn context (output pytest, code diff, error trace)
  → Sau ~15-20 vòng: context budget cạn kiệt
  → Agent cố chạy thêm lệnh nhưng model output lỗi: "invalid tool call (invalid_args)"
  → Hệ thống terminate → Client hiển thị "User cancelled agent execution"
```

---

## 📋 Quyết định đã chốt (Decisions so far)

1. **[Phân tích Log Lịch sử & Bằng chứng thực tế](#phân-tích-forensic-bằng-chứng-từ-log)** — Xác nhận 2 root cause riêng biệt: Server Daemon Restart + Context Budget Exhaustion.
2. **[Thiết lập Script Runner Cô lập (Ticket 1)](#ticket-1-thiết-lập-script-runner-cô-lập-detached-process-runner)** — `safe_runner.py` (commit `8ae987b`) cho phép chạy pytest detached khỏi daemon.
3. **[Phân rã Test Suite (Ticket 2)](#ticket-2-phân-rã--chạy-thử-nghiệm-test-suite-theo-lát-cắt-dọc)** — 23/23 tests pass qua `safe_runner.py`, không xảy ra "User cancelled".
4. **[Tích hợp Exponential Retry (Ticket 3)](#ticket-3-bổ-sung-exponential-retry-vào-ccba-ai)** — Retry + Exponential Backoff đã tích hợp vào ccba-ai SDK. Circuit Breaker giữ riêng ở skill api-circuit-breaker cho batch pipeline use case. 38/38 tests PASSED qua `safe_runner.py`.
5. **[Workflow Guard (Ticket 4)](#ticket-4-workflow-guard--giới-hạn-vòng-lặp-edittest-trong-ccba-implement-mới)** — Bổ sung Loop Budget (max 5 vòng/seam) vào AGENTS.md, implement SKILL.md, TDD SKILL.md.
6. **[Graceful Shutdown (Ticket 5)](#ticket-5-guardrail-invalid_args-error--phát-hiện-sớm--graceful-shutdown-mới)** — Bổ sung Invalid Args Circuit Breaker vào AGENTS.md và implement SKILL.md.

---

## 🚩 Frontier Tickets (Các ticket unblocked ở biên giới)

### Ticket 1: Thiết lập Script Runner Cô lập (Detached Process Runner)
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (commit `8ae987b`)
- **Giải quyết Root Cause**: ⚡ Server Daemon Restart
- **Kết quả**: `safe_runner.py` (151 LOC) — 3 mode: `--command`, `--status`, `--help`

### Ticket 2: Phân rã & Chạy thử nghiệm Test Suite theo lát cắt dọc
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (2026-07-22)
- **Kết quả**: 23/23 test cases PASSED (4.31s) qua `safe_runner.py`

### Ticket 3: Bổ sung Exponential Retry vào `ccba-ai`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (2026-07-22)
- **Giải quyết Root Cause**: ⚡ Server Daemon Restart (micro-restart 1-2 giây)
- **Kết quả**: Retry + Exponential Backoff đã tích hợp vào ccba-ai SDK. Circuit Breaker giữ riêng ở skill api-circuit-breaker cho batch pipeline use case. 38/38 tests PASSED.

### Ticket 4: Workflow Guard — Giới hạn vòng lặp Edit→Test trong `/ccba-implement`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (2026-07-22)
- **Giải quyết Root Cause**: 🧠 Context Budget Exhaustion
- **Kết quả**: Bổ sung "TDD Retry Cap" (max 5 vòng/seam) vào AGENTS.md (Layer 1), implement SKILL.md, TDD SKILL.md. Bắt buộc scoped pytest + full suite chỉ 1 lần cuối qua `safe_runner.py`.

### Ticket 5: Guardrail `invalid_args` Error — Phát hiện sớm & Graceful Shutdown
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (2026-07-22)
- **Giải quyết Root Cause**: 🧠 Context Budget Exhaustion
- **Kết quả**: Bổ sung "Invalid Args Circuit Breaker" vào AGENTS.md (Layer 1) và implement SKILL.md. Agent phải dừng ngay khi gặp `invalid_args` ≥ 2 lần liên tiếp.

---

### Ticket 6: Tự động Dọn Dẹp Zombie Process & Health Monitor
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ **Hoàn thành** (2026-07-22)
- **Giải quyết Root Cause**: ⚡ Tối ưu tài nguyên hệ thống & ngăn chặn tiến trình mồ côi
- **Kết quả**: Đã nâng cấp [session_cleanup.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/session_cleanup.py) tích hợp `clean_zombies()` và `health_check()`.

---

## 🚫 Ngoài phạm vi (Out of scope)

- Sửa lỗi Server Daemon Restart — đây là vấn đề infrastructure của Antigravity Platform, nằm ngoài tầm kiểm soát của CCBA. Chỉ có thể **mitigation** (Ticket 1, 3), không thể **fix root cause**.
- Thay đổi cách client hiển thị message "User cancelled" — đây là UX bug của Antigravity client, cần report upstream.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
