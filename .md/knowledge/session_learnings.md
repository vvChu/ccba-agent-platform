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
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051], RULE-1.6..1.9, 1.15..1.17, 1.19, 1.21 tại Mục 23-27, 33-36 history: `supersede_graduated_spoke_docs` lưu `<stem>.local-<sha8>.md` & khử link `file://` trong `.md/INDEX.md`)*
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - Tái sử dụng Package Seams / Master Skills là KISS bậc 1 (`compile_catalog.py --query <kw>`); CẤM script chắp vá hoặc hoãn sang Phase 2.
- **RULE-1.12 [ADR 0060 — Team Whitelist & Federated Architecture]**:
  - Unignore `!.agents/teams/` trong `.gitignore`. 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị qua CLI/REST/gRPC.
- **RULE-1.13 [Parameter Externalization & Active Cleanliness Guardrails]**:
  - CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP; dùng `choose_model()` / `ModelArchetype` & env vars (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`). `check_spoke_cleanliness.py` nối `check_raw_model_leakage` (AST) & `check_raw_ip_leakage` (`was_in_docstring`) vào `scan_spoke_cleanliness()` (Mục 41 history).
- **RULE-1.14 [ADR 0062 — Declarative Sync Registry & Fail-Closed Gate]**:
  - `assess_catalog_freshness` chặn `--apply` (exit 1) khi `catalog.yaml` stale (`--allow-stale-catalog` ghi audit log). Bindings tại `catalog_base.yaml`; `spoke_bootstrap.py` dùng Kahn's topo sort.
- **RULE-1.18 [ADR 0066 — Skills Taxonomy & Scope Declaration]**:
  - `bundle: _core` chỉ chứa SDLC loop; `_software` chứa nghiệp vụ code. Frontmatter khai báo `scope: hub | spoke | universal`; linter chặn `command: /...` ở `_governance` thiếu `scope: hub` & đối soát GPI (COND-01).
- **RULE-1.20 [ADR 0061 — Posture Title, Parity Radar & Contract Inflation]**:
  - Dùng đúng `## 🏛️ Platform-Aware Architecture Posture` (0 số ADR trong header); CẤM token ADR không tạo ADR mới (`sync_hub_adr_matrix.py`). 16 Deep Seams `package-bound`; 60 skills `seam-exempt`.
- **RULE-1.22 [Reasoning Tiering Parity & Anti-Silent-Degradation]**:
  - Tác vụ suy luận giữ Class A; CẤM fallback về Class C (`ocr-tier4`, `ocr-fallback`). Cạn quota Class A $\rightarrow$ **Fail-Fast** (HTTP 503) (Mục 38 history).
- **RULE-1.23 [ADR 0067 — 3-Tier One-Way Door Manifest & Backpressure]**:
  - `classify_pr_door` (`door_policy.py`) phân loại `TWO_WAY_DOOR`, `PAVED_ROAD`, `ONE_WAY_DOOR` (`ONE_WAY_DOOR_MANIFEST` 7 nhóm) & `compute_cumulative_streak` cấp `packages/<pkg>` ($K \ge 3$ PRs/72h hoặc $>200$ LOC $\to$ `ONE_WAY_DOOR`, mẫu 10% `is_sampled_for_audit`). `evaluate_backpressure_queue` (`backpressure.py`) ngắt mạch khi $>5$ PRs hoặc $>24\text{h}$; `validate_tradeoff_card` bắt buộc `Core Invariant`, `Invalidation Condition`, `Git Hunk Reference` ($\le 30$ dòng) qua `ccba-harness door-triage` (Mục 40 history).
- **RULE-1.24 [Federated Role & ERP Lifecycle Boundary — ADR 0046 vs IDOP-CCBA-WAY]**:
  - 15 `ROLE_ID` (`06_ccba_org_role_matrix.md`) & ERP 5 pha (`OPPORTUNITY` $\to$ `SETTLEMENT` / `PGV` P&L) thuộc SharePoint `IDOP-CCBA-WAY` (`ADR-0060`). Tại Hub, SSOT là **ADR-0046** (`seat_role` + 5 cấp QC, giữ `CHU_TRI_BO_MON`), bàn giao qua `idop_bridge.py` (`StagedSubmittal`), quota qua LiteLLM Virtual Keys + `telemetry.py`/`fleet.py`. CẤM Dual-SSOT hoặc tiêm `ROLE_ID` vào System Prompt (`ADR-0040`) (Mục 42 history).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- *(RULE-2.1..2.4, 2.8, 2.10..2.19 tại Mục 24-35 history: `.md/knowledge/` biên mục vào `index.md` chống Orphan Notes; `cat << 'EOF'`)*
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing & 100% Skill Coverage]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) dùng `archetypes.py` (17 archetypes); archetype chuyên biệt (`platform_tooling`, `legal_tooling`, `visual_design`) đứng trước khái quát (`orchestration`, `legal`, `visual`); cấm `None`.
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - `conftest.py` xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock lock vật lý (`is_kernel_runner_locked`, `check_daemon_lock` $\rightarrow$ `False`).
- **RULE-2.20 [Static Module Size Budget & Template Sanitizer Precision]**:
  - CẤM monofile $> 500$ LOC và CLI post-parse body $> 40$ LOC (quarantine có hạn). Scanner secret phân định f-string (`^\{[A-Za-z_][A-Za-z0-9_.]*[:,\s]`) với JSON literal `{"`.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - Viện dẫn CÒN HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP**. *(RULE-3.2 [ADR 0031 — TVPL VIP] tại Mục 27 history)*.
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span bao trọn toàn văn quy phạm; cấm span 1 dòng chỉ trỏ `<a>`. Tests dùng `tmp_path / "legal_registry.yaml"`.
- **RULE-3.5 [Documentation Link Scheme Portability Invariant]**:
  - `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`; dùng relative paths.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 & 4.2 [Entry Point `/ccba-new-feature` & Slash Command Parity]**:
  - Có Issue ID $\rightarrow$ `/ccba-new-feature #<id>` (8 bước). Đối chiếu `catalog.yaml` (`command: /...`) trước khi đề xuất `/command`.
- *(RULE-4.4..4.7, 4.10, 4.11, 4.13..4.15 tại Mục 25, 28-33 history: Turn budget review $\ge 10-14$ turns; `PeerVerdictBlock` `extra="ignore"`; `apply_anchor_patch` kiểm tra `is_file()` & `stat.st_mode`)*
- **RULE-4.8 & 4.12 [Review Danger Triage & Architecture Drift Pre-Commit]**:
  - AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic (`door-triage`). Thêm/xóa/đổi tên Level-1 files BẮT BUỘC chạy `python scripts/update_arch_stats.py` đồng bộ `README.md` & `PLATFORM.md`.
- **RULE-4.16 [Two-Pass Peer Review Protocol & Atomic Micro-PR Slicing]**:
  - Pass 1 (`APPROVE_PLAN`) đóng băng thiết kế; Pass 2 (`APPROVE`) đối soát reflog (`xhigh` timeout $\ge 900$s). Phân rã 7-8 skills thành 4 micro-PRs, khóa cục bộ bằng bộ 3 lệnh (< 1s) trước `verify-patch --preset ci`.
- **RULE-4.17 [Adversarial Rebuttal on `audit_direct`, Tool-Starvation Defense & CLI Parity]**:
  - Khi `audit_direct` suy diễn sai thuộc tính hoặc đòi GitHub API khi CI có `fetch-depth: 0`, đối chiếu AST tinh chỉnh theo KISS; ưu tiên `audit_direct --no-tools` khi plan đủ ngữ cảnh; đồng bộ subcommand vào `test_cli_contract_parity.py`.
- **RULE-4.18 [Pre-Brief/Pre-Plan Problem-Validity, Scale & Seam-Parity Gate — Chống Compliant Execution Bias]**:
  - Trước khi viết `Agent Brief` hoặc `implementation_plan.md`, BẮT BUỘC thẩm định: nếu áp hạ tầng nặng (RRF `#511`) lên tập nhỏ (`catalog.yaml` $N=76$ skills, `2ms`), xung đột `ADR-0040`/`ADR-0057` (`#512`, `#514`), trùng lặp Seams/lệch biên Hub (`#522`, `#523`), hoặc đã giải quyết ở lát cắt trước (`IDOP` `#10`–`#12`) $\rightarrow$ đóng `not_planned`/`completed` (Mục 42 history).
- **RULE-4.19 [Liveness-Aware Grok Watchdog, Multi-Turn Resume Telemetry & Degraded-Reasoning Gate]**:
  - Watchdog (`_peer_watchdog.py` — `inspect_session_liveness`) đọc `events.jsonl` (cấp grace `+45s` khi `streaming_text`/`streaming_reasoning`, fail-fast `90s` tại `mcp_init_completed:`, cấm ngắt `waiting_for_model`). Telemetry `--resume` lấy `turns[-1]`; `reasoning_tokens == 0` trên `high`/`xhigh` bơm `COND-DEGRADED-REASONING` (`blocking=True`) vào `synthesize_verdicts()` (Mục 43 history).

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
- *(Xem RULE-5.1..5.5 tại archive/session_learnings_history.md)*
- **RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines]**:
  - Structured output tắt thinking mode (`chat_template_kwargs: {"enable_thinking": False}`) hoặc dự phòng `max_tokens`; phân tầng `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Production Mounting & Dual Parser Separation]**:
  - DGX Spark Blackwell mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; tách `--reasoning-parser` và `--tool-call-parser`.
- **RULE-5.10 [Layer Anchoring Invariant: vLLM Backend vs Gateway Routing]**:
  - `fallbacks:` trong `litellm_config.yaml` chỉ nhận `model_name` tĩnh, CẤM nhúng `qwen-local-primary (enable_thinking=true)`. Tác vụ suy luận fallback về `local-coder` (`enable_thinking: true`) thay vì `rag-core`.
- **RULE-5.11 [GitHub Classic Projects GraphQL Deprecation & Project V2 Field Discovery]**:
  - `gh issue view <id>` (thiếu `--json`) lỗi exit 1 do `projectCards` bị gỡ; BẮT BUỘC truyền `--json ...` hoặc `gh api`. Khi chạy `gh project item-edit`, truy vấn `gh project field-list <num> --owner <owner> --format json` để lấy `PVTSSF_...` Field ID (Mục 42 history).
