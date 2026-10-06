# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Tiêu chuẩn:** ADR 0030, 0031, 0035, 0041, 0057, 0058.
> **Lịch sử & Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Thuần giải thuật/IO $\rightarrow$ Deep Seams (`packages/*/src/`). `SKILL.md` không code trần.
  - *Cổng 1 (Orchestration)*: Đa luồng/StateGraph/HITL $\rightarrow$ Tier 3 Composite Orchestrator (bỏ qua GPI).
  - *Chỉ số GPI*: $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $< 12.0 \rightarrow$ Tier 2A; $\ge 12.0 \rightarrow$ Tier 2B. Rituals: $A = 1.0$.
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051] tại Mục 23, 27; RULE-1.9 Mục 24; RULE-1.6, 1.8 Mục 25 của archive/session_learnings_history.md)*
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - Tái sử dụng Package Seams / Master Skills có sẵn là KISS bậc 1; CẤM script chắp vá. Tra cứu Seam qua CLI (`compile_catalog.py --query <kw>`). CẤM hoãn kiến trúc chuẩn sang Phase 2.
- **RULE-1.12 [ADR 0060 — Team Whitelist & Federated Architecture]**:
  - *Team Whitelist*: BẮT BUỘC unignore `!.agents/teams/` trong `.gitignore` lưu trữ team specs.
  - *Federated Hubs Alignment*: 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị chia sẻ tri thức qua CLI/REST/gRPC.
- **RULE-1.13 [Parameter Externalization & Declarative Config]**:
  - CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP. Dùng `choose_model()` / `ModelArchetype` và env vars (ngoại lệ: `# ccba:allow-raw-model`, `# ccba:allow-raw-ip`). Tách config theo OCP.
- **RULE-1.14 [ADR 0062 — Declarative Sync Registry & Fail-Closed Gate]**:
  - *Fail-Closed Gate*: `assess_catalog_freshness` chặn đứng `--apply` (exit 1) khi `catalog.yaml` stale. Cờ `--allow-stale-catalog` ghi audit log bypass.
  - *Declarative Registry & Topo*: Khai báo guardrails và package bindings trong `catalog_base.yaml`; `spoke_bootstrap.py` phân giải install set theo Kahn's topo sort.
- **RULE-1.15 [ADR 0057 — Upstream Retro Diagnostics & Deterministic Checks Invariant]**:
  - *Retro Diagnostics & Level 3 Index*: Khi có ma sát công cụ / lặp lỗi, đọc `references/agent_environment_diagnostics.md`. Kỹ năng có `references/` BẮT BUỘC khai báo Level 3 Reference Index trong `SKILL.md`.
  - *Deterministic Checks over Rules*: Lỗi cơ học BẮT BUỘC tạo automated linter/CI check (`verify-patch`, pre-commit); CẤM thêm prompt rules vào `AGENTS.md` gây Attention Dilution (ADR-0030).
- **RULE-1.16 [Lexical Analysis Naming & Maskara False-Positive Decoupling]**:
  - Trong code tokenizer/AST, CẤM đặt tên biến gán chứa chuỗi con `token` (`tokens = ...`, `name_tokens = ...`) với biểu thức $\ge 8$ ký tự tránh kích hoạt nhầm rule `env-secret` của Maskara trên PR diff. BẮT BUỘC dùng danh từ trung tính: `lex_items`, `lexemes`, `name_parts`, `name_vocab`.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- *(RULE-2.1, 2.3, 2.4 Mục 27; RULE-2.8, 2.10, 2.11 Mục 24; RULE-2.12 Mục 25; RULE-2.14 Mục 28 của archive/session_learnings_history.md)*
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing, Disjoint Hierarchy & 100% Skill Coverage]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) BẮT BUỘC dùng `archetypes.py` làm SSOT (17 archetypes).
  - *Disjoint Hierarchy*: Archetype chuyên biệt (`platform_tooling`, `legal_tooling`, `visual_design`) đứng trước archetype khái quát (`orchestration`, `legal`, `visual`). 100% kỹ năng (75/75 skills) map chuẩn xác; cấm unmapped (`None`).
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - *Env & Live Lock Isolation*: Test fixtures/runners (`conftest.py`) BẮT BUỘC xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock triệt để lock vật lý (`is_kernel_runner_locked`, `check_daemon_lock`, `/tmp/*.lock` $\rightarrow$ `False`). CẤM rò rỉ biến môi trường hoặc đọc lock thật.
- **RULE-2.13 [Atomic Micro-PR Slicing & Single-Seam Locality]**:
  - *Micro-Task Slicing*: Phân rã task $\le 150-200$ LOC logic vào 1 Deep Seam duy nhất kèm test tự động; chia nhỏ task phức tạp thành micro-PRs giảm review fatigue và conflict.
- **RULE-2.15 [Atomic Knowledge Cataloging, Hermetic Scripts & Ruff Guard]**:
  - Tệp `.md` mới trong `.md/knowledge/` BẮT BUỘC biên mục vào `index.md` ngay commit tạo tệp chống lỗi Orphan Notes. Shell script đa dòng dùng `cat << 'EOF'` chống lỗi nháy. Callable động dùng `hasattr(obj, "m") and callable(obj.m)`.
- **RULE-2.18 [AST Comment Sanitation & Anti-Slop Discipline]**:
  - Mọi code Python qua 7-Stage Gate `check_redundant_comments`. Dùng `tokenize` bảo toàn comments, bọc hàm/block header phát hiện dead code (`def`, `class`, `import`, `return`), và cấm comment $\le 5$ từ dịch tên định danh. Giữ nguyên allowlist chỉ thị và trích dẫn pháp lý.
- *(RULE-2.16, 2.17 tại Mục 28, 30 của archive/session_learnings_history.md)*

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - Viện dẫn BẮT BUỘC CÒN HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP**.
- *(RULE-3.2 [ADR 0031 — TVPL VIP] tại Mục 27 của archive/session_learnings_history.md)*
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span bắt buộc bao trọn toàn văn quy phạm; cấm span 1 dòng chỉ trỏ `<a>`. Tests dùng `tmp_path / "legal_registry.yaml"`.
- **RULE-3.5 [Documentation Link Scheme Portability Invariant]**:
  - `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`. BẮT BUỘC dùng relative paths hoặc repo-relative links.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Có Issue ID: LUÔN đề xuất `/ccba-new-feature #<id>` (8 bước Factory Model).
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - Đối chiếu `catalog.yaml` trước khi đề xuất `/command`. Chỉ kỹ năng có `command: /...` mới gắn tiền tố `/`.
- *(RULE-4.4-4.7, 4.10, 4.11 tại Mục 25, 28, 29 của archive/session_learnings_history.md)*
- **RULE-4.8 [Review Danger Triage, Read-Only Advisory & 10 Bugbot Invariants]**:
  - AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic. Core files $\rightarrow$ HARD human gate; Docs qua Fast-Path.
- **RULE-4.12 [Structural File Addition & Architecture Drift Pre-Commit Invariant]**:
  - Thêm/xóa/đổi tên Level-1 files BẮT BUỘC chạy `python scripts/update_arch_stats.py` trước khi commit để đồng bộ marker `README.md` và `PLATFORM.md`.
- **RULE-4.13 [ADR 0063 — Peer Delegation & Cost-Turn Guardrails]**:
  - *Turn Caps*: `AUDIT_PLAN` $\le 12$ turns, `AGENTIC_CODE` $\le 8$ turns, `PATCH_FAST` 1 turn (`--max-turns 1`). Hợp đồng Neo validate SHA-256 & `is_relative_to(root)`. Tier routing: `qwen-local` $\to$ `gemini-38-flash` $\to$ `grok-4.7`.
- **RULE-4.14 [ADR 0064 — Peer Provenance, Telemetry & Zero-Hang Lifecycle]**:
  - *Zero-Hang*: Dùng `--prompt-file`, `--output-format plain`, `subprocess.Popen` kèm watchdog. Khối verdict bổ sung `telemetry` (exact/estimated). `AUDIT_PLAN` chạy `grok-4.7` với `xhigh`.
- **RULE-4.15 [Multi-Turn Review Budgeting, Resilient Parsing & POSIX Atomicity]**:
  - Turn budget tools review $\ge 10-14$ turns. `PeerVerdictBlock` hỗ trợ `extra="ignore"`, Pydantic conditions coercion và session history fallback. `apply_anchor_patch` kiểm tra `is_file()`, rollback gom lỗi, và bảo tồn `stat.st_mode`.


---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
- *(Xem RULE-5.1-5.5 tại archive/session_learnings_history.md)*
- **RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines]**:
  - Structured output BẮT BUỘC tắt thinking mode (`chat_template_kwargs: {"enable_thinking": False}`) hoặc dự phòng `max_tokens` vượt ngưỡng suy nghĩ; phân tầng `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Production Mounting & Dual Parser Separation]**:
  - DGX Spark Blackwell volume mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; cấu hình tách biệt `--reasoning-parser` và `--tool-call-parser`.

