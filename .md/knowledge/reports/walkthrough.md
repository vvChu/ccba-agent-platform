# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — PR #644 (Peer Protocol v2 `audit_direct` Preamble Guard & In-Place Synthesis)
## Feature: `fix(harness): prevent audit_direct preamble-only stop and enable in-place synthesis`

> **Nguồn Kiểm Toán:** Kiểm toán hiệu quả vận hành thực tế 7 phiên Grok sau nâng cấp v2 (`c400b5f7`, `c67c2f8c`, `fa67f7de`, `082a3d79`, `7c138c28`, `032c5a43`, `014f6ddd`) dưới cơ chế Peer Coordination Protocol v2 (`ADR-0063..0067`)
> **Pull Request:** [#644](https://github.com/vvChu/ccba-agent-platform/pull/644) (`38eb2efe`) — tiếp nối [#638](https://github.com/vvChu/ccba-agent-platform/pull/638) (`e7e01b18`) và [#632](https://github.com/vvChu/ccba-agent-platform/pull/632) (`6ecd4998`)
> **Branch:** `fix/peer-audit-direct-preamble-synthesis`
> **Trạng thái:** ✅ **12/12 TEST TARGETS PASS, 97/97 PEER TESTS PASS, 8/8 CI CHECKS PASS, SQUASH MERGED**

---

## 1. Tổng Kết Thay Đổi Kiến Trúc & Quản Trị (`PR #644` & `PR #638`)

| Hạng Mục / Component | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **Explicit Tool Ban in `audit_direct` System Prompt (`PR #644`)** | `packages/ccba-harness/src/ccba_harness/_peer_watchdog.py` | Khắc phục cách hiểu nhầm `"no external tools"` trong reasoning trace của phiên `7c138c28`: khẳng định rõ mọi công cụ (bao gồm `read_file`, `grep`, `list_dir`, `bash` cục bộ) đều bị vô hiệu hóa, cấm xuất câu mở đầu hứa hẹn đọc file và yêu cầu mở đầu ngay bằng `---` YAML frontmatter. | Verified |
| **Single-Turn Preamble-Only Synthesis Recovery (`PR #644`)** | `packages/ccba-harness/src/ccba_harness/_peer_watchdog.py`, `peer.py`, `tests/test_peer.py` | Mở rộng `is_max_turns_exhausted()` và `_dispatch_grok_candidate()` để kích hoạt 1 lượt In-place Synthesis (`--resume <session_id>`) ngay trên `grok-4.7` khi Turn 1 kết thúc sớm (`outcome == "completed"`, `turn_ends == 1`, có `chat_history.jsonl`) mà thiếu YAML verdict, trước khi fallback sang `gemini-38-flash`. | Verified |
| **In-Place Synthesis Watchdog Guard (`min_timestamp`, `PR #638`)** | `packages/ccba-harness/src/ccba_harness/_peer_watchdog.py` | Bổ sung `min_timestamp` vào `inspect_session_liveness()` (truyền `min_timestamp=start_time` từ `_poll_grok_process_with_watchdog()`) để bỏ qua sự kiện `turn_ended` cũ khi tiến trình Turn 2 đang boot in-place (`fork_session=False`). | Verified |
| **Turn-Boundary Verdict Recovery & `is_aborted` Guard (`PR #638`)** | `packages/ccba-harness/src/ccba_harness/_peer_watchdog.py`, `peer.py` | Dừng vòng lặp quét ngược `_recover_verdict_from_chat_history()` ngay tại ranh giới `"type": "user"` của lượt hiện tại và kiểm tra `not is_aborted` trước khi khôi phục, chặn triệt để rò rỉ verdict Stage 1 sang Stage 3. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Tự Động (`ADR-0058`)

- **Hiệu quả vận hành Peer Protocol v2 trên dữ liệu thực (`~/.grok/sessions/`)**:
  - **Phiên `014f6ddd` (`VvC_Notes` FUSE Errno 5 Plan Review, `2026-11-07 06:15+07:00`)**: `grok-4.7-build` (`audit_direct`) hoàn tất trong **1 lượt (`292.51s`, `$0.0464` exact)** với **`12,810` reasoning tokens**, **`16,300` output tokens**, **`123.2 MB` Peak RSS**, `0` MCP server overhead, xuất chuẩn xác `APPROVE_WITH_CONDITIONS` (`C1..C7`).
  - **Khóa kẽ hở `7c138c28` $\to$ `032c5a43`**: Ngăn chặn việc `grok-4.7-build` dừng lượt sau 3 câu mở đầu (*"I am reading those modules..."*) và bảo đảm retry synthesis in-place giữ nguyên KV-cache trên `grok-4.7`.
- **GitHub Actions CI & Copilot Review trên PR #644**:
  - **8/8 CI Checks PASS** (`PR Danger Triage & Verifier Gate`, `Deterministic Parity & Schema Audit`, `Lint Markdown`, `Test - Python 3.10/3.11/3.12`, `Security & Privacy Scan`, `Documentation Check`).
  - `audit_pr_comments.py`: `[OK] All Copilot reviews and comments on PR #644 are clean or resolved.`
