# CCBA Agent Services Platform

> Central Hub for AI Agent skills, workflows, knowledge, and internal tools. 

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Architecture

**Hub-and-Spoke** — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

```
ccba-agent-platform/                    ← Hub (Git-backed)
├── .agents/
│   ├── skills/                        ← AI Agent skills (<!-- SKILL_COUNT_START -->80<!-- SKILL_COUNT_END --> skills) <!-- Last verified: 2026-08-11 -->
│   │   ├── legal-document-tracker/    ←   Theo dõi VBPL
│   │   ├── completion-checklist/      ←   HSHT công trình
│   │   ├── seminar-builder/           ←   Chuẩn bị seminar
│   │   ├── docs-validator/            ←   Linter tài liệu tĩnh (Patched)
│   │   ├── architecture-sync/         ←   Đồng bộ hiến pháp kiến trúc (Patched)
│   │   └── ...                        ←   Và 52+ kỹ năng chuyên dụng khác
│   ├── workflows/                     ← Automated workflows (<!-- WORKFLOW_COUNT_START -->0<!-- WORKFLOW_COUNT_END --> workflows)
│   └── templates/                     ← Shared templates
├── .md/                               ← Central Knowledge Base (Project Knowledge Base)
│   ├── knowledge/                     ←   Tài liệu nghiên cứu, roadmap, spec kỹ thuật
│   ├── seminars/                      ←   Agenda, tóm tắt seminar
│   └── extracted_docs/                ←   Văn bản pháp luật trích xuất thô
├── packages/                          ← Internal service modules (pip installable)
│   ├── ccba-ai/                       ←   AI Gateway client & SDK
│   ├── ccba-harness/                  ←   Testing harness utilities
│   ├── ccba-legal-intel/              ←   Legal intelligence connectors
│   ├── ccba-notebooklm/               ←   Google NotebookLM wrapper & Mock client
│   ├── ccba-ooxml/                    ←   OOXML validation and parsing engine
│   ├── ccba-pdf-prep/                 ←   PDF processing (tiling, title-block, chunks)
│   └── mdconverter/                   ←   Document-to-Markdown converter
├── scripts/                           ← CLI & Lifecycle Hooks
│   ├── hooks/                         ←   Git hooks & guards (privacy, naming, simplify)
│   ├── tests/                         ←   Unit test suites
│   ├── hook_runner.py                 ←   Unified Hook Runner CLI
│   ├── maskara.py                     ←   Maskara Privacy Engine CLI
│   ├── safe_pytest.py                 ←   Safe Scoped Pytest Execution Wrapper
│   └── validate_docs.py               ←   Documentation Accuracy Validator
├── conftest.py                        ← Pytest Scoped Guardrail Hook
└── pyproject.toml                     ← Workspace config
```

## Services & Tools

### ccba-ai — AI Gateway Client

Kết nối AI Gateway trên Server Spark — 22 models, 1 endpoint.

```python
from ccba_ai import ai
reply = ai.chat("Xin chào!")
```

### ccba-pdf-prep — PDF Preprocessor
Phân mảnh thông minh (tiling) lọc pixel trắng, bóc tách khung tên (title block) và chia nhỏ PDF cho mô hình AI Vision.

```python
from ccba_pdf_prep import PDFProcessingPipeline
pipeline = PDFProcessingPipeline()
result = pipeline.process(pdf_path, output_dir)
```

### ccba-notebooklm — NotebookLM Cloud Connector
Tích hợp Google NotebookLM Cloud RAG, sinh podcast audio overview, quiz, slides... Hỗ trợ Mock Client giả lập chạy test/CI-CD không cần cookies.

### ccba-ooxml — OOXML Validator
Kiểm định tính toàn vẹn cấu trúc file Office XML (.docx, .pptx) và bóc tách tracked changes thông qua deep validator seam.

### mdconverter — Document Converter
Modern Document to Markdown Converter với hỗ trợ đặc thù cho cấu trúc văn bản pháp luật xây dựng Việt Nam.

### validate_docs — Documentation Accuracy Validator
Quét tài liệu Markdown đối soát với codebase để phát hiện link hỏng, sai tên hàm/lớp hoặc biến môi trường thiếu trong `.env.example`.

```bash
python scripts/validate_docs.py [docs-dir] --src scripts,packages
```

## Workflows

| Command | Mô tả |
|---------|--------|
| `/ccba-prepare-seminar` | Chuẩn bị nội dung seminar |
| `/ccba-update-legal-registry` | Cập nhật registry VBPL |
| `/ccba-session-retrospective` | Tổng hợp kiến thức cuối phiên |
| `/ccba-new-feature` | Tạo feature branch |
| `/ccba-create-pr` | Push + tạo PR |
| `/ccba-release-feature` | Merge PR + cleanup |
| `/ccba-convert-markdown` | Chuyển đổi tài liệu sang Markdown bằng mdconverter |
| `/ccba-xia` | Trích xuất, so sánh, thích ứng tính năng từ repository khác |
| `/ccba-brainstorm` | Khởi động phiên thảo luận ý tưởng và chuẩn bị tài liệu đầu vào |
| `/ccba-init-spoke` | Khởi tạo dự án con (Spoke) tuân thủ kiến trúc CAP |
| `/ccba-run-qc-pipeline` | Chạy chuỗi kiểm soát chất lượng (QC) đa bộ môn |
| `/ccba-propose-to-hub` | Đề xuất tích hợp skill/workflow mới từ Spoke lên Hub |
| `/ccba-update-spoke` | Cập nhật thủ công các lệnh và kỹ năng mới từ Hub về Spoke |
| `/ccba-discard-feature` | Hủy bỏ branch hiện tại cả local và remote |
| `/ccba-sync-upstream` | Kiểm tra cập nhật và đồng bộ tri thức từ ClaudeKit và MattPocock |
| `/ccba-improve-codebase-architecture` | Quét phát hiện module nông (shallow modules) và sinh sơ đồ Mermaid đề xuất refactor |
| `/ccba-build-skill` | Nghiên cứu tài liệu và đóng gói tạo Skill mới đạt chuẩn CCBA |
| `/ccba-copywriting` | Soạn thảo tài liệu, biểu mẫu hành chính/thương mại |
| `/ccba-docs` | Cập nhật, đồng bộ và kiểm định tài liệu tĩnh |
| `/ccba-extract-style` | Trích xuất văn phong hành chính/thầu từ tài liệu mẫu |
| `/ccba-git-guardrails` | Kích hoạt rào chắn ngăn lệnh Git nguy hiểm |
| `/ccba-grilling` | Phỏng vấn dồn dập để kiểm chứng kế hoạch hoặc thiết kế |
| `/ccba-handoff` | Đóng gói phiên làm việc chuyển giao context |
| `/ccba-notebooklm` | RAG query, import tài liệu và tạo Audio Overview |
| `/ccba-resolving-merge-conflicts` | Giải quyết xung đột merge/rebase an toàn |
| `/ccba-review-skill` | Đánh giá chất lượng và tối ưu hóa file SKILL.md |
| `/ccba-tdd` | Thiết kế và viết code theo quy trình TDD |
| `/ccba-wayfinder` | Phân tích giải quyết bài toán mù mờ (foggy problems) |
| `/ccba-wizard` | Tạo bash script setup môi trường dev tương tác |
| `/workflow_pccc_cdt_tuthamdinh` | Quy trình hỗ trợ Chủ đầu tư Tự thẩm định thiết kế PCCC |
| `/workflow_pccc_thamdinh_congan` | Quy trình Thẩm định thiết kế PCCC phần MEP nộp PC07 |
| `/workflow_pccc_thamdinh_cqxd` | Quy trình Thẩm định PCCC phần Kiến trúc nộp Cơ quan xây dựng |

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
