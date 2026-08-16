@echo off
REM run_nightly_tuner.bat - Windows Task Scheduler wrapper for CCBA Nightly Auto-Tuner
REM Run at 00:00 daily

cd /d "%~dp0\..\.."

echo =================================================================
echo [CCBA Nightly Auto-Tuner Daemon] Starting at %DATE% %TIME%
echo =================================================================

REM Tri-Repo Sequential Pull Gate (ADR 0042)
if exist "%~dp0\..\..\..\ccba-legal-knowledge" (
    echo Updating ccba-legal-knowledge...
    cd /d "%~dp0\..\..\..\ccba-legal-knowledge"
    git checkout main && git pull origin main
)

if exist "%~dp0\..\..\..\IDOP-CCBA-WAY" (
    echo Updating IDOP-CCBA-WAY...
    cd /d "%~dp0\..\..\..\IDOP-CCBA-WAY"
    git checkout main && git pull origin main
)

cd /d "%~dp0\..\.."
git checkout main
git pull origin main


echo [1/2] Running Document Auto-Evolution Engine...
python scripts\eval\doc_refactor_daemon.py

echo [2/2] Running Multi-Skill Nightly Auto-Tuner...
python scripts\eval\nightly_tuner_daemon.py --max-iter 30

echo =================================================================
echo [CCBA Nightly Daemon] Completed at %DATE% %TIME%
echo =================================================================
