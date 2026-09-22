# CCBA Agent Services Platform — Layer 1 Constitution

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

## Core Invariants

- **Hub vs Spoke**: Identify environment via `git remote get-url origin`. If it contains `ccba-agent-platform` $\rightarrow$ **Hub**; otherwise $\rightarrow$ **Spoke** (enforcing upstream contribution loop).
- **Reuse-First Gate**: Check `catalog.yaml` before writing any new utility. Document reuse decision in implementation plans.
- **Session Learnings Bootstrap**: Read `.md/knowledge/session_learnings.md` at the start of Planning Mode or SDLC Loop to load established patterns.
- **Automation-First Quality & Deterministic Hard Completion Lock (ADR-0058)**: All code, skill, and artifact changes MUST pass automated deterministic verification via `python -m ccba_harness verify-patch` (or scoped verify presets) before completion. The Agent is strictly forbidden from claiming task completion or requesting user sign-off if any verification command exits with code $\ne 0$.
- **Virtual Hub Fallback**: In Spoke mode, if a referenced skill is not physically present in `.\.agents\skills\`, the Agent MUST transparently read the skill definition directly from `[hub_path]\.agents\skills\<skill_name>\SKILL.md`.
- **Constitution Preservation**: Synchronization engines (`sync_spoke.py`) MUST perform Non-Destructive Section Merge, preserving all custom sections (e.g. `## Agent skills`, Issue Tracker, Domain Docs) in Spoke `AGENTS.md`.
- **Skills Governance & Two-Stage Decision Framework**: Mọi kỹ năng mới hoặc sửa đổi thuộc namespace ccba-* / bigbim-* phải tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057), vượt qua Cổng 0 (Determinism) và Cổng 1 (Orchestration), đạt điểm GPI >= 12.0 mới được tạo Standalone Kernel Skill (Tier 2B), và phải vượt qua `python scripts/validate_skills.py --file <path> --enforce-gpi` trước khi hoàn tất (áp dụng bắt buộc cho cả các tác vụ sửa chữa kỹ năng như /skill-repair).
- **Legal Verbatim Grounding & Mandatory Acquisition Invariant (ADR-0059)**: All legal knowledge bundles, fixtures, and citation claims MUST strictly mirror verbatim text from official gazette sources (PDF/DOCX) with cryptographic SHA-256 provenance stamping. AI Agents are strictly prohibited from generating hypothetical or synthetic mock clauses for statutory documents. When a source document is missing, the Agent MUST acquire it via `TVPLCrawler` or immediately request the source file from the user before proceeding.
- **Multi-Client Peer Claim Locking Invariant**: Before claiming or working on any GitHub Issue or Pull Request, the Agent MUST verify that it does not have an active `in-progress` label or recent Claim Notice from a peer agent. Active tasks (< 24h for issues, < 4h for PRs) MUST be bypassed to prevent collisions and merge races. When claiming an issue or PR, the Agent MUST immediately transition status to `in-progress`, assign `@me`, and post a machine-parseable Claim Notice comment. Pre-push lease: always use `--force-with-lease`, never bare `--force`. Detailed takeover & TTL protocol: see [`docs/rules/execution_guardrails.md`](../docs/rules/execution_guardrails.md).
- **Single-User Multi-Device & Machine-State Decoupling**: Khi một repository Spoke được clone về nhiều máy (Windows, Linux, WSL), cấm tuyệt đối chạy các lệnh tái khởi tạo (`/ccba-init-spoke`, `/ccba-spoke-adopter`) hoặc commit đường dẫn ổ đĩa tuyệt đối vào `workspace_context.yaml`. Đường dẫn Hub trên từng máy phải được cô lập độc lập qua biến môi trường `CCBA_HUB_PATH`.
- **Remote Mutation Idempotency & State Inspection Gate**: Khi thực thi bất kỳ lệnh nào tạo hoặc chỉnh sửa tài nguyên trên remote (GitHub CLI `gh issue/pr create`, `git push`, Cloud Sync), nếu tiến trình bị gián đoạn, timeout hoặc huỷ giữa chừng, Agent BẮT BUỘC phải truy vấn trạng thái remote trước khi chạy lại lệnh, ngăn chặn triệt để việc phát sinh tài nguyên trùng lặp (duplicate issues/PRs).


## Progressive Disclosure

For detailed operational guidance, follow these domain resources:
- **Execution Guardrails & Async Tasks**: See [`docs/rules/execution_guardrails.md`](../docs/rules/execution_guardrails.md)
- **Git Conventions**: See [`docs/rules/git_conventions.md`](../docs/rules/git_conventions.md)
- **Code Quality & SDLC Loop**: See [`docs/rules/code_quality.md`](../docs/rules/code_quality.md)
- **Domain Vocabulary & ADRs**: See [`CONTEXT.md`](../CONTEXT.md) and [`docs/adr/`](../docs/adr/)
- **Monorepo Packages**: See individual `packages/*/AGENTS.md` for package-specific Deep Seams and scoped tests.
