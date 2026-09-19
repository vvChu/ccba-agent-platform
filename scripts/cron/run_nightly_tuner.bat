@echo off
REM run_nightly_tuner.bat - Windows Task Scheduler wrapper for CCBA Nightly Auto-Tuner
REM Run at 00:00 daily

if "%~1"=="--help" goto show_help
if "%~1"=="-h" goto show_help
if "%~1"=="/?" goto show_help
goto run

:show_help
echo CCBA Nightly Auto-Tuner ^& Evolution Runner (Windows)
echo.
echo Su dung:
echo   run_nightly_tuner.bat [--dry-run]
echo.
echo Tuy chon:
echo   -h, --help, /?  Hien thi huong dan su dung
echo   --dry-run       Chay kiem thu an toan, khong commit/push hoac mo PR
exit /b 0

:run
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


REM Phase 1: Legal Ground Truth Parity & Master CI Telemetry
set "LEGAL_SPOKE_DIR="
if exist "%~dp0\..\..\..\ccba-legal-knowledge" set "LEGAL_SPOKE_DIR=%~dp0\..\..\..\ccba-legal-knowledge"
if not defined LEGAL_SPOKE_DIR if exist "D:\GitHubProjects\ccba-legal-knowledge" set "LEGAL_SPOKE_DIR=D:\GitHubProjects\ccba-legal-knowledge"

if defined LEGAL_SPOKE_DIR if exist "%LEGAL_SPOKE_DIR%\.md\tools\run_nightly_telemetry.py" (
    echo =================================================================
    echo [1/3] Running Legal Ground Truth Parity ^& Master CI Telemetry...
    echo =================================================================
    pushd "%LEGAL_SPOKE_DIR%"
    set "DRY_RUN_ARG="
    if /i "%~1"=="--dry-run" set "DRY_RUN_ARG=--dry-run"
    python .md\tools\run_nightly_telemetry.py --cohorts golden %DRY_RUN_ARG%
    if errorlevel 1 (
        echo [WARNING] Legal telemetry encountered regression errors.
        python -c "import sys; from pathlib import Path; sys.path.insert(0, r'%~dp0\..\..'); from scripts.eval.telegram_alert import send_telegram_alert; send_telegram_alert('🚨 *[CCBA CRON WARNING] Lỗi Hồi Quy Kiểm Chuẩn Pháp Lý Ban Đêm!*\n• *Spoke:* `ccba-legal-knowledge`\n• *Lỗi:* Telemetry Parity / Master CI thất bại\n• *Chi tiết:* Xem báo cáo `.md/reports/nightly_*.md`', parse_mode='Markdown', mock_fallback=True)" 2>nul
    )
    git status -s .md\reports 2>nul | findstr /i "nightly_" >nul
    if not errorlevel 1 (
        echo Committing and pushing nightly legal telemetry reports...
        git add .md\reports\nightly_*.md .md\reports\nightly_*.json 2>nul
        git commit --no-verify -m "chore(telemetry): record automated nightly legal verification report [skip ci]"
        git push origin main
    )
    popd
)

cd /d "%~dp0\..\.."
echo [2/3] Running Document Auto-Evolution Engine...
python scripts\eval\doc_refactor_daemon.py %DRY_RUN_ARG%

echo [3/3] Running Multi-Skill Nightly Auto-Tuner...
python scripts\eval\nightly_tuner_daemon.py --max-iter 30 %DRY_RUN_ARG%

echo =================================================================
echo [CCBA Nightly Daemon] Completed at %DATE% %TIME%
echo =================================================================
