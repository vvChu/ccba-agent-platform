# CCBA Agent Services Platform

> Central Hub for AI Agent skills, workflows, knowledge, and internal tools.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Architecture

**Hub-and-Spoke** — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

```
ccba-agent-platform/                    ← Hub (Git-backed)
├── .agent/
│   ├── skills/                        ← AI Agent skills (6 skills)
│   │   ├── legal-document-tracker/    ←   Theo dõi VBPL
│   │   ├── completion-checklist/      ←   HSHT công trình
│   │   ├── seminar-builder/           ←   Chuẩn bị seminar
│   │   ├── long-form-writer/          ←   Viết tài liệu dài
│   │   ├── ai-gateway-sdk/           ←   Kết nối AI Gateway (22 models)
│   │   └── platform-loader/          ←   Bootstrap + routing
│   └── workflows/                     ← Automated workflows (7 workflows)
├── rules/                             ← CCBA organizational rules
├── knowledge/                         ← Accumulated knowledge
├── packages/                          ← Internal service modules
│   ├── ccba-ai/                       ←   AI Gateway client
│   └── mdconverter/                   ←   Document-to-Markdown converter
└── pyproject.toml                     ← Workspace config
```

## Services

### ccba-ai — AI Gateway Client

Kết nối AI Gateway trên Server Spark — 22 models, 1 endpoint.

```bash
pip install -e "packages/ccba-ai"
```

```python
from ccba_ai import ai
reply = ai.chat("Xin chào!")
```

### mdconverter — Document Converter

Modern Document to Markdown Converter with Vietnamese legal document support.

```bash
pip install -e "packages/mdconverter[dev,llm]"
mdconvert convert document.pdf
```

## Skills

| Skill | Mô tả |
|-------|--------|
| `legal-document-tracker` | Theo dõi, so sánh VBPL xây dựng |
| `completion-checklist` | Danh mục hồ sơ hoàn thành công trình |
| `seminar-builder` | Chuẩn bị nội dung seminar |
| `long-form-writer` | Viết tài liệu dài (2000+ words) |
| `ai-gateway-sdk` | Kết nối AI Gateway (22 models) |

## Workflows

| Command | Mô tả |
|---------|--------|
| `/prepare-seminar` | Chuẩn bị nội dung seminar |
| `/update-legal-registry` | Cập nhật registry VBPL |
| `/session-retrospective` | Tổng hợp kiến thức cuối phiên |
| `/new-feature` | Tạo feature branch |
| `/create-pr` | Push + tạo PR |
| `/release-feature` | Merge PR + cleanup |

## Development

```bash
# Clone
git clone https://github.com/vvChu/ccba-agent-platform.git
cd ccba-agent-platform

# Install services
pip install -e "packages/ccba-ai"
pip install -e "packages/mdconverter[dev,llm]"

# Run tests
python -m pytest packages/mdconverter/tests/

# Lint
ruff check packages/
```

## License

MIT License — developed by IBST BIM Team for Vietnamese construction industry.
