# 📜 Biên Bản Quyết Định Thiết Kế (Grilling Decision Log)

> **Mã Phiên Grilling:** `GRILL-NIGHTLY-TUNER-20260918`  
> **Chủ Đề:** Hội tụ thiết kế kiến trúc cô lập môi trường và khắc phục sự cố Nightly Tuner Daemon  
> **Kỹ Năng Thực Thi:** `ccba-grilling` $\times$ `ccba-issue-tree`  
> **Thời Gian:** 2026-09-18 06:14:30 (+07:00)

---

## 1. Tóm Tắt Các Quyết Định Được Chốt (Frontier Decisions)

Qua 4 vòng phỏng vấn đối kháng Socrates dồn dập (Grilling Loop), người dùng và Agent đã hội tụ 100% về các quyết định thiết kế:

| Vòng (Round) | Hạng Mục Thiết Kế (Design Scope) | Quyết Định Được Chốt (Committed Decision) | Lý Do & Phân Tích Đối Kháng (Rationale) |
| :---: | :--- | :--- | :--- |
| **Vòng 1** | **Kiến Trúc Cô Lập Môi Trường (Workspace Isolation)** | **Git Worktree Chuyên Dụng** (`.worktrees/nightly-runner`) | Triệt tiêu hoàn toàn rủi ro Working Tree bẩn của developer/agent. Tách biệt 100% không gian chạy cron khỏi branch làm việc dở dang mà không tốn dung lượng đĩa nhân bản repository. |
| **Vòng 2** | **Vòng Đời & Quản Trị Dọn Dẹp (Worktree Lifecycle)** | **Idempotent Ephemeral Worktree** (Trap `EXIT` + Force Pre-clean) | Trước khi chạy, luôn kiểm tra và dọn dẹp cưỡng chế nếu worktree cũ còn sót lại từ lần chạy trước (phòng ngừa crash/OOM/kill). Đồng thời gắn trap `EXIT` để tự động thu hồi tài nguyên ngay khi script hoàn thành. |
| **Vòng 3** | **Cơ Chế Bắt Lỗi & Cảnh Báo Khẩn Cấp (Shell Error Trap)** | **Trap `ERR` Tích Hợp Python One-Liner** (`telegram_alert.py`) | Tái sử dụng trọn vẹn module `telegram_alert.py` đã có cấu hình Telegram Bot Token, Chat ID, parse mode Markdown và fallback an toàn. Bắn alert ngay lập tức khi shell script văng exit code $\ne 0$. |
| **Vòng 4** | **Trình Tự Triển Khai & Chạy Bù (Execution Sequence)** | **Stash Tạm $\rightarrow$ Nâng Cấp Script $\rightarrow$ Live Run Chạy Bù** | Đảm bảo an toàn 100% cho uncommitted code trên nhánh `proposal/dynamic-base-branch-for-create-pr`, sau đó kích hoạt kịch bản mới để vừa nghiệm thu thực tế kiến trúc Worktree vừa chạy bù chu trình tối ưu cho ngày 18/09/2026. |

---

## 2. Đặc Tả Kỹ Thuật Chi Tiết Kịch Bản Nâng Cấp (`scripts/cron/run_nightly_tuner.sh`)

```bash
#!/bin/bash
# run_nightly_tuner.sh - Isolated Ephemeral Worktree Runner for Server Spark (:8090)
# Schedule: 0 0 * * * (Every midnight at 00:00 AM)

set -euo pipefail

# 1. Environment & Locales
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:/snap/bin:${PATH:-}"
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"
export PYTHONIOENCODING="utf-8"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 2. Auto-load .env secrets
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# 3. Emergency Error Trap (Python Telegram Alert)
on_error() {
    local exit_code=$?
    local failed_line=$1
    local failed_cmd=$2
    echo "🚨 [FATAL ERROR] Nightly Tuner thất bại tại dòng $failed_line (cmd: '$failed_cmd', exit: $exit_code)" >&2
    python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')
from scripts.eval.telegram_alert import send_telegram_alert
send_telegram_alert(
    message='🚨 *[CCBA CRON FAILURE] Nightly Daemon Thất Bại!*\\n'
            '• *Thời gian:* $(date \"+%Y-%m-%d %H:%M:%S\")\\n'
            f'• *Dòng lỗi:* \`line $failed_line\`\\n'
            f'• *Lệnh lỗi:* \`$failed_cmd\`\\n'
            f'• *Exit Code:* \`$exit_code\`\\n'
            '• *Chi tiết:* Xem log \`.md/logs/nightly_cron.log\`',
    parse_mode='Markdown',
    mock_fallback=True
)
" 2>/dev/null || true
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

# 4. Tri-Repo Sequential Pull Gate (ADR 0042)
BASE_DIR="$(cd "$PROJECT_ROOT/.." && pwd)"

if [ -d "$BASE_DIR/ccba-legal-knowledge" ]; then
    echo "🔄 Updating ccba-legal-knowledge..."
    cd "$BASE_DIR/ccba-legal-knowledge" && git fetch origin main && git checkout -q main && git pull -q origin main || echo "⚠️ Warning: Failed to pull ccba-legal-knowledge"
fi

if [ -d "$BASE_DIR/IDOP-CCBA-WAY" ]; then
    echo "🔄 Updating IDOP-CCBA-WAY..."
    cd "$BASE_DIR/IDOP-CCBA-WAY" && git fetch origin main && git checkout -q main && git pull -q origin main || echo "⚠️ Warning: Failed to pull IDOP-CCBA-WAY"
fi

# 5. Setup Ephemeral Worktree Runner
WORKTREE_DIR="$PROJECT_ROOT/.worktrees/nightly-runner"

cleanup_worktree() {
    echo "🧹 Đang thu hồi tài nguyên Ephemeral Worktree..."
    cd "$PROJECT_ROOT"
    if [ -d "$WORKTREE_DIR" ]; then
        git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
    fi
    git worktree prune 2>/dev/null || true
    echo "✅ Đã dọn dẹp hoàn tất."
}
trap cleanup_worktree EXIT

echo "================================================================="
echo "[CCBA Nightly Auto-Tuner Daemon] Starting at $(date)"
echo "================================================================="

# Pre-clean if any stale worktree exists
cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/.worktrees"
if [ -d "$WORKTREE_DIR" ]; then
    git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
fi
git worktree prune 2>/dev/null || true

# Fetch latest main without modifying current user working tree
git fetch origin main

# Create detached ephemeral worktree from origin/main
git worktree add --detach "$WORKTREE_DIR" origin/main

# Activate virtualenv inside worktree context
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

cd "$WORKTREE_DIR"

# 6. Run Document Auto-Evolution Engine
echo "📚 [1/2] Running Document Auto-Evolution Engine..."
python3 scripts/eval/doc_refactor_daemon.py

# 7. Run Nightly Auto-Tuner Daemon
echo "🌙 [2/2] Running Multi-Skill Nightly Auto-Tuner..."
python3 scripts/eval/nightly_tuner_daemon.py --max-iter 30

echo "================================================================="
echo "[CCBA Nightly Daemon] Finished successfully at $(date)"
echo "================================================================="
```

---

## 3. Trạng Thái Vòng Đời & Ghế Trách Nhiệm Hiến Chương CCBA

- **Trạng thái:** `COMMITTED` (Đã người dùng phê chuẩn qua phỏng vấn dồn dập).
- **Ghế Phụ Trách Kỹ Thuật:** `KY_SU_THUC_THI` & `CHU_TRI_BO_MON`.
- **Ghế Phê Duyệt Kiến Trúc:** `TRUONG_PHONG_RD_HTQT`.
