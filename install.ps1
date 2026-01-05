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
    uv venv
    & .\.venv\Scripts\Activate.ps1
    uv pip install -e ".[dev,llm]"
} else {
    Write-Host "'uv' not found. Falling back to standard pip..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev,llm]"
}

# 3. Create .env template if not exists
if (!(Test-Path .env)) {
    Write-Host "Creating .env template..."
    "# MarkDownConvertor Configuration`nMDCONVERT_ANTIGRAVITY_PROXY=http://127.0.0.1:8045`nMDCONVERT_GEMINI_API_KEY=`nMDCONVERT_LLAMA_CLOUD_API_KEY=" | Out-File -FilePath .env
    Write-Host "Done! Please edit .env to add your API keys." -ForegroundColor Yellow
}

Write-Host "`n✅ Installation Complete!" -ForegroundColor Green
Write-Host "To start, run: .\.venv\Scripts\Activate.ps1"
Write-Host "Then try: mdconvert --help"
