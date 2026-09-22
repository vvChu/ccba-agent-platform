# Biên Bản Phỏng Vấn Chuyên Sâu (Grilling Resolution): Kế Hoạch Khắc Phục Rủi Ro PR #325

> **Thời điểm xác lập**: 2026-09-22 17:06:00  
> **Phương pháp**: `/ccba-grilling` (Nhánh A: Standard Stress-Test theo Cây Thiết kế & Frontier Questions)  
> **Tham chiếu**: Báo cáo Đánh giá Đối kháng Chuyên sâu (`walkthrough.md` audit)  
> **Mục tiêu**: Hoàn thiện triệt để 5 hạng mục P1/P2 trên cả hai kho `ccba-agent-platform` và `dgx-spark-toolkit` trước ca chạy Nightly Auto-Tuner 00:00:00 đêm nay.

---

## 1. Danh Sách Quyết Định Thiết Kế Đã Thống Nhất (Decisions Matrix)

| STT | Quyết định (Decision) | Phương án Đã Chọn | Lý do Kỹ thuật & Tác động |
| :---: | :--- | :--- | :--- |
| **Q1** | **Phạm vi & Lộ trình Triển khai** | **Trọn gói P1 + P2 (cả 2 kho)** | Triển khai dứt điểm ngay trong phiên làm việc hiện tại để bảo đảm hạ tầng ổn định tuyệt đối trước ca chạy tự động 00:00:00. |
| **Q2** | **Xóa Nhánh Rác Git khi `total_commits == 0`** | **Tự động dọn dẹp tại chỗ trong `daemon.py`** | Khi ca chạy kết thúc với 0 commits (plateau, rollback), tự động checkout detach và `git branch -D {branch_name}`. Chống ô nhiễm rác branch cho cả ca Nightly lẫn /boost cô lập. |
| **Q3** | **Cơ chế Timeout Termination** | **Two-Phase Termination (SIGTERM $\rightarrow$ 5s $\rightarrow$ SIGKILL)** | Trong `chatops_daemon.py`, gửi `SIGTERM` trước để kích hoạt `trap cleanup_worktree EXIT INT TERM HUP` trong `run_boost_worktree.sh`, cho phép thu hồi sạch worktree. Chỉ cưỡng chế `SIGKILL` nếu quá 5s. |
| **Q4** | **Kiểm tra Kỹ năng & Xử lý Spam Telegram** | **Fail-Fast `exit 1` + cờ `--no-telegram`** | `run_boost_worktree.sh` kiểm tra `[ -d .agents/skills/$SKILL ]` trước khi tạo worktree; nếu sai tên $\rightarrow$ `exit 1` (ChatOps báo lỗi rõ ràng). Truyền `--no-telegram` khi gọi daemon để ChatOps độc quyền quản lý thông báo, chống spam tin nhắn kép. |
| **Q5** | **Kiểm soát Tải Nặng & Tranh chấp Lock Kernel** | **`is_heavy_op: true` + Kiểm tra non-blocking file lock `/tmp/...lock`** | Đổi `is_heavy_op: true` trong `chatops_commands.yaml` để ngăn chặn các tác vụ nâng cấp server đè lên /boost. Kiểm tra file lock vật lý tại ChatOps để bảo toàn `nonce` và thông báo ngay cho người dùng nếu cron đêm đang chạy. |

---

## 2. Danh Mục Tệp Cần Chỉnh Sửa

### 2.1. Phía Server: `dgx-spark-toolkit` (`/home/vvc/Codebase/dgx-spark-toolkit`)
1. **`scripts/chatops_commands.yaml`**:
   - Cập nhật `is_heavy_op: true` cho command `ccba.skill.boost`.
2. **`scripts/chatops_daemon.py`**:
   - Chuyển cơ chế tiêu diệt tiến trình khi timeout sang **Two-Phase Termination**: `SIGTERM` $\rightarrow$ `wait(5.0)` $\rightarrow$ `SIGKILL`.
   - Bổ sung kiểm tra non-blocking file lock `/tmp/ccba_nightly_runner.lock` trong `dispatch_action_by_nonce` và slash command `/boost`: nếu lock đang bận, thông báo thân thiện và hoàn trả nonce vào `action_cache`.
3. **Restart User Service**:
   - `systemctl --user restart dgx-chatops` và kiểm tra `systemctl --user status dgx-chatops`.

### 2.2. Phía Hub: `ccba-agent-platform` (`/home/vvc/ccba/ccba-agent-platform`)
1. **`scripts/eval/run_boost_worktree.sh`**:
   - **Fail-Fast**: Kiểm tra thư mục kỹ năng `$PROJECT_ROOT/.agents/skills/$SKILL` tồn tại trước khi tạo worktree; nếu không $\rightarrow$ `exit 1`.
   - **Signal Trap**: Mở rộng `trap cleanup_worktree EXIT INT TERM HUP`.
   - **Chống tin trùng lặp**: Truyền cờ `--no-telegram` vào lệnh gọi daemon.
2. **`packages/ccba-harness/src/ccba_harness/evals/daemon.py`**:
   - Bổ sung tham số `--no-telegram` vào CLI `nightly_tuner_daemon.py` / `NightlyTunerDaemon`.
   - Nếu `not dry_run and total_commits == 0`: tự động checkout detach và xóa nhánh `git branch -D {branch_name}`.
3. **Kiểm thử & CI**:
   - Bổ sung unit tests cho nhánh rỗng (`test_tuner_daemon.py`).
   - Chạy `verify-patch --preset ci` đạt 100% xanh trước khi mở PR.
4. **Cập nhật tài liệu**:
   - Cập nhật [walkthrough.md](file:///home/vvc/.gemini/antigravity/brain/fc58ab89-e6b3-4cdf-bd6c-4c4e31c3a85f/walkthrough.md) và `PLATFORM.md` với các hướng dẫn vận hành chuẩn xác (`systemctl --user`, đường dẫn `.worktrees/`).
