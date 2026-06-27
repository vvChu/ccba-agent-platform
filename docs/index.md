# mdconvert Documentation

Modern Document to Markdown Converter with Vietnamese legal document support.

## Features

- 📄 **Multi-format support**: PDF, DOCX, HTML, images
- 🤖 **AI-powered conversion**: Gemini API, LlamaParse for scanned docs
- 🇻🇳 **Vietnamese legal docs**: Special handling for Điều, Chương, Khoản
- 🔧 **Post-processing**: Auto-fix formatting issues
- ✅ **Quality validation**: Automatic quality scoring
- 🧹 **Linting**: Custom VN Legal lint rules (VN001-VN004)

## Quick Start

```bash
# Install
pip install mdconvert-cli

# Convert a PDF
mdconvert convert document.pdf

# Lint Markdown files
mdconvert lint ./docs/ --fix

# Show configuration
mdconvert config
```

## Links

- [GitHub Repository](https://github.com/vvChu/mdconverter)
- [Installation Guide](getting-started/installation.md)
- [ClaudeKit Agent Tools Guide](getting-started/claudekit-tools.md)
- [CLI Reference](user-guide/cli.md)
