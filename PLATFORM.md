# CCBA Agent Services Platform

> **Vai trò**: Central Hub cho tất cả AI Agent services, tools, skills và knowledge của CCBA.
> **Kiến trúc**: Hub-and-Spoke — Hub lưu trữ tập trung, mỗi project (Spoke) chỉ lưu config riêng.

## Cấu trúc Platform

```
ccba-agent-platform/                   ← Hub (Git-backed)
│
├── .agent/                            ← AI Agent configurations
│   ├── skills/                        ← Reusable AI skills
│   │   ├── legal-document-tracker/    ←   Theo dõi VBPL
│   │   ├── completion-checklist/      ←   HSHT công trình
│   │   ├── seminar-builder/           ←   Chuẩn bị seminar
│   │   ├── long-form-writer/          ←   Viết tài liệu dài
│   │   └── ai-gateway-sdk/           ←   Kết nối AI Gateway (22 models)
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
├── scripts/                           ← Deterministic scripts
├── templates/                         ← Shared templates
├── tools/                             ← CLI tools, MCP servers
│
├── packages/                          ← Internal Python packages
│   └── ccba-ai/                      ←   AI Gateway client (pip install -e)
├── .md/                               ← Processing workspace (gitignored)
└── src/                               ← Core library code
```

## Cách sử dụng

### Khi mở bất kỳ project nào

1. Agent tự động đọc `user_global` rules → biết Hub location
2. Agent truy cập Hub để lấy skills, rules, knowledge
3. Agent đọc `.md/workspace_context.yaml` của project (nếu có) để lấy local overrides
4. Xử lý công việc bằng skills từ Hub
5. Lưu output cuối cùng về project folder

### Khi cần skill mới

1. Tạo folder trong `.agent/skills/{tên-skill}/`
2. Viết `SKILL.md` theo format chuẩn (YAML frontmatter + instructions)
3. Thêm data/, templates/ nếu cần
4. Skill tự động available cho mọi project

### Khi mở project mới (Spoke)

1. Tạo `.md/workspace_context.yaml` với Hub reference
2. Ghi lại local settings đặc thù (output format, focus area)
3. Done — Agent sẽ kết hợp Hub skills + local context

## Principles

1. **Hub chứa tools** — Skills, workflows, knowledge, rules
2. **Spoke chứa context** — Chỉ local config đặc thù
3. **Output về đích** — Kết quả cuối cùng lưu tại project folder
4. **Git-backed** — Mọi thay đổi tracked, có thể rollback
5. **Rules enforce identity** — Đảm bảo output mang bản sắc CCBA

## Repository

- **GitHub**: [vvChu/ccba-agent-platform](https://github.com/vvChu/ccba-agent-platform)
- **Local**: `D:\GitHubProjects\ccba-agent-platform`
