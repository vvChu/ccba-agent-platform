@echo off
REM run_nightly_tuner.bat - Windows Task Scheduler wrapper for CCBA Nightly Auto-Tuner
REM Run at 00:00 daily

cd /d "%~dp0\..\.."

echo =================================================================
echo [CCBA Nightly Auto-Tuner Daemon] Starting at %DATE% %TIME%
echo =================================================================

git checkout main
git pull origin main

python scripts\eval\nightly_tuner_daemon.py --max-iter 30

echo =================================================================
echo [CCBA Nightly Auto-Tuner Daemon] Completed at %DATE% %TIME%
echo =================================================================
