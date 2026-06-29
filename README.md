# CCBA Agent Services Platform

> Central Hub for AI Agent skills, workflows, knowledge, and internal tools.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Architecture

**Hub-and-Spoke** — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

```
ccba-agent-platform/                    ← Hub (Git-backed)
├── .agent/
│   ├── skills/                        ← AI Agent skills (7 skills)
│   │   ├── legal-document-tracker/    ←   Theo dõi VBPL
│   │   ├── completion-checklist/      ←   HSHT công trình
│   │   ├── seminar-builder/           ←   Chuẩn bị seminar
│   │   ├── long-form-writer/          ←   Viết tài liệu dài
│   │   ├── ai-gateway-sdk/           ←   Kết nối AI Gateway (22 models)
│   │   ├── maskara-privacy/          ←   Bảo mật & Quét nhạy cảm (Regex scan)
│   │   └── platform-loader/          ←   Bootstrap + routing
│   └── workflows/                     ← Automated workflows (8 workflows)
├── rules/                             ← CCBA organizational rules
├── .md/                               ← Accumulated knowledge (Project Knowledge Base)
│   ├── knowledge/                     ←   Tài liệu nghiên cứu, roadmap, spec kỹ thuật
│   ├── seminars/                      ←   Agenda, báo cáo tóm tắt seminar
│   └── extracted_docs/                ←   Văn bản pháp luật trích xuất thô
├── packages/                          ← Internal service modules
│   ├── ccba-ai/                       ←   AI Gateway client
│   └── mdconverter/                   ←   Document-to-Markdown converter
├── scripts/                           ← CLI & Lifecycle Hooks
│   ├── hooks/                         ←   Git hooks & guards (privacy, naming, scout, simplify)
│   ├── tests/                         ←   Unit test suites
│   ├── hook_runner.py                 ←   Unified Hook Runner CLI
│   ├── maskara.py                     ←   Maskara Privacy Engine CLI
│   └── validate_docs.py               ←   Documentation Accuracy Validator
└── pyproject.toml                     ← Workspace config
```

## Services & Tools

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

### validate_docs — Documentation Accuracy Validator
Quét tài liệu Markdown đối soát với codebase để phát hiện link hỏng, sai tên hàm/lớp hoặc biến môi trường thiếu trong `.env.example`.

```bash
python scripts/validate_docs.py [docs-dir] --src scripts,packages
```

## Skills

| Skill | Mô tả |
|-------|--------|
| `legal-document-tracker` | Theo dõi, so sánh VBPL xây dựng |
| `completion-checklist` | Danh mục hồ sơ hoàn thành công trình |
| `seminar-builder` | Chuẩn bị nội dung seminar |
| `long-form-writer` | Viết tài liệu dài (2000+ words) |
| `ai-gateway-sdk` | Kết nối AI Gateway (22 models) |
| `maskara-privacy` | Phát hiện, che giấu (redact) thông tin nhạy cảm và cài đặt guardrails bảo mật |

## Workflows

| Command | Mô tả |
|---------|--------|
| `/prepare-seminar` | Chuẩn bị nội dung seminar |
| `/update-legal-registry` | Cập nhật registry VBPL |
| `/session-retrospective` | Tổng hợp kiến thức cuối phiên |
| `/new-feature` | Tạo feature branch |
| `/create-pr` | Push + tạo PR |
| `/release-feature` | Merge PR + cleanup |
| `/convert-markdown` | Chuyển đổi tài liệu sang Markdown bằng mdconverter |
| `/ccba-xia` | Trích xuất, so sánh, thích ứng tính năng từ repository khác |

## Development

```bash
# Clone
git clone https://github.com/vvChu/ccba-agent-platform.git
cd ccba-agent-platform

# Install services
pip install -e "packages/ccba-ai"
pip install -e "packages/mdconverter[dev,llm]"

# Run core tests
python -m pytest packages/mdconverter/tests/

# Run Lifecycle Hooks tests
python -m unittest discover -s scripts/tests

# Lint
ruff check packages/
```

## License

MIT License — developed by IBST BIM Team for Vietnamese construction industry.
