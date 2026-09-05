# CCBA Agent Services Platform

> **Vai trò**: Central Hub cho tất cả AI Agent services, tools, skills và knowledge của CCBA.
> **Kiến trúc**: Hub-and-Spoke — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

## Cấu trúc Platform

```
ccba-agent-platform/                   ← Hub (Git-backed)
│
├── AGENTS.md                          ← Minimal Root Constitution (Layer 1 Anchor)
├── CLAUDE.md                          ← Claude Code Cross-Agent Parity Bridge
│
├── docs/                              ← Documentation & Reference
│   ├── adr/                           ←   Architectural Decision Records (ADRs)
│   └── rules/                         ←   Progressive Disclosure Rules (Guardrails, Git, Code Quality)
│
├── .agents/                           ← AI Agent configurations
│   ├── AGENTS.md                      ←   Layer 1 Constitution Mirror
│   ├── skills/                        ←   Reusable AI skills (<!-- SKILL_COUNT_START -->100<!-- SKILL_COUNT_END --> skills)
│   │   ├── ccba-legal-document-tracker/ ← Theo dõi VBPL
│   │   ├── ccba-completion-checklist/ ←   HSHT công trình
│   │   ├── ccba-seminar-builder/      ←   Chuẩn bị seminar
│   │   ├── ccba-long-form-writer/     ←   Viết tài liệu dài
│   │   ├── ccba-ai-gateway-sdk/       ←   Kết nối AI Gateway (Đa mô hình local GPU + cloud)
│   │   └── platform-loader/           ←   Bootstrap core + service routing
│   │
│   ├── workflows/                     ←   Workflows lưu trữ an toàn (.md.bak, hợp nhất vào skills)
│   └── templates/                     ←   Shared templates
│
├── .md/                               ← Central Knowledge Base (Layer 2)
│   ├── knowledge/                     ←   Tài liệu nghiên cứu, roadmap, spec kỹ thuật
│   │   └── session_learnings.md       ←     Tích lũy kinh nghiệm qua các phiên
│   ├── seminars/                      ←   Agenda, tóm tắt seminar
│   └── extracted_docs/                ←   Văn bản pháp luật trích xuất thô
│
├── packages/                          ← Internal service modules (pip installable)
│   ├── ccba-ai/                       ←   AI Gateway client, SEOAuditor & SDK
│   ├── ccba-harness/                  ←   Testing harness & Multi-Scorer Evals engine
│   ├── ccba-legal-intel/              ←   Legal intelligence connectors
│   ├── ccba-maskara/                  ←   Secret detection and redaction engine
│   ├── ccba-notebooklm/               ←   Google NotebookLM wrapper & Mock client
│   ├── ccba-ooxml/                    ←   OOXML validation and parsing engine
│   ├── ccba-pdf-prep/                 ←   PDF processing (tiling, title-block, chunks)
│   └── mdconverter/                   ←   Document converter service
│
├── scripts/                           ← CLI & Lifecycle Hooks
│   ├── governance/                    ←   Documentation, Skills & Architecture Auditors (Deep Seam)
│   ├── scaffolding/                   ←   Skill generation & AST scaffolding tools
│   ├── eval/                          ←   Process safety & evaluation gate runners
│   ├── hooks/                         ←   Git hooks & guards (privacy, naming, simplify)
│   ├── spoke/                         ←   Hub↔Spoke bootstrap, sync & migration tools (ADR 0044)
│   ├── tests/                         ←   Unit test suites
│   ├── doc_auditor.py                 ←   Governance Facade
│   ├── hook_runner.py                 ←   Unified Hook Runner CLI
│   ├── maskara.py                     ←   Maskara Privacy Engine CLI
│   ├── run_safe_eval_wrapper.py       ←   Safe Execution Sandbox (CI Gate wrapper)
│   ├── run_isolated_tests.py          ←   Cross-package Test Isolation Runner
│   └── validate_docs.py               ←   Documentation Accuracy Validator
│
└── pyproject.toml                     ← Root workspace config (uv)
```


## Phân loại Kỹ năng (Skills Classification)

Hệ thống kỹ năng (<!-- SKILL_COUNT_START -->100<!-- SKILL_COUNT_END --> skills) được phân làm hai loại chính dựa trên cơ chế kích hoạt và tương tác:

### 1. Kỹ năng kích hoạt bởi User (User-Invocable Skills)
Là các kỹ năng nhận lệnh trực tiếp từ người dùng thông qua Slash Commands (`/ccba-*` hoặc `/bigbim-*`):
*   **Quản lý Tài liệu & Quy trình:** `ccba-docs-manager` (qua `/ccba-docs-manager`), `ccba-handoff` (qua `/ccba-handoff`), `ccba-sync-upstream` (qua `/ccba-sync-upstream`).
*   **Soạn thảo & Đóng gói:** `ccba-copywriting` (qua `/ccba-copywriting`), `ccba-design` (thiết kế slides/brief), `ccba-wizard` (sinh setup scripts).
*   **Nghiệp vụ Xây dựng & Tư vấn:** `ccba-legal-document-tracker` (qua `/ccba-update-legal-registry`), `ccba-completion-checklist` (quản lý HSHT), `ccba-seminar-builder` (qua `/ccba-seminar-builder`).
*   **Kỹ thuật Phần mềm & Kiểm thử:** `ccba-code-review` (rà soát code), `ccba-xia` (port/clone tính năng qua `/ccba-xia`).
*   **Điều phối & Thẩm định:** `ccba-ai-qc` (qua `/ccba-ai-qc`), `ccba-grilling` (hỏi xoáy để test thiết kế), `ccba-wayfinder` (vạch bản đồ giải quyết bài toán mù mờ).

### 2. Kỹ năng kích hoạt tự động bởi Model (Model-Triggered / Helper Skills)
Là các thư viện bổ trợ, middleware, hoặc các cấu hình tự động kích hoạt bởi model khi thực hiện tác vụ:
*   **Bootstrap & Kết nối:** `platform-loader` (bootstrap hệ thống), `ccba-ai-gateway-sdk` (giao tiếp AI Gateway).
*   **Quy chuẩn & Pipeline:** `ccba-llm-pipeline-patterns` (patterns pipeline), `ccba-file-stability-guard` (phát hiện file sync), `ccba-api-circuit-breaker` (middleware rate limit), `ccba-append-only-logger` (thread-safe logger).
*   **Bảo mật & Kiểm định:** `ccba-maskara` (tự động quét/redact keys), `ccba-docs-validator` (linter tài liệu), `ccba-eval-gate` (kiểm định chất lượng).
*   **Master Skills với Progressive References:** `ccba-markdown-document-processing` (xử lý tài liệu Markdown), `ccba-ai-qc` (thẩm tra thiết kế đa bộ môn).
*   **Phát hiện rủi ro (BIGBIM):** `bigbim-rase`, `bigbim-governance`, `bigbim-classification`, `bigbim-risk`, `bigbim-vbpl-digest`.
*   **Thư viện phân tích file:** `ccba-pdf`, `ccba-pptx`, `ccba-docx` (các parser/manipulator định dạng OOXML/PDF).
*   **Hỗ trợ phát triển:** `ccba-diagnosing-bugs` (chẩn đoán bug), `ccba-writing-great-skills` (quy chuẩn thiết kế skill).

## Service Modules

| Package | Mô tả | Install |
|---------|--------|---------|
| `ccba-ai` | AI Gateway client & SDK — Đa mô hình (local GPU + cloud), 1 endpoint | `pip install -e "packages/ccba-ai"` |
| `ccba-harness` | Testing harness and multi-scorer evaluation engine | `pip install -e "packages/ccba-harness"` |
| `ccba-legal-intel` | Legal intelligence services, legislative consolidator, OKF v2.4 GoldStandard, Gate 4 & Federated RAG | `pip install -e "packages/ccba-legal-intel"` |
| `ccba-maskara` | Secret detection, redaction and commit privacy engine | `pip install -e "packages/ccba-maskara"` |
| `ccba-notebooklm` | Google NotebookLM API wrapper & mock client | `pip install -e "packages/ccba-notebooklm"` |
| `ccba-ooxml` | OOXML document structure integrity validator | `pip install -e "packages/ccba-ooxml"` |
| `ccba-pdf-prep` | PDF Preprocessing pipeline (tiling, title-block, chunks) | `pip install -e "packages/ccba-pdf-prep"` |
| `mdconverter` | Document-to-Markdown converter service | `pip install -e "packages/mdconverter"` |

## Cách sử dụng

### Khi mở bất kỳ project nào

1. Agent tự động đọc `user_global` rules → biết Hub location
2. Agent truy cập Hub để lấy skills, rules, knowledge
3. Agent đọc `.md/workspace_context.yaml` của project (nếu có) để lấy local overrides
4. Xử lý công việc bằng skills từ Hub
5. Lưu output cuối cùng về project folder

### Khi cần skill mới

1. Tạo folder trong `.agents/skills/{tên-skill}/`
2. Viết `SKILL.md` theo format chuẩn (YAML frontmatter + instructions)
3. Thêm data/, templates/ nếu cần
4. Đăng ký trong `catalog.yaml`

### Khi thêm service module mới

1. Tạo folder trong `packages/{tên-service}/`
2. Thêm `pyproject.toml` với dependencies riêng
3. Tạo `src/{package_name}/` + `tests/`
4. Install: `pip install -e packages/{tên-service}`

### Khi mở project mới (Spoke)

1. Tạo `.md/workspace_context.yaml` với Hub reference
2. Ghi lại local settings đặc thù (output format, focus area)
3. Done — Agent sẽ kết hợp Hub skills + local context

## Principles

1. **Hub chứa tools** — Skills, workflows, knowledge, rules, packages
2. **Spoke chứa context** — Chỉ local config đặc thù
3. **Output về đích** — Kết quả cuối cùng lưu tại project folder
4. **Git-backed** — Mọi thay đổi tracked, có thể rollback
5. **Modular services** — Mỗi package là 1 service độc lập, pip-installable
6. **Rules enforce identity** — Đảm bảo output mang bản sắc CCBA

## Repository

- **GitHub**: [vvChu/ccba-agent-platform](https://github.com/vvChu/ccba-agent-platform)
- **Local**: `D:\GitHubProjects\ccba-agent-platform`
