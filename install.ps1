# MarkDownConvertor Automated Installer (Windows)

$PythonMinVersion = "3.10"

Write-Host "--- 🚀 MarkDownConvertor Installer ---" -ForegroundColor Cyan

# 1. Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found! Please install Python $PythonMinVersion+ from python.org"
    exit
}

$PythonVersion = python --version 2>&1
Write-Host "Found $PythonVersion"

# 2. Check for UV (Recommended)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Detected 'uv' - Using fast installation method..." -ForegroundColor Green
    uv venv --allow-existing
    & .\.venv\Scripts\Activate.ps1
    uv pip install -e ".[dev,llm]"
}
else {
    Write-Host "'uv' not found. Falling back to standard pip..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev,llm]"
}

# 3. Interactive Configuration
Write-Host "`n⚙️  Configuration Setup" -ForegroundColor Cyan

if (Test-Path .env) {
    Write-Host ".env file already exists. Skipping configuration." -ForegroundColor Yellow
}
else {
    $ProxyUrl = Read-Host "Enter Antigravity Proxy URL [Default: http://127.0.0.1:8045]"
    if ([string]::IsNullOrWhiteSpace($ProxyUrl)) { $ProxyUrl = "http://127.0.0.1:8045" }

    $ProxyToken = Read-Host "Enter Antigravity Proxy Access Token (Leave empty if Auth disabled)"
    $LlamaKey = Read-Host "Enter LlamaCloud API Key (Optional, for scanned PDFs)"

    $EnvContent = @"
# MarkDownConvertor Configuration
MDCONVERT_ANTIGRAVITY_PROXY=$ProxyUrl
MDCONVERT_ANTIGRAVITY_ACCESS_TOKEN=$ProxyToken
MDCONVERT_GEMINI_API_KEY=
MDCONVERT_LLAMA_CLOUD_API_KEY=$LlamaKey
"@
    
    $EnvContent | Out-File -FilePath .env -Encoding utf8
    Write-Host "Created .env with your settings!" -ForegroundColor Green
}

Write-Host "`n✅ Installation Complete!" -ForegroundColor Green
Write-Host "To start, run: .\.venv\Scripts\Activate.ps1"
Write-Host "Then try: mdconvert --help"
