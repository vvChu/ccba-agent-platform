<#
.SYNOPSIS
Script test run cho Semantic PCCC Audit Engine

.DESCRIPTION
Script này trỏ tới thư mục dữ liệu mẫu trong `scratch` để demo cách chạy `audit_engine.py` với tham số CLI.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$EngineScript = Join-Path $ScriptDir "audit_engine.py"

# Tham chiếu thư mục dữ liệu mẫu (hoặc qua biến môi trường PCCC_DATA_DIR)
$WorkspacePath = if ($env:PCCC_DATA_DIR) { $env:PCCC_DATA_DIR } else { Join-Path $ScriptDir "sample_data" }
$OutputReport = if ($env:PCCC_OUTPUT_REPORT) { $env:PCCC_OUTPUT_REPORT } else { "PCCC_MapReduce_Report_CLI.md" }

$TmPath = Join-Path $WorkspacePath "0-TM TTPCCC.md"
$ArchPath = Join-Path $WorkspacePath "kien_truc.md"
$MepPath = Join-Path $WorkspacePath "mep.md"
$Pc07Path = Join-Path $WorkspacePath "GopY_PC07.md"

Write-Host "Bắt đầu chạy Semantic PCCC Audit..." -ForegroundColor Cyan

python $EngineScript `
    --tm "$TmPath" `
    --arch "$ArchPath" `
    --mep "$MepPath" `
    --gopy "$Pc07Path" `
    --out "$OutputReport"

Write-Host "Hoàn thành! Vui lòng kiểm tra báo cáo tại: $OutputReport" -ForegroundColor Green
