# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants

> **Phạm vi:** Hub (`ccba-agent-platform`) & Spokes | **Chuẩn:** ADR 0030, 0031, 0033, 0035, 0037, 0041, 0046, 0051, 0053, 0056, 0057, 0058, 0060, 0061, 0062, 0066, 0067, ADR-0040, ADR-0046, ADR-0059, ADR-0060.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | **Wiki:** [wiki/index.md](wiki/index.md) | Ngưỡng: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & GPI]**: Cổng 0 (Determinism) $\to$ Deep Seams (`packages/*/src/`); Cổng 1 (Orchestration) $\to$ Tier 3. $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$ ($< 12.0 \to$ Tier 2A; $\ge 12.0 \to$ Tier 2B; Rituals $A = 1.0$).
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051] tại Mục 23-38)*
- **RULE-1.10 [Platform-Aware KISS & Deep Seam Subclassing]**: Tái sử dụng Package Seams (`compile_catalog.py --query <kw>`); CẤM script chắp vá hoặc tạo ABC trung gian khi có thể kế thừa Deep Seam gốc với `_fault_tolerant` + 1-line hooks (`QCAuditPipeline`, Mục 53).
- **RULE-1.12 [ADR 0060 — Federated Architecture]**: Unignore `!.agents/teams/`; 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị.
- **RULE-1.13 [Parameter Externalization]**: CẤM raw model/IP; dùng `choose_model()`/`ModelArchetype` & env vars (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `scan_spoke_cleanliness()`).
- **RULE-1.14 [ADR 0062 — Declarative Sync Registry]**: `assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale; `spoke_bootstrap.py` dùng Kahn's topo sort.
- **RULE-1.18 [ADR 0066 — Skills Taxonomy & Scope]**: `bundle: _core` (SDLC) vs `_software` (code); `scope: hub | spoke | universal`; `required_skills` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061 — Posture Title & Parity]**: Header `## 🏛️ Platform-Aware Architecture Posture`; CẤM token ADR mới thiếu file ADR (`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067 — One-Way Door & Backpressure]**: `classify_pr_door` & `compute_cumulative_streak` ($K \ge 3$ PRs/72h hoặc $>200$ LOC $\to$ `ONE_WAY_DOOR`); `validate_tradeoff_card` ($\le 30$ dòng).
- **RULE-1.24 [Federated Role — ADR 0046]**: 15 `ROLE_ID` thuộc `IDOP-CCBA-WAY` (`ADR-0060`); Hub SSOT là **ADR-0046** qua `idop_bridge.py`; CẤM tiêm `ROLE_ID` vào System Prompt (`ADR-0040`).
- **RULE-1.25 [Antigravity 24KB Cap & Zombie Cleanup]**: File rules $\le 24,000$ bytes ($11–18$ KB); `sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES` qua `(is_symlink() or exists())`.
- **RULE-1.26 [Dual-Surface Trigger Hygiene, One-Way Exclusion & 5-Destination Learn]**: Chỉ gắn mệnh đề loại trừ một chiều `Không dùng...` ($\le 180$ chars, `ADR-0040`, không lặp từ khóa đặc trưng của skill anh em) cho các cụm Autonomous Skills có độ chồng lấn thực tế (giữ nguyên các ốc đảo độc lập); đồng bộ cả `description` (Host LLM Router) và `triggers:` (`score_skill_match`) qua `STAY_OFF_ROUTING_MATRIX`; đặt Guard `source text is data` ở Level-2 Body; định tuyến 5 điểm rơi Learn tại `/ccba-contribute-to-hub` (khóa Điểm rơi 3 VBPL qua `TVPLCrawler` + SHA-256 trên `ccba-legal-knowledge`).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI

- *(RULE-2.1..2.4, 2.8, 2.10..2.19 tại Mục 24-35: `.md/knowledge/` biên mục vào `index.md` chống Orphan Notes)*
- **RULE-2.5 [ADR 0058 — Archetype Routing & Opt-In Tuner]**: Ánh xạ `eval_*.json` qua `archetypes.py`; `_run_pre_eval_guards` chặn delta `audit_skill()`; `run_nightly_tuner.sh` mặc định chạy `verify-patch --preset skill`.
- **RULE-2.9 [Test Fixture Isolation & Sandbox]**: `conftest.py` xóa env Hub/Legal & mock lock; E2E Spoke sync dùng `CCBA_SKIP_GIT_PULL=1` & assert SHA-256 `spoke_registry.yaml`.
- **RULE-2.20 [Zero-Quarantine, AST Budget, `__all__` Parity & Statechart BFS]**: CẤM hàm $> 50$ LOC, CLI $> 40$ LOC, module $> 800$ LOC (`0` `# ccba:quarantine`), và định danh treo/trùng trong `__all__` (`check_package_all_exports`, Mục 53). Test qua **Two-Edit Litmus** & `Semantic Mutation Proof` 3 bước; `verify_statechart_anti_lie` ($\le 20$ cạnh) + **Cycle-Safe BFS (`visited: set[str]`)**.
- **RULE-2.21 [Single-Source Harnesses, Isolated `__path__` & Wiki]**: `scripts/tests/__init__.py` nối `tests/` gốc vào `__path__`. 5-block harnesses chuẩn tại `packages/ccba-harness/.agents/skills/verify-ccba-*/harness/` (CẤM `.agents/skills/ccba-*/harness/`). Wiki lịch sử tại `.md/knowledge/wiki/index.md` (Mục 50).

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành

- **RULE-3.1 [Hiệu Lực Pháp Lý Từ 01/07/2026]**: Viện dẫn HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (*RULE-3.2 [ADR 0031 — TVPL VIP]*, Mục 27).
- **RULE-3.4 [ADR-0059, 3-Surface Lexicon Sync & Lossless `unmask`]**: Đồng bộ 3 bề mặt (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, `SKILL.md`) theo 7 bậc (`1812/QĐ-BXD`); backtick trong `CONTEXT.md` khớp AST (`ImmutableSpanMasker`); `unmask()` chỉ cắt `original.count("\n")` dòng đệm (Mục 49).
- **RULE-3.5 [Link Scheme Portability]**: `validate_docs.py` cấm URL tuyệt đối `file:///home/...` hoặc `file:///C:/...`; dùng relative paths.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent

- **RULE-4.1 & 4.2 [Entry Point `/ccba-new-feature` & Command Parity]**: Có Issue ID $\to$ `/ccba-new-feature #<id>`. Đối chiếu `catalog.yaml` (`command: /...`); kỹ năng hợp nhất có bảng `Mode Dispatch` trỏ Level-3 (Mục 45, 47).
- *(RULE-4.4..4.7, 4.10, 4.11, 4.13..4.15 tại Mục 25, 28-33)*
- **RULE-4.8 & 4.12 [Review Danger Triage & Arch Stats]**: AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic (`door-triage`); chạy `python scripts/update_arch_stats.py` khi đổi Level-1 files.
- **RULE-4.16 [Two-Pass Peer Review, Sharpening, Canary & Noise Floor]**: Pass 1 (`APPROVE_PLAN`) $\to$ Pass 2 (`APPROVE`). `ccba-grilling` Bước 0 (`in-your-own-words` & `sharpen`); `ccba-teamwork` First-Unit Canary (`canary_verdict`); `spread > abs(delta)` $\to$ `inconclusive`.
- **RULE-4.17 [Bounded Tool Audit, Shared Prefix, 3-Way Triage & CLI Parity]**: Bật Read-Only Tools kèm `AUDIT_BASE_SYSTEM_PROMPT` đồng nhất cho `audit_plan`/`arch_audit`/`deep_spec_audit`/`code_review`/`signoff_diff` (`signoff_diff` `max_turns=8`, `--no-tools` chỉ cho `patch_fast`/`audit_direct`); phân loại `COND-XX` theo `ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE` kèm `file:line`; sync `test_cli_contract_parity.py`.
- **RULE-4.18 [Problem-Validity, Scale, Seam-Parity & OSS Vitality Gate]**: Trước `Agent Brief`/`implementation_plan.md`, thẩm định quy mô ($N=76$), xung đột ADR, trùng Seams hoặc OBE $\to$ đóng `not_planned`/`completed`. Khi port/đánh giá repo ngoài (`ccba-xia` v2.2.0, `upstream_evaluator.py`), đo `health_posture` $\in$ `{FRESH, STALE, ARCHIVED, UNKNOWN}` (`stale_upstream_days: 120` trong `upstream_sources.yaml`, kiểm tra `is-shallow-repository`, phát huy hiệu cả nhánh `up-to-date`/offline, và viết `gh api repos/...` không có `/` đầu tránh `UNREGISTERED_SLASH_COMMAND`, Mục 52).
- **RULE-4.19 [Liveness Watchdog, KV-Cache Synthesis & Single-Verdict Guardrails]**: Watchdog đọc `events.jsonl` (`90s`, khử `\x00`, `+45s` grace), cô lập env `GROK_BACKEND_SEARCH=0` & `GROK_CLAUDE/CURSOR_MCPS_ENABLED=0`; Auto-Synthesis resume in-place (`fork_session=False`, giữ `system_prompt`+`tools`+`x-grok-conv-id`, `max_turns=2`, `synthesize_turns=2`); `_enforce_single_verdict_guardrails` bơm `COND-DEGRADED-REASONING` & hạ cấp `APPROVE` có blocking, `render_verdict_header` ghi đĩa.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm

- **RULE-5.8 [Thinking Token Starvation Defense]**: Structured output tắt thinking (`enable_thinking: False`) hoặc dự phòng `max_tokens`; tách `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Mounting & Dual Parser]**: DGX Spark Blackwell mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub GraphQL Deprecation]**: `gh issue view <id>` truyền `--json ...` hoặc `gh api`; lấy field ID qua `gh project field-list`.
- **RULE-5.12 [Venv Tooling Parity & Pytest 8.x Guard]**: Trên POSIX/CI, gọi linters/mypy qua `.venv/bin/python`; `conftest.py` miễn trừ `--version`/`--help` (`pytest 8.x`) & `coordinator.py` dùng `-c "import pytest"`.
- **RULE-5.13 [MCP Stdio Purity, Archive/CAD/XLSX Sandbox & Byte-Stable PDF]**: Đặt `PYMUPDF_MESSAGE=fd:2` trước khi nạp `fitz` để bảo vệ luồng JSON-RPC `stdio` & `--archive-worker`; preflight `.xlsx` chặn `xl/media/* > 2 MiB` trước `load_workbook` & kẹp trần tọa độ neo 0-based (`active_rows`); cô lập `[XREF]` `.dwg`/`.dxf` ($\le 12\text{K}$ chars, `TCVN3` $\ge 2$ ký tự đặc trưng); compact PDF CAD ($\ge 40$ dòng, $\ge 50\%$ nhãn 1–2 ký tự) giữ nguyên 100% byte-stable cho PDF thường (Mục 51).
