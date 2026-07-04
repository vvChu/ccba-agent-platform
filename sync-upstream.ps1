<#
.SYNOPSIS
    Script đồng bộ tri thức từ các kho chứa thượng nguồn (ClaudeKit & MattPocock) cho ccba-agent-platform.
.DESCRIPTION
    Tự động kích hoạt môi trường ảo Python (.venv) nếu có và chạy check_claudekit_updates.py.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$SyncScript = Join-Path $ScriptDir "scripts\check_claudekit_updates.py"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "CCBA Agent Platform - Đồng bộ tri thức thượng nguồn" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

if (Test-Path $VenvPython) {
    Write-Host "[Info] Đang chạy script đồng bộ bằng Python từ môi trường ảo (.venv)..." -ForegroundColor Yellow
    & $VenvPython $SyncScript
} else {
    Write-Host "[Info] Không tìm thấy thư mục .venv. Đang chạy bằng Python hệ thống..." -ForegroundColor Yellow
    python $SyncScript
}

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Hoàn tất kiểm tra đồng bộ." -ForegroundColor Cyan
