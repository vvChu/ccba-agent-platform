#!/bin/bash
# run_boost_worktree.sh - Isolated Ephemeral Worktree Deep Reasoning Runner for Stuck Skills (ADR-0052)
# Triggered via Telegram /boost <skill> or CLI

set -euo pipefail

# 1. Ensure Full PATH and UTF-8 Locale
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:/snap/bin:${PATH:-}"
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"
export PYTHONIOENCODING="utf-8"
export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ $# -lt 1 ] || [ -z "$1" ]; then
    echo "❌ [LỖI] Thiếu tham số tên kỹ năng! Sử dụng: $0 <skill_name>" >&2
    exit 1
fi

SKILL="$1"

# 2. Process Mutex / Concurrency Lock (ADR-0043 / REC-04)
# Prevent conflict with Nightly Cron or another concurrent runner
LOCK_FILE="/tmp/ccba_nightly_runner.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "⚠️ [LOCK BUSY] Một tiến trình Nightly Tuner hoặc Boost khác đang chạy. Dừng thực thi an toàn."
    exit 1
fi

# 3. Auto-load .env secrets if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# 4. Worktree Lifecycle & Auto-Cleanup Hook
WORKTREE_DIR="$PROJECT_ROOT/.worktrees/boost-${SKILL}-$$-$(date +%s)"

cleanup_worktree() {
    echo "🧹 Đang thu hồi tài nguyên Ephemeral Worktree ($WORKTREE_DIR)..."
    cd "$PROJECT_ROOT"
    if [ -d "$WORKTREE_DIR" ]; then
        # Copy newly generated reports and plateau briefs back to main project root
        if [ -d "$WORKTREE_DIR/.md/knowledge/reports" ]; then
            mkdir -p "$PROJECT_ROOT/.md/knowledge/reports"
            find "$WORKTREE_DIR/.md/knowledge/reports" -maxdepth 1 -name "nightly_tuner_report_*.md" -exec cp -f {} "$PROJECT_ROOT/.md/knowledge/reports/" \; 2>/dev/null || true
        fi
        if [ -d "$WORKTREE_DIR/.md/knowledge/escalations" ]; then
            mkdir -p "$PROJECT_ROOT/.md/knowledge/escalations"
            find "$WORKTREE_DIR/.md/knowledge/escalations" -maxdepth 1 -name "*_plateau.md" -exec cp -f {} "$PROJECT_ROOT/.md/knowledge/escalations/" \; 2>/dev/null || true
        fi
        git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
    fi
    git worktree prune 2>/dev/null || true
    echo "✅ Đã dọn dẹp hoàn tất."
}
trap cleanup_worktree EXIT

echo "================================================================="
echo "[CCBA Skill Boost Runner] Starting boost for skill '$SKILL' at $(date)"
echo "================================================================="

# 5. Setup Isolated Ephemeral Worktree from origin/main
cd "$PROJECT_ROOT"
mkdir -p "$PROJECT_ROOT/.worktrees"

echo "🔄 Fetching latest origin/main..."
git fetch origin main || echo "⚠️ Cảnh báo: git fetch origin main không thành công, tiếp tục với local origin/main..."

TARGET_REF="origin/main"
if ! git rev-parse --verify "$TARGET_REF" >/dev/null 2>&1; then
    TARGET_REF="main"
fi

echo "🌿 Khởi tạo Ephemeral Worktree từ $TARGET_REF: $WORKTREE_DIR"
git worktree add --detach "$WORKTREE_DIR" "$TARGET_REF"

# Replicate .env if exists (preventing Blind Worktree)
if [ -f "$PROJECT_ROOT/.env" ] && [ ! -f "$WORKTREE_DIR/.env" ]; then
    cp -n "$PROJECT_ROOT/.env" "$WORKTREE_DIR/.env" 2>/dev/null || true
fi

# Replicate historical reports and plateau briefs to ephemeral worktree
if [ -d "$PROJECT_ROOT/.md/knowledge/reports" ]; then
    mkdir -p "$WORKTREE_DIR/.md/knowledge/reports"
    find "$PROJECT_ROOT/.md/knowledge/reports" -maxdepth 1 -name "nightly_tuner_report_*.md" -exec cp -f {} "$WORKTREE_DIR/.md/knowledge/reports/" \; 2>/dev/null || true
fi
if [ -d "$PROJECT_ROOT/.md/knowledge/escalations" ]; then
    mkdir -p "$WORKTREE_DIR/.md/knowledge/escalations"
    find "$PROJECT_ROOT/.md/knowledge/escalations" -maxdepth 1 -name "*_plateau.md" -exec cp -f {} "$WORKTREE_DIR/.md/knowledge/escalations/" \; 2>/dev/null || true
fi

# Activate python virtualenv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Switch into isolated worktree context
cd "$WORKTREE_DIR"

# Ensure full PYTHONPATH across packages and isolated worktree root
export PYTHONPATH="$WORKTREE_DIR/packages/ccba-harness/src:$WORKTREE_DIR/packages/ccba-ai/src:$WORKTREE_DIR:${PYTHONPATH:-}"

echo "🚀 [Boost] Running Nightly Auto-Tuner Daemon for $SKILL with Deep Reasoning (gemini-3.8-flash-high)..."
python3 scripts/eval/nightly_tuner_daemon.py \
    --skill "$SKILL" \
    --use-real-llm \
    --model "gemini-3.8-flash-high" \
    --max-iter 2 \
    --token-budget 500000 \
    --per-skill-mutation-budget 250000 \
    --ref "$TARGET_REF" \
    ${@:2}

echo "================================================================="
echo "[CCBA Skill Boost Runner] Boost finished successfully at $(date)"
echo "================================================================="
