#!/bin/bash
# run_nightly_tuner.sh - Isolated Ephemeral Worktree Runner for Server Spark (:8090)
# Schedule: 0 0 * * * (Every midnight at 00:00 AM)

set -euo pipefail

# 1. Ensure Full PATH and UTF-8 Locale for Linux Cron execution
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:/snap/bin:${PATH:-}"
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"
export PYTHONIOENCODING="utf-8"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 2. Parse optional command line flags
DRY_RUN_FLAG=""
MAX_ITER="30"
TARGET_REF="${TARGET_REF:-origin/main}"
USE_REAL_LLM_FLAG=""
TOKEN_BUDGET_FLAG=""
MODEL_FLAG=""
SKILL_FLAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            cat << 'EOF'
CCBA Nightly Auto-Tuner & Evolution Runner (Server Spark :8090)

Sử dụng:
  run_nightly_tuner.sh [TÙY CHỌN]

Tùy chọn:
  -h, --help           Hiển thị hướng dẫn sử dụng và thoát
  --dry-run            Chạy kiểm thử an toàn, không commit/push git hoặc mở Pull Request
  --max-iter N         Số vòng lặp tối đa cho mỗi kỹ năng (mặc định: 30)
  --ref TARGET_REF     Git target ref để so khớp baseline (mặc định: origin/main)
  --use-real-llm       Kích hoạt chạy với mô hình LLM thực tế qua AI Gateway LiteLLM
  --token-budget N     Giới hạn trần ngân sách token hàng đêm (mặc định: 5,000,000)
  --model MODEL_NAME   Tên mô hình LLM (mặc định: qwen-local-primary)
  --skill SKILL_NAME   Chỉ định tối ưu một kỹ năng cụ thể (bỏ qua queue toàn bộ catalog)

Ví dụ:
  ./scripts/cron/run_nightly_tuner.sh --dry-run
  ./scripts/cron/run_nightly_tuner.sh --use-real-llm --model qwen-local-primary --skill ccba-legal-ingest
EOF
            exit 0
            ;;
        --dry-run)
            DRY_RUN_FLAG="--dry-run"
            shift
            ;;
        --max-iter)
            MAX_ITER="$2"
            shift 2
            ;;
        --ref)
            TARGET_REF="$2"
            shift 2
            ;;
        --use-real-llm)
            USE_REAL_LLM_FLAG="--use-real-llm"
            shift
            ;;
        --token-budget)
            TOKEN_BUDGET_FLAG="--token-budget $2"
            shift 2
            ;;
        --model)
            MODEL_FLAG="--model $2"
            shift 2
            ;;
        --skill|--skills)
            SKILL_FLAG="--skill $2"
            shift 2
            ;;
        *)
            echo "⚠️ [CẢNH BÁO] Bỏ qua cờ không xác định: $1"
            shift
            ;;
    esac
done

# 2.1. Process Mutex / Concurrency Lock (ADR-0043 / REC-04)
LOCK_FILE="/tmp/ccba_nightly_runner.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "⚠️ [LOCK BUSY] Một tiến trình Nightly Tuner khác đang chạy. Dừng thực thi an toàn."
    exit 0
fi

# 3. Auto-load .env secrets if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# 4. Emergency Error Trap (Python Telegram Alert)
on_error() {
    local exit_code=$?
    local failed_line=$1
    local failed_cmd=$2
    local now_str
    now_str="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "🚨 [FATAL ERROR] Nightly Tuner thất bại tại dòng $failed_line (cmd: '$failed_cmd', exit: $exit_code)" >&2
    python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from scripts.eval.telegram_alert import send_telegram_alert
    time_str, line_num, cmd_str, code_str = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    send_telegram_alert(
        message='🚨 *[CCBA CRON FAILURE] Nightly Daemon Thất Bại!*\\n'
                f'• *Thời gian:* {time_str}\\n'
                f'• *Dòng lỗi:* \`line {line_num}\`\\n'
                f'• *Lệnh lỗi:* \`{cmd_str}\`\\n'
                f'• *Exit Code:* \`{code_str}\`\\n'
                '• *Chi tiết:* Xem log \`.md/logs/nightly_cron.log\`',
        parse_mode='Markdown',
        mock_fallback=True
    )
except Exception as e:
    print(f'Lỗi khi gửi telegram alert: {e}', file=sys.stderr)
" "$now_str" "$failed_line" "$failed_cmd" "$exit_code" 2>/dev/null || true
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

# 5. Worktree Lifecycle & Auto-Cleanup Hook
WORKTREE_DIR="$PROJECT_ROOT/.worktrees/nightly-runner"

cleanup_worktree() {
    echo "🧹 Đang thu hồi tài nguyên Ephemeral Worktree..."
    cd "$PROJECT_ROOT"
    if [ -d "$WORKTREE_DIR" ]; then
        # Copy newly generated reports back to main project root if any
        if [ -d "$WORKTREE_DIR/.md/knowledge/reports" ]; then
            mkdir -p "$PROJECT_ROOT/.md/knowledge/reports"
            cp -n "$WORKTREE_DIR/.md/knowledge/reports"/nightly_tuner_report_*.md "$PROJECT_ROOT/.md/knowledge/reports/" 2>/dev/null || true
        fi
        git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
    fi
    git worktree prune 2>/dev/null || true
    echo "✅ Đã dọn dẹp hoàn tất."
}
trap cleanup_worktree EXIT

echo "================================================================="
echo "[CCBA Nightly Auto-Tuner Daemon] Starting at $(date)"
echo "================================================================="

# 6. Tri-Repo Sequential Pull Gate (ADR 0042)
BASE_DIR="$(cd "$PROJECT_ROOT/.." && pwd)"
LEGAL_SPOKE_DIR=""
if [ -d "$BASE_DIR/ccba-legal-knowledge" ]; then
    LEGAL_SPOKE_DIR="$BASE_DIR/ccba-legal-knowledge"
elif [ -d "$HOME/ccba/ccba-legal-knowledge" ]; then
    LEGAL_SPOKE_DIR="$HOME/ccba/ccba-legal-knowledge"
elif [ -d "/home/ccba/ccba/ccba-legal-knowledge" ]; then
    LEGAL_SPOKE_DIR="/home/ccba/ccba/ccba-legal-knowledge"
fi

if [ -n "$LEGAL_SPOKE_DIR" ]; then
    echo "🔄 Updating ccba-legal-knowledge ($LEGAL_SPOKE_DIR)..."
    (cd "$LEGAL_SPOKE_DIR" && git fetch origin main && git checkout -q main && git pull -q origin main) || echo "⚠️ Warning: Failed to pull ccba-legal-knowledge"
fi

if [ -d "$BASE_DIR/IDOP-CCBA-WAY" ]; then
    echo "🔄 Updating IDOP-CCBA-WAY..."
    (cd "$BASE_DIR/IDOP-CCBA-WAY" && git fetch origin main && git checkout -q main && git pull -q origin main) || echo "⚠️ Warning: Failed to pull IDOP-CCBA-WAY"
fi

# 7. Setup Isolated Ephemeral Worktree from origin/main
cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/.worktrees"

# Pre-clean stale worktree if interrupted previously
if [ -d "$WORKTREE_DIR" ]; then
    git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
fi
git worktree prune 2>/dev/null || true

# Fetch latest main if target ref is origin/main
if [ "$TARGET_REF" = "origin/main" ]; then
    echo "🔄 Fetching latest origin/main..."
    git fetch origin main
fi

# Create detached ephemeral worktree from TARGET_REF
echo "🌿 Khởi tạo Ephemeral Worktree từ $TARGET_REF: $WORKTREE_DIR"
git worktree add --detach "$WORKTREE_DIR" "$TARGET_REF"

# Replicate .env if exists
if [ -f "$PROJECT_ROOT/.env" ] && [ ! -f "$WORKTREE_DIR/.env" ]; then
    cp -n "$PROJECT_ROOT/.env" "$WORKTREE_DIR/.env" 2>/dev/null || true
fi

# Activate python virtualenv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Switch into isolated worktree context
cd "$WORKTREE_DIR"

# Ensure full PYTHONPATH across packages and isolated worktree root
export PYTHONPATH="$WORKTREE_DIR/packages/ccba-harness/src:$WORKTREE_DIR/packages/ccba-ai/src:$WORKTREE_DIR:${PYTHONPATH:-}"

# 7.4. Phase 1: Legal Ground Truth Parity & Master CI Telemetry
echo "⚖️ [1/3] Running Legal Ground Truth Parity & Master CI Telemetry..."
if [ -n "$LEGAL_SPOKE_DIR" ] && [ -f "$LEGAL_SPOKE_DIR/.md/tools/run_nightly_telemetry.py" ]; then
    echo "🔍 Executing Nightly Telemetry Runner in $LEGAL_SPOKE_DIR..."
    TELEMETRY_EXIT=0
    (
        cd "$LEGAL_SPOKE_DIR"
        if [ -n "$DRY_RUN_FLAG" ]; then
            echo "   [DRY-RUN] Executing: python3 .md/tools/run_nightly_telemetry.py --cohorts all --dry-run"
            python3 .md/tools/run_nightly_telemetry.py --cohorts all --dry-run
        else
            python3 .md/tools/run_nightly_telemetry.py --cohorts all || TELEMETRY_EXIT=$?
            if [ $TELEMETRY_EXIT -ne 0 ]; then
                echo "🚨 [TELEMETRY REGRESSION] Legal Parity / Master CI phát hiện lỗi hồi quy (Exit: $TELEMETRY_EXIT)!" >&2
                python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from scripts.eval.telegram_alert import send_telegram_alert
    code_str = sys.argv[1]
    send_telegram_alert(
        message='🚨 *[CCBA CRON WARNING] Lỗi Hồi Quy Kiểm Chuẩn Pháp Lý Ban Đêm!*\\n'
                '• *Spoke:* \`ccba-legal-knowledge\`\\n'
                f'• *Lỗi:* Telemetry Parity / Master CI thất bại (exit code: \`{code_str}\`)\\n'
                '• *Chi tiết:* Xem báo cáo \`.md/reports/nightly_*.md\`',
        parse_mode='Markdown',
        mock_fallback=True
    )
except Exception as e:
    print(f'Lỗi khi gửi telegram alert: {e}', file=sys.stderr)
" "$TELEMETRY_EXIT" 2>/dev/null || true
            fi
            # Auto-commit and push nightly reports if generated
            if git status --porcelain .md/reports/ 2>/dev/null | grep -q "nightly_"; then
                echo "📝 Committing and pushing nightly legal telemetry reports..."
                git add .md/reports/nightly_*.md .md/reports/nightly_*.json 2>/dev/null || true
                git -c user.name="CCBA Nightly Daemon" -c user.email="daemon@ccba-ai.local" commit --no-verify -m "chore(telemetry): record automated nightly legal verification report [skip ci]" || true
                git push origin main || echo "⚠️ Warning: Failed to push nightly reports to origin/main"
            fi
        fi
    )
else
    echo "⚠️ Warning: ccba-legal-knowledge not found or run_nightly_telemetry.py missing. Skipping Phase 1."
fi

# 8. Run Document Auto-Evolution Engine (Audit -> AST Grounding -> Zero-Deletion -> PR)
echo "📚 [2/3] Running Document Auto-Evolution Engine..."
python3 scripts/eval/doc_refactor_daemon.py ${DRY_RUN_FLAG}

# 8.1. Ensure clean detached HEAD from TARGET_REF before running Tuner
echo "🔄 Đồng bộ trạng thái worktree về HEAD sạch từ $TARGET_REF..."
git checkout --detach "$TARGET_REF"

# 9. Run Multi-Skill Nightly Auto-Tuner Daemon with specified iterations
echo "🌙 [3/3] Running Multi-Skill Nightly Auto-Tuner (max-iter: $MAX_ITER)..."
python3 scripts/eval/nightly_tuner_daemon.py --max-iter "$MAX_ITER" ${DRY_RUN_FLAG} ${USE_REAL_LLM_FLAG} ${TOKEN_BUDGET_FLAG} ${MODEL_FLAG} ${SKILL_FLAG}

echo "================================================================="
echo "[CCBA Nightly Daemon] Finished successfully at $(date)"
echo "================================================================="
