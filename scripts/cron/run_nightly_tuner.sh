#!/bin/bash
# run_nightly_tuner.sh - Cron execution wrapper for Server Spark (:8090)
# Schedule: 0 0 * * * (Every midnight at 00:00 AM)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================================================="
echo "[CCBA Nightly Auto-Tuner Daemon] Starting at $(date)"
echo "================================================================="

# Pull latest main branch before tuning
git checkout main
git pull origin main

# Activate python virtualenv if exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Run Nightly Auto-Tuner Daemon with 30 iterations for weak skills
python3 scripts/eval/nightly_tuner_daemon.py --max-iter 30

echo "================================================================="
echo "[CCBA Nightly Auto-Tuner Daemon] Finished at $(date)"
echo "================================================================="
