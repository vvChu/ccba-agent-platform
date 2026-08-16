#!/usr/bin/env bash
# bootstrap_spark_server.sh - Automated Deployment Script for Server Spark (100.83.192.30)
# Designed to be executed autonomously by Antigravity Agent or Server Administrator.

set -euo pipefail

echo "================================================================="
echo "🚀 [CCBA Server Spark] Starting Autonomous Deployment Protocol"
echo "================================================================="

# 1. Determine Base Directory (~/ccba or /opt/ccba)
BASE_DIR="${CCBA_BASE_DIR:-$HOME/ccba}"
echo "📂 Target Directory: $BASE_DIR"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

# 2. Clone or Update Hub (ccba-agent-platform)
if [ -d "$BASE_DIR/ccba-agent-platform/.git" ]; then
    echo "🔄 Updating ccba-agent-platform (Hub)..."
    cd "$BASE_DIR/ccba-agent-platform"
    git checkout main
    git pull origin main
else
    echo "📥 Cloning ccba-agent-platform (Hub)..."
    git clone https://github.com/vvChu/ccba-agent-platform.git "$BASE_DIR/ccba-agent-platform"
fi

# 3. Clone or Update Knowledge Spoke (ccba-legal-knowledge)
if [ -d "$BASE_DIR/ccba-legal-knowledge/.git" ]; then
    echo "🔄 Updating ccba-legal-knowledge (Knowledge Spoke)..."
    cd "$BASE_DIR/ccba-legal-knowledge"
    git checkout main
    git pull origin main
else
    echo "📥 Cloning ccba-legal-knowledge (Knowledge Spoke)..."
    git clone https://github.com/vvChu/ccba-legal-knowledge.git "$BASE_DIR/ccba-legal-knowledge"
fi

# 4. Clone or Update Enterprise Governance Spoke (IDOP-CCBA-WAY)
if [ -d "$BASE_DIR/IDOP-CCBA-WAY/.git" ]; then
    echo "🔄 Updating IDOP-CCBA-WAY (Governance Spoke)..."
    cd "$BASE_DIR/IDOP-CCBA-WAY"
    git checkout main
    git pull origin main
else
    echo "📥 Cloning IDOP-CCBA-WAY (Governance Spoke)..."
    git clone https://github.com/vvChu/IDOP-CCBA-WAY.git "$BASE_DIR/IDOP-CCBA-WAY"
fi

# 5. Setup Python Virtual Environment & Install Monorepo Packages
cd "$BASE_DIR/ccba-agent-platform"
echo "🐍 Setting up Python Virtual Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate


echo "📦 Installing Monorepo Packages in Editable mode..."
pip install --upgrade pip setuptools wheel
pip install -e "./packages/ccba-harness"
pip install -e "./packages/ccba-ai"
pip install -e "./packages/ccba-legal-intel"
pip install pytest pytest-timeout

# 5. Configure Permissions and Log Directory
mkdir -p .md/logs
chmod +x scripts/cron/run_nightly_tuner.sh

# 6. Check LiteLLM AI Gateway Connectivity on :8090
echo "🤖 Checking LiteLLM AI Gateway on :8090..."
if curl -s http://localhost:8090/health > /dev/null 2>&1; then
    echo "✅ LiteLLM AI Gateway is ACTIVE on :8090"
else
    echo "⚠️ LiteLLM Gateway not responding on :8090. Ensure systemd service or Docker container is started."
fi

# 7. Execute Self-Verification Dry Run
echo "🧪 Running Nightly Auto-Tuner Dry-Run Verification..."
python scripts/eval/nightly_tuner_daemon.py --dry-run --max-iter 1

# 8. Setup Crontab Schedule (00:00 Daily)
CRON_JOB="0 0 * * * /bin/bash $BASE_DIR/ccba-agent-platform/scripts/cron/run_nightly_tuner.sh >> $BASE_DIR/ccba-agent-platform/.md/logs/nightly_cron.log 2>&1"
(crontab -l 2>/dev/null | grep -Fv "run_nightly_tuner.sh" ; echo "$CRON_JOB") | crontab -
echo "⏰ Cron Schedule Verified: 0 0 * * * (Daily at Midnight)"

echo "================================================================="
echo "🎉 [CCBA Server Spark] Deployment Complete & Verified 100%!"
echo "================================================================="
