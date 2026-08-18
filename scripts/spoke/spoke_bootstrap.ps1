<#
.SYNOPSIS
    CCBA Spoke Hub Package Bootstrapper (ADR 0044)
.DESCRIPTION
    Tự động hóa kết nối Spoke Python với Hub Packages qua chế độ editable install (pip install -e),
    thay thế hoàn toàn anti-pattern sys.path.insert.
.PARAMETER Spoke
    Đường dẫn thư mục Spoke (mặc định: thư mục hiện hành '.')
.PARAMETER Hub
    Đường dẫn Platform Hub (mặc định: auto-discover)
.PARAMETER CreateVenv
    Tự động tạo .venv nếu chưa tồn tại
.PARAMETER DryRun
    Chạy mô phỏng không ghi tệp
.PARAMETER CheckOnly
    Chỉ kiểm tra hiện trạng không cài đặt
.PARAMETER Force
    Bỏ qua cảnh báo Branch Guard khi Hub đang trên branch khác main
#>

param (
    [string]$Spoke = ".",
    [string]$Hub = "",
    [switch]$CreateVenv,
    [switch]$DryRun,
    [switch]$CheckOnly,
    [switch]$Force
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hubDir = if ($Hub) { $Hub } else { (Split-Path -Parent (Split-Path -Parent $scriptDir)) }
$engineScript = Join-Path $scriptDir "spoke_bootstrap.py"

$pythonCmd = "python"
if (Get-Command "py" -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
}

$argsList = @($engineScript, "--spoke", $Spoke)

if ($Hub) {
    $argsList += @("--hub", $Hub)
}
if ($CreateVenv) {
    $argsList += "--create-venv"
}
if ($DryRun) {
    $argsList += "--dry-run"
}
if ($CheckOnly) {
    $argsList += "--check-only"
}
if ($Force) {
    $argsList += "--force"
}

# Use call operator instead of Invoke-Expression to prevent argument injection
& $pythonCmd @argsList
exit $LASTEXITCODE
