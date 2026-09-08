# CCBA Agent Services Platform — Layer 1 Constitution

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

## Core Invariants

- **Hub vs Spoke**: Identify environment via `git remote get-url origin`. If it contains `ccba-agent-platform` $\rightarrow$ **Hub**; otherwise $\rightarrow$ **Spoke** (enforcing upstream contribution loop).
- **Reuse-First Gate**: Check `catalog.yaml` before writing any new utility. Document reuse decision in implementation plans.
- **Session Learnings Bootstrap**: Read `.md/knowledge/session_learnings.md` at the start of Planning Mode or SDLC Loop to load established patterns.
- **Automation-First Quality**: All code changes MUST pass automated `ruff check` and `mypy` static validation before completion.
- **Virtual Hub Fallback**: In Spoke mode, if a referenced skill is not physically present in `.\.agents\skills\`, the Agent MUST transparently read the skill definition directly from `[hub_path]\.agents\skills\<skill_name>\SKILL.md`.
- **Constitution Preservation**: Synchronization engines (`sync_spoke.py`) MUST perform Non-Destructive Section Merge, preserving all custom sections (e.g. `## Agent skills`, Issue Tracker, Domain Docs) in Spoke `AGENTS.md`.
- **Skills Governance & Two-Stage Decision Framework**: Mọi kỹ năng mới hoặc sửa đổi thuộc namespace ccba-* / bigbim-* phải tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057), vượt qua Cổng 0 (Determinism) và Cổng 1 (Orchestration), đạt điểm GPI >= 12.0 mới được tạo Standalone Kernel Skill (Tier 2B), và phải vượt qua `python scripts/validate_skills.py --file <path> --enforce-gpi` trước khi hoàn tất (áp dụng bắt buộc cho cả các tác vụ sửa chữa kỹ năng như /skill-repair).

## Progressive Disclosure

For detailed operational guidance, follow these domain resources:
- **Execution Guardrails & Async Tasks**: See [`docs/rules/execution_guardrails.md`](../docs/rules/execution_guardrails.md)
- **Git Conventions**: See [`docs/rules/git_conventions.md`](../docs/rules/git_conventions.md)
- **Code Quality & SDLC Loop**: See [`docs/rules/code_quality.md`](../docs/rules/code_quality.md)
- **Domain Vocabulary & ADRs**: See [`CONTEXT.md`](../CONTEXT.md) and [`docs/adr/`](../docs/adr/)
- **Monorepo Packages**: See individual `packages/*/AGENTS.md` for package-specific Deep Seams and scoped tests.
