# mdconverter

Modern Document to Markdown Converter with Vietnamese legal document support.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Features

- 📄 **Multi-format support**: PDF, DOCX, HTML, images
- 🤖 **AI-powered conversion**: Gemini API with fallback chain
- 🇻🇳 **Vietnamese legal docs**: Special handling for Điều, Chương, Khoản
- 🔧 **Post-processing**: Auto-fix formatting issues
- ✅ **Quality validation**: Automatic quality scoring
- 🧹 **Linting**: Custom VN Legal lint rules (VN001-VN004)

## Quick Start (Automatic)

Nếu bạn dùng **Windows**, hãy chạy lệnh sau để tự động cài đặt mọi thứ (venv, dependencies) chỉ trong 1 giây:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Installation (Manual)

Chúng tôi khuyến khích sử dụng [**uv**](https://github.com/astral-sh/uv) để cài đặt cực nhanh:

```bash
# Cài đặt với uv (Khuyên dùng)
uv pip install -e ".[dev,llm]"

# Hoặc dùng pip truyền thống
pip install -e ".[dev,llm]"
```

## Quick Start

```bash
# Convert a single file
mdconvert convert document.pdf

# Convert a directory
mdconvert convert ./documents/ --recursive

# Validate Markdown files
mdconvert validate ./output/

# Lint with auto-fix
mdconvert lint ./output/ --fix

# Show configuration
mdconvert config
```

## Configuration

Create a `.env` file:

```bash
MDCONVERT_ANTIGRAVITY_PROXY=http://127.0.0.1:8045
MDCONVERT_LLAMA_CLOUD_API_KEY=your_key_here
MDCONVERT_MAX_OUTPUT_TOKENS=65536
```

## Project Structure

```txt
MarkDownConvertor/
├── src/
│   └── mdconverter/
│       ├── cli.py           # Typer CLI
│       ├── config.py        # Pydantic Settings
│       ├── core/            # Generic converters
│       │   ├── base.py      # Base classes
│       │   ├── gemini.py    # Gemini API
│       │   └── pandoc.py    # Pandoc
│       └── plugins/
│           └── vn_legal/    # Vietnamese Legal Docs
│               ├── detector.py
│               ├── processor.py
│               └── linter.py
├── tests/
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/

# Pre-commit hooks
pre-commit install
```

## Vietnamese Legal Document Rules

| Rule  | Description                                |
| ----- | ------------------------------------------ |
| VN001 | Merged list items (a, b, c on same line)   |
| VN002 | Suspicious numbering reset                 |
| VN003 | Missing blank line before Điều headers     |
| VN004 | Incorrect Điểm format                      |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Developed by IBST BIM Team for Vietnamese construction industry documentation.
