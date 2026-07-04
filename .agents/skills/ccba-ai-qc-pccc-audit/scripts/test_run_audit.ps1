<#
.SYNOPSIS
Script test run cho Semantic PCCC Audit Engine

.DESCRIPTION
Script này trỏ tới thư mục dữ liệu mẫu trong `scratch` để demo cách chạy `audit_engine.py` với tham số CLI.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$EngineScript = Join-Path $ScriptDir "audit_engine.py"

# Thay thế biến $WorkspacePath thành đường dẫn thực tế của workspace nếu chạy ở nơi khác.
$WorkspacePath = "C:\Users\chuvu\.gemini\antigravity\brain\8eacf34e-8e53-4d27-a860-de8ea455c177\scratch\pccc_audit_data"
$OutputReport = "C:\Users\chuvu\.gemini\antigravity\brain\8eacf34e-8e53-4d27-a860-de8ea455c177\scratch\PCCC_MapReduce_Report_CLI.md"

$TmPath = Join-Path $WorkspacePath "0-TM TTPCCC - TẦNG 4 KHOI B - BV NTP-DC 20.11.md"
$ArchPath = Join-Path $WorkspacePath "2- 241118_TANG 4 BV NTP_KIEN TRUC PCCC.md"
$MepPath = Join-Path $WorkspacePath "3- 241119 - BV NTP - PCCC MEP final.md"
$Pc07Path = Join-Path $WorkspacePath "GopY_PC07.md"

Write-Host "Bắt đầu chạy Semantic PCCC Audit..." -ForegroundColor Cyan

python $EngineScript `
    --tm "$TmPath" `
    --arch "$ArchPath" `
    --mep "$MepPath" `
    --gopy "$Pc07Path" `
    --model "qwen-local-primary" `
    --out "$OutputReport"

Write-Host "Hoàn thành! Vui lòng kiểm tra báo cáo tại: $OutputReport" -ForegroundColor Green
