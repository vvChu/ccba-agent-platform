#!/bin/bash
# run_nightly_tuner.sh - Cron execution wrapper for Server Spark (:8090)
# Schedule: 0 0 * * * (Every midnight at 00:00 AM)

set -euo pipefail

# 1. Ensure Full PATH and UTF-8 Locale for Linux Cron execution
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:/snap/bin:${PATH:-}"
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"
export PYTHONIOENCODING="utf-8"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 2. Auto-load .env secrets if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

cd "$PROJECT_ROOT"


echo "================================================================="
echo "[CCBA Nightly Auto-Tuner Daemon] Starting at $(date)"
echo "================================================================="

# Tri-Repo Sequential Pull Gate (ADR 0042)
BASE_DIR="$(cd "$PROJECT_ROOT/.." && pwd)"

if [ -d "$BASE_DIR/ccba-legal-knowledge" ]; then
    echo "🔄 Updating ccba-legal-knowledge..."
    cd "$BASE_DIR/ccba-legal-knowledge" && git checkout main && git pull origin main || echo "⚠️ Warning: Failed to pull ccba-legal-knowledge"
fi

if [ -d "$BASE_DIR/IDOP-CCBA-WAY" ]; then
    echo "🔄 Updating IDOP-CCBA-WAY..."
    cd "$BASE_DIR/IDOP-CCBA-WAY" && git checkout main && git pull origin main || echo "⚠️ Warning: Failed to pull IDOP-CCBA-WAY"
fi

# Pull latest main branch of Hub before tuning
cd "$PROJECT_ROOT"
git checkout main
git pull origin main

# Activate python virtualenv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi


# 1. Run Document Auto-Evolution Engine (Audit -> AST Grounding -> Zero-Deletion -> PR)
echo "📚 [1/2] Running Document Auto-Evolution Engine..."
python3 scripts/eval/doc_refactor_daemon.py

# 2. Run Nightly Auto-Tuner Daemon with 30 iterations for weak skills
echo "🌙 [2/2] Running Multi-Skill Nightly Auto-Tuner..."
python3 scripts/eval/nightly_tuner_daemon.py --max-iter 30

echo "================================================================="
echo "[CCBA Nightly Daemon] Finished at $(date)"
echo "================================================================="
