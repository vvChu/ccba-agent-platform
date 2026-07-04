# Installation

## Requirements

- Python 3.10 or higher
- Pandoc (for DOCX/HTML conversion)

## Step 1: Get the Code

```bash
git clone https://github.com/vvChu/mdconverter.git
cd mdconverter
```

## Step 2: Install

### Option A: Automatic (Windows Recommended)

Use the provided PowerShell script to automatically setup Python virtual environment and dependencies:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Option B: Install from PyPI

```bash
pip install mdconvert-cli
```

### Option C: Manual Install from Source

```bash
pip install -e ".[dev]"
```

## Verify Installation

```bash
mdconvert --version
# Output: mdconverter version 1.0.0
```

## Optional Dependencies

### LlamaParse (for scanned PDFs)

```bash
pip install mdconvert-cli[llm]
```

Set your API key:

```bash
export MDCONVERT_LLAMA_CLOUD_API_KEY=your_key_here
```

### Pandoc

Install Pandoc for DOCX/HTML conversion:

- **Windows**: `winget install pandoc`
- **macOS**: `brew install pandoc`
- **Linux**: `apt install pandoc`
