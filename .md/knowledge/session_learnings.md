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
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051] tại Mục 23, 27; RULE-1.6, 1.8, 1.9, 1.15, 1.16 Mục 24-25, 33-34 của archive/session_learnings_history.md)*
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - Tái sử dụng Package Seams / Master Skills là KISS bậc 1; CẤM script chắp vá. Tra cứu qua `compile_catalog.py --query <kw>`. CẤM hoãn kiến trúc chuẩn sang Phase 2.
- **RULE-1.12 [ADR 0060 — Team Whitelist & Federated Architecture]**:
  - *Team Whitelist*: Unignore `!.agents/teams/` trong `.gitignore`. *Federated Hubs*: 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị qua CLI/REST/gRPC.
- **RULE-1.13 [Parameter Externalization & Declarative Config]**:
  - CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP. Dùng `choose_model()` / `ModelArchetype` và env vars (ngoại lệ: `# ccba:allow-raw-model`, `# ccba:allow-raw-ip`). Tách config theo OCP.
- **RULE-1.14 [ADR 0062 — Declarative Sync Registry & Fail-Closed Gate]**:
  - `assess_catalog_freshness` chặn `--apply` (exit 1) khi `catalog.yaml` stale (`--allow-stale-catalog` ghi audit log). Bindings tại `catalog_base.yaml`; `spoke_bootstrap.py` phân giải theo Kahn's topo sort.
- **RULE-1.18 [ADR 0066 — Skills Taxonomy & Scope Declaration]**:
  - `bundle: _core` chỉ chứa SDLC loop; `_software` chứa nghiệp vụ code. Frontmatter khai báo `scope: hub | spoke | universal`; linter chặn `command: /...` ở `_governance` thiếu `scope: hub` và đối soát GPI (COND-01).
- *(RULE-1.17, 1.19 tại Mục 34-35 của archive/session_learnings_history.md)*
- **RULE-1.20 [ADR 0061 — Posture Title, Parity Radar & Contract Inflation]**:
  - Dùng đúng `## 🏛️ Platform-Aware Architecture Posture` (0 số ADR trong header); CẤM token ADR trong posture không tạo ADR mới (`sync_hub_adr_matrix.py`). 16 Deep Seams nhận `package-bound`; 60 skills nhận `seam-exempt`.
- **RULE-1.21 [Spoke Graduation Supersession, SHA-8 Divergent Archive & Link Parity]**:
  - Khi `supersede_graduated_spoke_docs` (`graduation.py`) thu hồi bản nháp Spoke đã thành Hub ADR, nếu `archive/<name>.md` khác nội dung, lưu thêm `<stem>.local-<sha8>.md` trước khi ghi `GRADUATED_STUB_MARKER`. Khử link `file://` và tiền tố `.md/` dư trong `.md/INDEX.md`.
- **RULE-1.22 [Reasoning Tiering Parity & Anti-Silent-Degradation in Gateway Fallback]**:
  - Tác vụ suy luận (Reasoning/Review/Audit) BẮT BUỘC duy trì Class A; CẤM fallback về Class C (`ocr-tier4`, `ocr-fallback`). Khi cạn quota Class A, Gateway **Fail-Fast** (HTTP 503) thay vì hạ cấp âm thầm (Mục 38 history).
- **RULE-1.23 [ADR 0067 — 3-Tier One-Way Door Manifest & Backpressure Circuit-Breaker]**:
  - `classify_pr_door` (`door_policy.py`) phân loại PR thành `TWO_WAY_DOOR`, `PAVED_ROAD`, `ONE_WAY_DOOR` qua `ONE_WAY_DOOR_MANIFEST` (7 nhóm) và `compute_cumulative_streak` gom cấp `packages/<pkg>` ($K \ge 3$ PRs/72h hoặc $>200$ LOC $\to$ `ONE_WAY_DOOR`, lấy mẫu 10% `is_sampled_for_audit`). `evaluate_backpressure_queue` (`backpressure.py`) ngắt mạch khi $>5$ PRs hoặc $>24\text{h}$, và `validate_tradeoff_card` bắt buộc 3 trường (`Core Invariant`, `Invalidation Condition`, `Git Hunk Reference` $\le 30$ dòng) qua `ccba-harness door-triage` (Mục 40 history).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- *(RULE-2.1, 2.3, 2.4, 2.8, 2.10-2.12, 2.14, 2.16-2.18 tại Mục 24-25, 27-28, 30, 32 của archive/session_learnings_history.md)*
- **RULE-2.5 [ADR 0058 — SSOT Archetype Routing, Disjoint Hierarchy & 100% Skill Coverage]**:
  - Ánh xạ kỹ năng sang đề thi (`eval_*.json`) dùng `archetypes.py` (17 archetypes); archetype chuyên biệt (`platform_tooling`, `legal_tooling`, `visual_design`) đứng trước khái quát (`orchestration`, `legal`, `visual`); 100% skills map chuẩn, cấm `None`.
- **RULE-2.9 [Test Fixture Isolation, Live Lock & Hub Decoupling]**:
  - Test fixtures (`conftest.py`) BẮT BUỘC xóa `CCBA_HUB_PATH`, `HUB_PATH` và mock triệt để lock vật lý (`is_kernel_runner_locked`, `check_daemon_lock` $\rightarrow$ `False`). CẤM rò rỉ env var hoặc đọc lock thật.
- **RULE-2.15 [Atomic Knowledge Cataloging, Hermetic Scripts & Ruff Guard]**:
  - Tệp `.md` mới trong `.md/knowledge/` BẮT BUỘC biên mục vào `index.md` ngay commit tạo tệp chống Orphan Notes. Shell script dùng `cat << 'EOF'`. Callable động dùng `hasattr(obj, "m") and callable(obj.m)`.
- *(RULE-2.13, 2.19 tại Mục 35 của archive/session_learnings_history.md)*
- **RULE-2.20 [Static Module Size Budget & Template Sanitizer Precision]**:
  - *Module Budget*: CẤM monofile $> 500$ LOC và CLI post-parse body $> 40$ LOC (quarantine có hạn). Scanner quét secret BẮT BUỘC phân định f-string cú pháp biến (`^\{[A-Za-z_][A-Za-z0-9_.]*[:,\s]`) với JSON literal `{"`.

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
- *(RULE-4.4-4.7, 4.10, 4.11, 4.13, 4.14 tại Mục 25, 28, 29, 30 của archive/session_learnings_history.md)*
- **RULE-4.8 [Review Danger Triage, Read-Only Advisory & 10 Bugbot Invariants]**:
  - AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic. Core files $\rightarrow$ HARD human gate (`door-triage`); Docs qua Fast-Path.
- **RULE-4.12 [Structural File Addition & Architecture Drift Pre-Commit Invariant]**:
  - Thêm/xóa/đổi tên Level-1 files BẮT BUỘC chạy `python scripts/update_arch_stats.py` trước khi commit để đồng bộ marker `README.md` và `PLATFORM.md`.
- **RULE-4.15 [Multi-Turn Review Budgeting, Resilient Parsing & POSIX Atomicity]**:
  - Turn budget tools review $\ge 10-14$ turns. `PeerVerdictBlock` hỗ trợ `extra="ignore"`, Pydantic conditions coercion và session history fallback. `apply_anchor_patch` kiểm tra `is_file()`, rollback gom lỗi, và bảo tồn `stat.st_mode`.
- **RULE-4.16 [Two-Pass Peer Review Protocol & Atomic Micro-PR Slicing]**:
  - Pass 1 (`APPROVE_PLAN`) đóng băng thiết kế; Pass 2 (`APPROVE`) đối soát reflog (`xhigh` timeout $\ge 900$s). Phân rã 7-8 skills thành 4 micro-PRs, khóa cục bộ bằng bộ 3 lệnh (< 1s) trước khi chạy `verify-patch --preset ci`.
- **RULE-4.17 [Adversarial Rebuttal on `audit_direct` Claims, Tool-Starvation Defense & CLI Parity]**:
  - Khi `audit_direct` suy diễn sai thuộc tính hoặc đòi GitHub API khi CI đã có `fetch-depth: 0`, đối chiếu AST thực tế để tinh chỉnh theo KISS; ưu tiên `audit_direct --no-tools` khi plan đủ ngữ cảnh; đồng bộ subcommand mới vào `test_cli_contract_parity.py`.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)
- *(Xem RULE-5.1-5.5 tại archive/session_learnings_history.md)*
- **RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines]**:
  - Structured output BẮT BUỘC tắt thinking mode (`chat_template_kwargs: {"enable_thinking": False}`) hoặc dự phòng `max_tokens` vượt ngưỡng suy nghĩ; phân tầng `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Production Mounting & Dual Parser Separation]**:
  - DGX Spark Blackwell volume mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; cấu hình tách biệt `--reasoning-parser` và `--tool-call-parser`.
- **RULE-5.10 [Layer Anchoring Invariant: vLLM Backend vs Gateway Routing]**:
  - Tầng Gateway (`fallbacks:` trong `litellm_config.yaml`) chỉ nhận `model_name` tĩnh, CẤM nhúng cờ động `qwen-local-primary (enable_thinking=true)`. Tác vụ suy luận fallback về virtual deployment `local-coder` (`enable_thinking: true`) thay vì `rag-core`.
