# CCBA Execution Runtime Guardrails & Async Task Policy

> **Tài liệu Tham chiếu Quy chuẩn Thực thi Runtime & Tác vụ Ngầm (Layer 2 — SSOT)**  
> Áp dụng cho các tác vụ chạy lệnh, kiểm thử, quản trị tiến trình nền và cách ly môi trường trên CCBA Platform.  
> Đối với quy chuẩn điều phối đa tác nhân, GitHub remote và giao thức ngang hàng, xem [`docs/rules/execution_coordination_guardrails.md`](execution_coordination_guardrails.md).

## 🧭 Bảng Điều Hướng Nhanh (Runtime Navigation Index)

| Nhóm Quy Chuẩn (Category) | Các Mục Quy Chuẩn (Sections) |
| :--- | :--- |
| **I. Thực Thi Kiểm Thử & Tiến Trình Ngầm** | [1. Scoped Test](#1-scoped-test-execution-kiểm-thử-cô-lập) · [2. Bounded Async & Reactive Wakeup](#2-bounded-async-task-zero-polling--reactive-wakeup-invariant) · [3. TDD Retry Cap](#3-tdd-retry-cap--early-escalation-giới-hạn-vòng-lặp--điểm-cắt-lỗi) · [4. Anti-Duplicate Runner](#4-anti-duplicate-background-runner) · [5. Safe Process Termination](#5-safe-process-termination-invariant) · [6. Task Log Readiness](#6-task-log-readiness-check) · [7. Invalid Args Breaker](#7-invalid-args-circuit-breaker) · [8. 2-Tier Test Speed](#8-2-tier-test-speed-compliance) |
| **II. Hooks & Đa Nền Tảng** | [11. Antigravity Lifecycle Hooks](#11-antigravity-lifecycle-hooks-policy-chính-sách-móc-vòng-đời-antigravity--adr-0054) · [14. Cross-Platform Machine-State Isolation](#14-cross-platform-machine-state-isolation--environment-parity-invariant-quy-chuẩn-cách-ly-trạng-thái-máy--đồng-bộ-đa-nền-tảng) |
| **III. Trình Duyệt & Worktree** | [15. Chrome CDP Automation](#15-chrome-devtools-protocol-cdp--browser-agent-automation-invariant-quy-chuẩn-tự-động-hóa-trình-duyệt--bảo-mật-cdp) · [16. Ephemeral Worktree & Nightly Cron](#16-ephemeral-worktree--automated-nightly-cron-invariant-quy-chuẩn-vận-hành-worktree-tạm-thời) · [17. Spoke CLI Parameter Symmetry](#17-spoke-cli-parameter-symmetry--safe-invocation-invariant-quy-chuẩn-chữ-ký-tham-số--an-toàn-thực-thi-spoke-cli) |
| **IV. Điều Phối Đa Tác Nhân & Remote** | Xem tài liệu bổ trợ: [`execution_coordination_guardrails.md`](execution_coordination_guardrails.md) (Mục 9, 10, 12, 13, 18, 19, 20) |

---

## 1. Scoped Test Execution (Kiểm thử Cô lập)
- Nghiêm cấm kích hoạt kiểm thử toàn diện không khoanh vùng (unscoped `pytest`) trên toàn bộ repository.
- Luôn chỉ định rõ file test hoặc module mục tiêu (`pytest packages/{pkg}/tests/test_file.py`) kèm `WaitMsBeforeAsync=10000` (10s) để lệnh hoàn tất đồng bộ ngay trong lượt gọi đầu tiên, hoặc dùng cờ loại trừ `-m "not slow and not stress"`.

---

## 2. Bounded Async Task, Zero-Polling & Reactive Wakeup Invariant
- Khi một lệnh chuyển sang chạy ngầm (Background Task) như `pytest`, `peer-dispatch`, hoặc `gh pr checks --watch`:
  - **Nguyên lý Reactive Wakeup (Bắt buộc):** Runtime tự động đánh thức và gửi `<SYSTEM_MESSAGE>` ngay khi tác vụ nền hoàn thành.
  - **Chính sách Không Polling Tuyệt Đối (Zero-Tolerance Polling Policy):**
    - Nghiêm cấm lặp `manage_task status` để thăm dò trạng thái tiến trình nền.
    - **Hành động bắt buộc ngay sau khi lệnh chuyển sang Background Task:**
      1. **Dừng gọi công cụ (End Turn):** Thông báo ngắn gọn cho người dùng và kết thúc lượt ngay để hệ thống tự động đánh thức khi hoàn tất; **hoặc**
      2. **Làm việc song song có ích (Parallel Work):** Soạn thảo tài liệu hoặc phân tích mã nguồn độc lập khác trong lúc chờ.
  - **Rào chắn theo dõi CI & Copilot Review (`gh pr checks`):** Khởi chạy `gh pr checks <id> --watch` rồi dừng lượt chờ Reactive Wakeup. Nghiêm cấm chạy `gh pr merge` khi `gh pr view <id> --json reviewRequests` vẫn còn `copilot-pull-request-reviewer`.

---

## 3. TDD Retry Cap & Early Escalation (Giới Hạn Vòng Lặp & Điểm Cắt Lỗi)
- Trong vòng lặp Red $\rightarrow$ Green $\rightarrow$ Refactor, chỉ được thử tối đa **5 vòng** cho cùng một seam hoặc test file:
  - **Cắt lỗi sớm tại vòng 3 (Early Escalation):** Nếu sau 3 vòng liên tiếp vẫn lỗi do logic sâu hoặc race condition, dừng đoán mò và đóng gói **Deep Problem Brief** (Mục 9 `execution_coordination_guardrails.md`).
  - **Dừng cứng tại vòng 5 (Hard Stop):** Commit WIP, xuất Deep Problem Brief và kích hoạt **Boost Escalation Gate** (Mục 9 `execution_coordination_guardrails.md`) — tuyệt đối không lặp tiếp làm cạn ngân sách ngữ cảnh.

---

## 4. Anti-Duplicate Background Runner
- Nghiêm cấm kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner hoặc harness evaluation.
- Mọi script runner ngầm bắt buộc tích hợp khóa đơn tiến trình (`ensure_single_instance`) và kiểm tra tiến trình cũ trước khi khởi động.

---

## 5. Safe Process Termination Invariant
- Khi viết hoặc thực thi logic dọn dẹp tiến trình (`ensure_single_instance`), **bắt buộc loại trừ** cả tiến trình hiện tại (`os.getpid`) và tiến trình cha (`os.getppid`).
- Nghiêm cấm gọi `taskkill` hoặc `proc.terminate` lên `os.getppid` để tránh làm sập Agent Server Host.

---

## 6. Task Log Readiness Check
- Nghiêm cấm gọi `view_file` tới `task-XXX.log` ngay sau lượt `run_command` async khi chưa nhận được thông báo hoàn tất từ hệ thống hoặc kiểm tra trạng thái qua `manage_task status`.

---

## 7. Invalid Args Circuit Breaker
- Khi gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên** (dấu hiệu cạn kiệt context budget), Agent phải **dừng ngay lập tức**, commit WIP, tóm tắt trạng thái và đề nghị người dùng mở phiên mới (hoặc dùng `/compact`).

---

## 8. 2-Tier Test Speed Compliance
- Mọi Unit Test mới bắt buộc chạy dưới **2.0 giây**.
- Các bài test tích hợp mạng, Chromium CDP, hoặc LLM thực tế bắt buộc gắn decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để loại trừ khỏi vòng kiểm thử nhanh (`-m "not slow"`).

---

## 11. Antigravity Lifecycle Hooks Policy (Chính Sách Móc Vòng Đời Antigravity) — ADR 0054
- File `scripts/hooks/antigravity_hook_bridge.py` đóng vai trò **Adapter Layer mỏng** dịch schema giữa Antigravity IDE (`toolCall.name` / `toolCall.args` camelCase) và `HookCoordinator` (snake_case, cùng chia sẻ 7 hooks với CLI `hook_runner.py`).
- Chỉ kích hoạt ở bước `"PreToolUse"` trên matcher `run_command|write_to_file|replace_file_content|multi_replace_file_content`.
- **Fail-Safe Default:** Mọi ngoại lệ không mong muốn trong bridge đều trả về `{"decision": "allow"}` để không làm gián đoạn IDE.

---

## 14. Cross-Platform Machine-State Isolation & Environment Parity Invariant (Quy Chuẩn Cách Ly Trạng Thái Máy & Đồng Bộ Đa Nền Tảng)
1. **Ưu tiên `$CCBA_HUB_PATH`:** Mọi script phân giải vị trí Hub/Spoke phải ưu tiên đọc biến môi trường `$CCBA_HUB_PATH`.
2. **An toàn đường dẫn đa hệ điều hành:** Trên Linux/WSL/POSIX, không truyền trực tiếp chuỗi ổ đĩa Windows (`D:\...`, `C:\...`) vào `pathlib.Path`; bắt buộc dùng `resolve_cross_platform_path`.
3. **Chống rò rỉ trạng thái máy (ADR-0061):** Cấm commit đường dẫn tuyệt đối cục bộ (`/home/...`, `C:/...`) hoặc IP cứng; kiểm định qua `check_spoke_cleanliness.py`.
4. **Chuẩn hóa LF & Ngân sách In-Memory:** Mọi repo phải có `.gitattributes` (`* text=auto eol=lf`). Ngưỡng dung lượng tài liệu (như 10.0 KB của `session_learnings.md`) phải tính sau khi chuẩn hóa `content.replace("\r\n", "\n").encode("utf-8")`.
5. **Sharded Legal Registry Gate:** Tại các Spoke có `legal_docs/`, lệnh `ccba-legal compile-registry --check` bắt buộc trả về exit code 0 trước khi commit.
6. **Skills Hygiene Bash Labeling:** Các khối bash trong `SKILL.md` có lệnh `export` phải ghi nhãn ````bash (linux)````.

---

## 15. Chrome DevTools Protocol (CDP) & Browser Agent Automation Invariant (Quy Chuẩn Tự Động Hóa Trình Duyệt & Bảo Mật CDP)
- **Bắt buộc `--remote-allow-origins=*` & Khóa Loopback `127.0.0.1`:** Mọi lệnh mở Chrome Debug trên cổng `9222` (SSOT duy nhất) phải kèm `--remote-allow-origins=*` và chỉ lắng nghe trên `127.0.0.1` (cấm `0.0.0.0`).
- **Attach-First & Profile Dùng Chung:** Dùng chung profile bền vững `~/.gemini/antigravity-browser-profile`; tự động dọn `~/.gemini/antigravity-browser-profile/LOCK` bị treo nếu cổng `9222` trống.
- **Dừng An Toàn Chọn Lọc:** Chỉ tắt tiến trình gắn với cổng `9222` hoặc `antigravity-browser-profile`; nghiêm cấm `taskkill /IM chrome.exe /F` hàng loạt.

---

## 16. Ephemeral Worktree & Automated Nightly Cron Invariant (Quy Chuẩn Vận Hành Worktree Tạm Thời)
- **Cách ly Worktree & Chống rò rỉ đường dẫn import:** Mọi tác vụ auto-tuner/telemetry tự động phải chạy trong detached worktree (`.worktrees/` đã khai báo trong `.gitignore`) và đặt lại đường dẫn tìm kiếm gói Python ưu tiên trỏ vào worktree trước khi chạy test:
  ```bash (linux)
  export PYTHONPATH="$worktree_dir/packages/ccba-harness/src:$worktree_dir/packages/ccba-ai/src:$worktree_dir"
  ```
- **Fast-Forward Guard & Dynamic Branching:** Dùng hậu tố nhánh động `docs/auto-refactor-YYYYMMDD_HHMMSS`. Không chép ngược untracked files vào workspace chính; chỉ `git merge --ff-only origin/main` khi working tree chính hoàn toàn sạch.
- **Kiểm tra tiến trình trước khi xóa Worktree (`Active Lock Protection`):** Trước khi `git worktree remove` hoặc xóa lock file, bắt buộc kiểm tra bằng `fuser -v "$worktree_dir"` và `flock -n "$lock_file" -c "true"`; cấm xóa khi tiến trình đang hoạt động.

---

## 17. Spoke CLI Parameter Symmetry & Safe Invocation Invariant (Quy Chuẩn Chữ Ký Tham Số & An Toàn Thực Thi Spoke CLI)
1. **Bộ Script Độc Lập (`scripts/`):**
   - `python scripts/sync_spoke.py --spoke <path> [--apply]`: Mặc định chạy xem trước (Preview); bắt buộc truyền `--apply` để ghi đĩa.
   - `python scripts/adopt_spoke.py --spoke <path> [--dry-run]`: Mặc định áp dụng trực tiếp; truyền `--dry-run` để xem trước (cấm truyền `--apply`).
   - `python scripts/init_spoke.py <spoke_path>` (hoặc `-p <spoke_path>`): Nhận tham số vị trí (cấm truyền `--spoke`).
2. **CLI Hợp Nhất (`scripts/ccba_platform_cli.py`):** Cả 3 lệnh `init-spoke`, `adopt-spoke`, `sync-spoke` đều nhận `<spoke_path>` là **tham số vị trí** (cấm truyền `--spoke`).
