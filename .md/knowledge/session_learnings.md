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
- *(RULE-4.4, 4.5, 4.6 tại Mục 29; RULE-4.7 Mục 25; RULE-4.10, 4.11 Mục 28; chi tiết RULE-4.8 Mục 29 của archive/session_learnings_history.md)*
- **RULE-4.8 [Review Danger Triage, Read-Only Advisory & 10 Bugbot Invariants]**:
  - *Read-Only Advisory*: AI Reviewers (Bugbot, Copilot) chỉ đọc/tư vấn, CẤM gửi "APPROVE", cấm auto-merge code logic. Đối soát theo 10 Invariants tại `.github/bugbot-rules.md`.
  - *Danger Triage & Maskara*: Tệp cốt lõi $\rightarrow$ HARD human gate; Docs qua Fast-Path. Kích hoạt Opt-in (`ai-review-requested` / `/ccba-ai-review`) kèm `redact_secrets_in_text`.
- **RULE-4.12 [Structural File Addition & Architecture Drift Pre-Commit Invariant]**:
  - Thêm/xóa/đổi tên Level-1 structural files BẮT BUỘC chạy `python scripts/update_arch_stats.py` trước khi commit mở PR để đồng bộ marker trong `README.md` và `PLATFORM.md`.
- **RULE-4.13 [ADR 0063 — Peer Delegation & Cost-Turn Guardrails]**:
  - *Turn Caps*: Bắt buộc qua `invoke_grok_cli`: `AUDIT_PLAN` $\le 12$ turns (read-only), `AGENTIC_CODE` $\le 8$ turns, `PATCH_FAST` 1 turn (`--max-turns 1`).
  - *Anchor Replacement*: Task $\le 100$ LOC dùng Hợp đồng Neo `{path, blob_sha256, replacements}`. `apply_anchor_patch` validate `is_relative_to(root)` và SHA-256; cấm raw diff.
  - *Tier Routing*: `qwen-local` (0 USD) cho 1-turn; `gemini-38-flash` cho Gateway; `grok-4.7` cho deep audit.
- **RULE-4.14 [ADR 0064 — Peer Provenance, Telemetry & Zero-Hang Lifecycle]**:
  - *Zero-Hang Lifecycle*: CẤM positional prompt (gây treo TUI). BẮT BUỘC `--prompt-file`, `--output-format plain`, `subprocess.Popen` kèm watchdog terminate ngay khi file có verdict hợp lệ.
  - *Telemetry & Cost*: Khối verdict bổ sung `telemetry`; trích xuất qua `grok usage <session_id>` (retry 2 lần) + fallback `TokenEstimator`. Phân định `cost_mode: exact | estimated | unknown`.
  - *Auditor Model*: `AUDIT_PLAN` mặc định `grok-4.7` với `reasoning_effort: xhigh`.
- **RULE-4.15 [Multi-Turn Review Budgeting, Resilient Parsing & POSIX Atomicity]**:
  - *Turn Budgeting & Sandboxing*: Headless 1-turn (`patch_fast`) dùng `--deny "*"`, cấm `run_terminal_command`. Review profile có tools (`code_review`, `arch_audit`) BẮT BUỘC $\ge 10-14$ turns chống cạn lượt khi chạy `grep`/`read_file`.
  - *Resilient Parsing*: `PeerVerdictBlock` bắt buộc `extra="ignore"` và validator chuẩn hóa `list[str]` $\to$ `PeerCondition`. Khi stdout phân mảnh do tool calls, tự động quét assistant message trong `~/.grok/sessions/**/{session_id}/chat_history.jsonl`.
  - *Transactional Rollback & Mode Preservation*: `apply_anchor_patch` Phase 1 kiểm tra `target_file.is_file()`; Phase 2 hoàn nguyên qua `written_backups` và thu thập `rollback_errors` (cấm bare `pass`). `atomic_write_text` bảo tồn `stat.st_mode` của tệp đích.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
- *(Xem RULE-5.1-5.5 tại archive/session_learnings_history.md)*
- **RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines]**:
  - Structured output BẮT BUỘC tắt thinking mode (`chat_template_kwargs: {"enable_thinking": False}`) hoặc dự phòng `max_tokens` vượt ngưỡng suy nghĩ; phân tầng `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Production Mounting & Dual Parser Separation]**:
  - DGX Spark Blackwell volume mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; cấu hình tách biệt `--reasoning-parser` và `--tool-call-parser`.

