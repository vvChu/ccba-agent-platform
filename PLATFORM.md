# CCBA Agent Services Platform

> **Vai trò**: Central Hub cho tất cả AI Agent services, tools, skills và knowledge của CCBA.
> **Kiến trúc**: Hub-and-Spoke — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

## Cấu trúc Platform

```
ccba-agent-platform/                   ← Hub (Git-backed)
│
├── .agents/                           ← AI Agent configurations
│   ├── skills/                        ← Reusable AI skills
│   │   ├── legal-document-tracker/    ←   Theo dõi VBPL
│   │   ├── completion-checklist/      ←   HSHT công trình
│   │   ├── seminar-builder/           ←   Chuẩn bị seminar
│   │   ├── long-form-writer/          ←   Viết tài liệu dài
│   │   ├── ai-gateway-sdk/            ←   Kết nối AI Gateway (22 models)
│   │   └── platform-loader/           ←   Bootstrap + service routing
│   └── workflows/                     ← Automated workflows
│       ├── prepare-seminar.md
│       ├── update-legal-registry.md
│       ├── session-retrospective.md
│       └── [git workflows]
│
├── rules/                             ← CCBA organizational rules
│   ├── ccba_identity.md               ←   Brand & voice
│   ├── quality_standards.md           ←   QC tiêu chuẩn
│   ├── naming_conventions.md          ←   Quy ước đặt tên
│   └── compliance.md                  ←   Tuân thủ pháp luật
│
├── knowledge/                         ← Accumulated knowledge
│   └── session_learnings.md           ←   Patterns, anti-patterns
│
├── packages/                          ← Internal service modules
│   ├── ccba-ai/                       ←   AI Gateway client & SDK
│   ├── ccba-harness/                  ←   Testing harness utilities
│   ├── ccba-legal-intel/              ←   Legal intelligence connectors
│   ├── ccba-notebooklm/               ←   Google NotebookLM wrapper & Mock client
│   ├── ccba-ooxml/                    ←   OOXML validation and parsing engine
│   ├── ccba-pdf-prep/                 ←   PDF processing (tiling, title-block, chunks)
│   └── mdconverter/                   ←   Document converter service
│
├── scripts/                           ← Utility scripts
├── templates/                         ← Shared templates
├── tools/                             ← CLI tools, MCP servers
│
├── .md/                               ← Central Knowledge Base (Layer 2 - structure tracked, temp files ignored)
└── pyproject.toml                     ← Root workspace config (uv)
```

## Service Modules

| Package | Mô tả | Install |
|---------|--------|---------|
| `ccba-ai` | AI Gateway client & SDK — 22 models, 1 endpoint | `pip install -e "packages/ccba-ai"` |
| `ccba-harness` | Testing harness and mocking utilities | `pip install -e "packages/ccba-harness"` |
| `ccba-legal-intel` | Legal intelligence services and connectors | `pip install -e "packages/ccba-legal-intel"` |
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
