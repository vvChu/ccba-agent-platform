# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants

> **Phạm vi:** Hub (`ccba-agent-platform`) & Spokes | **Chuẩn:** ADR 0030, 0031, 0035, 0041, 0057, 0058.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Thuần giải thuật/IO $\to$ Deep Seams (`packages/*/src/`); `SKILL.md` không code trần.
  - *Cổng 1 (Orchestration)*: Đa luồng/StateGraph/HITL $\to$ Tier 3 Composite Orchestrator (bỏ qua GPI).
  - *Chỉ số GPI*: $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$. $< 12.0 \to$ Tier 2A; $\ge 12.0 \to$ Tier 2B. Rituals: $A = 1.0$.
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051], RULE-1.6..1.9, 1.15..1.17, 1.19, 1.21..1.22 tại Mục 23-27, 33-38: Class A Fail-Fast)*
- **RULE-1.10 [Platform-Aware KISS & Anti-Phantom Deferral]**:
  - Tái sử dụng Package Seams/Master Skills là KISS bậc 1 (`compile_catalog.py --query <kw>`); CẤM script chắp vá hoặc hoãn Phase 2.
- **RULE-1.12 [ADR 0060 — Team Whitelist & Federated Architecture]**:
  - Unignore `!.agents/teams/` trong `.gitignore`. 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị qua CLI/REST/gRPC.
- **RULE-1.13 [Parameter Externalization & Active Cleanliness Guardrails]**:
  - CẤM nhúng raw model (`gemini-*`, `gpt-*`) hoặc IP; dùng `choose_model()`/`ModelArchetype` & env vars (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`). `check_spoke_cleanliness.py` nối AST & docstring checkers vào `scan_spoke_cleanliness()` (Mục 41).
- **RULE-1.14 [ADR 0062 — Declarative Sync Registry & Fail-Closed Gate]**:
  - `assess_catalog_freshness` chặn `--apply` (exit 1) khi `catalog.yaml` stale (`--allow-stale-catalog` ghi audit log). Bindings tại `catalog_base.yaml`; `spoke_bootstrap.py` dùng Kahn's topo sort.
- **RULE-1.18 [ADR 0066 — Skills Taxonomy, Scope & Resource Skill-Ref Parity]**:
  - `bundle: _core` chỉ chứa SDLC; `_software` chứa code. Frontmatter có `scope: hub | spoke | universal`; linter chặn `command: /...` ở `_governance` thiếu `scope: hub` & đối soát GPI. `required_skills` trong `resources/*.yaml` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061 — Posture Title, Parity Radar & Contract Inflation]**:
  - Dùng `## 🏛️ Platform-Aware Architecture Posture` (0 số ADR ở header); CẤM token ADR không tạo ADR mới (`sync_hub_adr_matrix.py`). 16 Deep Seams `package-bound`; 60 skills `seam-exempt`.
- **RULE-1.23 [ADR 0067 — 3-Tier One-Way Door Manifest & Backpressure]**:
  - `classify_pr_door` & `compute_cumulative_streak` ($K \ge 3$ PRs/72h hoặc $>200$ LOC $\to$ `ONE_WAY_DOOR`). `evaluate_backpressure_queue` ngắt khi $>5$ PRs/$>24\text{h}$; `validate_tradeoff_card` bắt buộc Tradeoff Card ($\le 30$ dòng, Mục 40).
- **RULE-1.24 [Federated Role & ERP Boundary — ADR 0046 vs IDOP-CCBA-WAY]**:
  - 15 `ROLE_ID` & ERP 5 pha thuộc `IDOP-CCBA-WAY` (`ADR-0060`). Hub SSOT là **ADR-0046** (`seat_role` + 5 cấp QC), qua `idop_bridge.py`; CẤM Dual-SSOT/tiêm `ROLE_ID` vào System Prompt (`ADR-0040`, Mục 42).
- **RULE-1.25 [Antigravity 24KB Rule Hard Cap, Decomposition & Fleet Zombie Cleanup Invariant]**:
  - File rules bắt buộc $\le 24,000$ bytes (mục tiêu $11–18$ KB) chống silent truncation (`rules.go:544`). Khi phân rã tệp Hub, `CORE_LAYER2_RULES` cập nhật tệp mới; `sync_layer2_rules` dọn `LEGACY_MONOLITHIC_RULES` tại Spoke (`.agents/rules/`) chống Zombie Rule: dùng `(is_symlink() or exists())` xử lý broken symlinks và assert sau `unlink()` (`CLEANUP_FAILED` nếu còn file). `normalize_spoke_agents_links` định tuyến đa mục tiêu theo section anchor (`#...`) sang tệp con tương ứng (PR #553, #556).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI

- *(RULE-2.1..2.4, 2.8, 2.10..2.19 tại Mục 24-35: `.md/knowledge/` biên mục vào `index.md` chống Orphan Notes; `cat << 'EOF'`)*
- **RULE-2.5 [ADR 0058 — Archetype Routing, Pre-Eval Hygiene Delta & Opt-In Tuner]**:
  - Ánh xạ `eval_*.json` qua `archetypes.py` (17 archetypes); chuyên biệt trước khái quát. `_run_pre_eval_guards` chặn delta `audit_skill()`; `run_nightly_tuner.sh` mặc định chạy `verify-patch --preset skill` (0 token), khóa tuner sau `--enable-tuner`/`--skill` (Mục 47).
- **RULE-2.9 [Test Fixture Isolation, Subpackage Pytest INI Parity & Zero Hub Pollution Sandbox]**:
  - `conftest.py` xóa `CCBA_HUB_PATH`, `HUB_PATH`, `CCBA_LEGAL_KNOWLEDGE_PATH`, `CCBA_LEGAL_CORPUS_PATH` & mock lock (`is_kernel_runner_locked`, `check_daemon_lock` $\to$ `False`). Subpackage `[tool.pytest.ini_options]` sync `pythonpath` & `markers`, cấm `--cov` cứng. Harness/E2E test Spoke sync bắt buộc cô lập Hub: `CCBA_SKIP_GIT_PULL=1`, `CCBA_HUB_PATH`, `--sync-item platform-loader`, và kiểm tra SHA-256 `spoke_registry.yaml` bất biến (Mục 44, PR #556).
- **RULE-2.20 [Zero-Quarantine, AST Budget, Two-Edit Litmus & Mutation Proof]**:
  - CẤM hàm $> 50$ LOC, CLI post-parse $> 40$ LOC, module $> 800$ LOC (`0` `# ccba:quarantine`). Test mới qua **Two-Edit Litmus** (*Break behavior* $\to$ FAIL; *Change internals* $\to$ PASS); `Semantic Mutation Proof` hoàn nguyên 3 bước (`git diff --quiet` $\to$ fail log $\to$ `git checkout --`, Mục 44, 47).

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - Viện dẫn HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (Mục 27).
- **RULE-3.4 [RAG Normative Spanning & ADR-0059 Test Isolation]**:
  - `clauses.json` span bao trọn toàn văn quy phạm; cấm span 1 dòng chỉ trỏ `<a>`. Tests dùng `tmp_path / "legal_registry.yaml"`.
- **RULE-3.5 [Documentation Link Scheme Portability Invariant]**:
  - `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`; dùng relative paths.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent

- **RULE-4.1 & 4.2 [Entry Point `/ccba-new-feature`, Slash Command Parity & Multi-Mode Dispatch]**:
  - Có Issue ID $\to$ `/ccba-new-feature #<id>` (8 bước). Đối chiếu `catalog.yaml` (`command: /...`) trước đề xuất `/command` (cấm `/ccba-verify`). Kỹ năng hợp nhất (`/ccba-ask`, `/ccba-contribute-to-hub`, `/ccba-issue-to-hub`) có bảng `Mode Dispatch` trong `SKILL.md` trỏ Level-3 (Mục 45, 47).
- *(RULE-4.4..4.7, 4.10, 4.11, 4.13..4.15 tại Mục 25, 28-33: Turn budget $\ge 10-14$ turns; `PeerVerdictBlock` `extra="ignore"`; `apply_anchor_patch` kiểm tra `is_file()` & `stat.st_mode`)*
- **RULE-4.8 & 4.12 [Review Danger Triage & Architecture Drift Pre-Commit]**:
  - AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic (`door-triage`). Thêm/xóa/đổi tên Level-1 files chạy `python scripts/update_arch_stats.py` sync `README.md` & `PLATFORM.md`.
- **RULE-4.16 [Two-Pass Peer Review, Pre-Grill Sharpening & Decision-Decidable Handoff]**:
  - Pass 1 (`APPROVE_PLAN`) đóng băng thiết kế; Pass 2 (`APPROVE`) đối soát reflog (timeout $\ge 900$s). `ccba-grilling` có Bước 0 (`in-your-own-words` & `sharpen` 1 *outside check*); `ccba-handoff` xếp `riskiest first` (5 thành tố) & Mermaid $\le 6$ khối (Mục 47).
- **RULE-4.17 [Adversarial Rebuttal on `audit_direct`, Tool-Starvation Defense & CLI Parity]**:
  - Khi `audit_direct` suy diễn sai/đòi GitHub API khi CI có `fetch-depth: 0`, đối chiếu AST theo KISS; ưu tiên `audit_direct --no-tools`; sync subcommand vào `test_cli_contract_parity.py`.
- **RULE-4.18 [Pre-Brief/Pre-Plan Problem-Validity, Scale & Seam-Parity Gate]**:
  - Trước `Agent Brief`/`implementation_plan.md`, thẩm định: hạ tầng nặng trên tập nhỏ ($N=76$), xung đột ADR (`#512`, `#514`), trùng Seams/lệch biên Hub (`#522`, `#523`), hoặc OBE $\to$ đóng `not_planned`/`completed` (Mục 42).
- **RULE-4.19 [Liveness Watchdog, Single-Verdict Guardrails & Unconditional Re-Render]**:
  - Watchdog đọc `events.jsonl` (grace `+45s`, fail-fast `90s`). `_enforce_single_verdict_guardrails` bơm `COND-DEGRADED-REASONING` & hạ cấp `APPROVE` có blocking/risk $\ge 4$ ở đơn luồng, `render_verdict_header` ghi đĩa (`COND-RE-RENDER-ON-MUTATION`, Mục 43, 46).

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm
- *(Xem RULE-5.1..5.5, 5.10 [vLLM Routing Fallback] tại Mục 23, 41)*
- **RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines]**:
  - Structured output tắt thinking (`chat_template_kwargs: {"enable_thinking": False}`) hoặc dự phòng `max_tokens`; tách `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Production Mounting & Dual Parser Separation]**:
  - DGX Spark Blackwell mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub Classic Projects GraphQL Deprecation & Project V2 Field Discovery]**:
  - `gh issue view <id>` (thiếu `--json`) lỗi exit 1 do `projectCards`; truyền `--json ...` hoặc `gh api`. Khi `gh project item-edit`, lấy field ID qua `gh project field-list` (Mục 42).
- **RULE-5.12 [Venv Tooling Execution Parity & Non-Test Module Verify-Patch Pattern]**:
  - Trên POSIX/CI, linters/mypy bắt buộc gọi qua `.venv/bin/python` thay vì system python; với module không chứa test case (nhánh core/sync), `verify-patch -c` chỉ định rõ linter + test suite mục tiêu thay cho `--preset code` (tránh exit code 5 của pytest khi 0 test collected).
