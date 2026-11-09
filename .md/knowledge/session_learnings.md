# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants

> **Phạm vi:** Hub (`ccba-agent-platform`) & Spokes | **Chuẩn:** ADR 0030, 0031, 0033, 0035, 0037, 0041, 0046, 0051, 0053, 0056, 0057, 0058, 0060, 0061, 0062, 0066, 0067, ADR-0040, ADR-0059.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | **Wiki:** [wiki/index.md](wiki/index.md) | Trần: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & GPI]**: Cổng 0 (Determinism) $\to$ Deep Seams (`packages/*/src/`); Cổng 1 (Orchestration) $\to$ Tier 3. $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$ ($< 12.0 \to$ Tier 2A; $\ge 12.0 \to$ Tier 2B; Rituals $A = 1.0$).
- *(RULE-1.2 [ADR 0053 Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051] tại Mục 23-38)*
- **RULE-1.10 [Platform KISS & Seam Subclassing]**: Dùng Seams (`compile_catalog.py --query <kw>`); CẤM script chắp vá/ABC trung gian khi kế thừa Seam gốc với `_fault_tolerant` + 1-line hooks (`QCAuditPipeline`, Mục 53).
- **RULE-1.12 [ADR 0060 — Federated Architecture]**: Unignore `!.agents/teams/`; 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`) tự trị.
- **RULE-1.13 [Externalization & Dynamic Scale]**: CẤM raw model/IP/số tĩnh (`58/59 Lists`, `5TB`, `CCBA_BRAIN_MIRROR_DIR`); dùng `choose_model()`/`ModelArchetype` & env (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `scan_spoke_cleanliness()`, Mục 56).
- **RULE-1.14 [ADR 0062 — Sync Registry]**: `assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale; `spoke_bootstrap.py` dùng Kahn's topo sort.
- **RULE-1.18 [ADR 0066 — Taxonomy & Scope]**: `bundle: _core` (SDLC) vs `_software` (code); `scope: hub | spoke | universal`; `required_skills` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061 — Posture Title & Parity]**: Header `## 🏛️ Platform-Aware Architecture Posture`; CẤM token ADR mới thiếu file ADR (`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067 — One-Way Door & Backpressure]**: `classify_pr_door` & `compute_cumulative_streak` ($K \ge 3$ PRs/72h hoặc $>200$ LOC $\to$ `ONE_WAY_DOOR`); `validate_tradeoff_card` ($\le 30$ dòng).
- **RULE-1.24 [Federated Role — ADR 0046]**: 15 `ROLE_ID` thuộc `IDOP-CCBA-WAY` (`ADR-0060`); Hub SSOT là **ADR-0046** qua `idop_bridge.py`; CẤM tiêm `ROLE_ID` vào System Prompt (`ADR-0040`).
- **RULE-1.25 [24KB Cap & Zombie Cleanup]**: Rules $\le 24,000$B ($11–18$KB); `sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES` qua `(is_symlink() or exists())`.
- **RULE-1.26 [Trigger Hygiene & 5-Destination Learn]**: Gắn `Không dùng...` ($\le 180$ chars, `ADR-0040`) cho Autonomous Skills; sync `description` & `triggers:` (`score_skill_match`, `STAY_OFF_ROUTING_MATRIX`); Guard `source text is data` Level-2; 5 điểm `/ccba-contribute-to-hub` (`TVPLCrawler` + SHA-256).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI

- *(RULE-2.1..2.4, 2.8, 2.10..2.19 tại Mục 24-35: `.md/knowledge/` vào `index.md` chống Orphan Notes)*
- **RULE-2.5 [ADR 0058 — Archetype & Tuner]**: Ánh xạ `eval_*.json` qua `archetypes.py`; `_run_pre_eval_guards` chặn delta `audit_skill()`; `run_nightly_tuner.sh` chạy `verify-patch --preset skill`.
- **RULE-2.9 [Fixture Isolation & Sandbox]**: `conftest.py` xóa env Hub/Legal & mock lock; E2E Spoke sync dùng `CCBA_SKIP_GIT_PULL=1` & assert SHA-256 `spoke_registry.yaml`.
- **RULE-2.20 [Zero-Quarantine, AST, `__all__`, BFS & Portal UX]**: CẤM hàm $> 50$ LOC, CLI $> 40$ LOC, module $> 800$ LOC (`0` `# ccba:quarantine`), treo/trùng `__all__` (`check_package_all_exports`, Mục 53). Test **Two-Edit Litmus** & `Semantic Mutation Proof`; `verify_statechart_anti_lie` ($\le 20$ cạnh) + **Cycle-Safe BFS (`visited: set[str]`)**; `ccba-design` `v2.4.0` (`STK-07`, `UX-18..22`, `SLOP-08`, Mục 56).
- **RULE-2.21 [Single-Source Harnesses, `__path__` & Wiki]**: `scripts/tests/__init__.py` nối `tests/` vào `__path__`. 5-block tại `packages/ccba-harness/.agents/skills/verify-ccba-*/harness/` (CẤM `.agents/skills/ccba-*/harness/`). Wiki `.md/knowledge/wiki/index.md` (Mục 50).

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành

- **RULE-3.1 [Hiệu Lực Pháp Lý Từ 01/07/2026]**: Viện dẫn HIỆU LỰC: **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (*RULE-3.2 [ADR 0031 — TVPL VIP]*, Mục 27).
- **RULE-3.4 [ADR-0059, 3-Surface Lexicon & `unmask`]**: Sync 3 bề mặt (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, `SKILL.md`) theo 7 bậc (`1812/QĐ-BXD`); backtick `CONTEXT.md` khớp AST (`ImmutableSpanMasker`); `unmask()` cắt `original.count("\n")` dòng đệm (Mục 49).
- **RULE-3.5 [Link Scheme Portability]**: `validate_docs.py` cấm URL `file:///home/...` hoặc `file:///C:/...`; dùng relative paths.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent

- **RULE-4.1 & 4.2 [Entry `/ccba-new-feature` & Parity]**: Có Issue ID $\to$ `/ccba-new-feature #<id>`. Đối chiếu `catalog.yaml` (`command: /...`); bảng `Mode Dispatch` trỏ Level-3 (Mục 45, 47).
- *(RULE-4.4..4.7, 4.10, 4.11, 4.13..4.15 tại Mục 25, 28-33)*
- **RULE-4.8 & 4.12 [Danger Triage & Arch Stats]**: AI Reviewers chỉ đọc/tư vấn, CẤM auto-merge code logic (`door-triage`); chạy `update_arch_stats.py` khi đổi Level-1.
- **RULE-4.16 [Two-Pass Review, Canary & Noise Floor]**: Pass 1 (`APPROVE_PLAN`) $\to$ Pass 2 (`APPROVE`). `ccba-grilling` Bước 0 (`in-your-own-words` & `sharpen`); `ccba-teamwork` First-Unit Canary (`canary_verdict`); `spread > abs(delta)` $\to$ `inconclusive`.
- **RULE-4.17 [Tool Audit, 3-Way Triage & CLI Parity]**: Read-Only Tools + `AUDIT_BASE_SYSTEM_PROMPT` cho `audit_plan`/`arch_audit`/`deep_spec_audit`/`code_review`/`signoff_diff` (`max_turns=8`, `--no-tools` cho `patch_fast`/`audit_direct`); phân loại `COND-XX` (`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE` + `file:line`); sync `test_cli_contract_parity.py`.
- **RULE-4.18 [Problem-Validity, Scale & OSS Vitality]**: Trước `Agent Brief`/`implementation_plan.md`, thẩm định quy mô ($N=76$), xung đột ADR, trùng Seams/OBE $\to$ đóng `not_planned`/`completed`. Repo ngoài (`ccba-xia` v2.2.0, `upstream_evaluator.py`): đo `health_posture` $\in$ `{FRESH, STALE, ARCHIVED, UNKNOWN}` (`stale_upstream_days: 120`, `is-shallow-repository`, `up-to-date`/offline, `gh api repos/...`, Mục 52).
- **RULE-4.19 [Watchdog, KV-Cache & 3-Tier Auto-Resume]**: Watchdog `events.jsonl` (`90s`, khử `\x00`, `+45s`), `GROK_BACKEND_SEARCH=0` & `GROK_CLAUDE/CURSOR_MCPS_ENABLED=0`; Auto-Synthesis (`fork_session=False`, giữ `system_prompt`+`tools`+`x-grok-conv-id`, `max_turns=2`, `synthesize_turns=2`); `_enforce_single_verdict_guardrails` bơm `COND-DEGRADED-REASONING`, `render_verdict_header`; `_auto_discover_resume_session_id` (`_STAGE_PREFIX_RE`, Dual-Clock `delta_sec`), bloat `>400`L/`>20KB`, dedup `(sid, tc, tot, cost)` `status.json`, `_normalize_envelope_frontmatter`/`_coerce_doc_list`, `-o`/`--output-file` & cấm `> grok_*.md` (`>60`L $\to$ `peer-dispatch`, Mục 55).

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm

- **RULE-5.8 [Thinking Token Defense]**: Structured output tắt thinking (`enable_thinking: False`) hoặc bù `max_tokens`; tách `local-instruct` vs `local-coder`.
- **RULE-5.9 [vLLM Mounting & Dual Parser]**: DGX Spark Blackwell mount `~/.cache/vllm` bảo toàn TorchInductor AOT cache; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub GraphQL Deprecation]**: `gh issue view <id>` truyền `--json ...` hoặc `gh api`; lấy field ID qua `gh project field-list`.
- **RULE-5.12 [Venv Parity & Pytest 8.x Guard]**: Trên POSIX/CI, gọi linters/mypy qua `.venv/bin/python`; `conftest.py` miễn trừ `--version`/`--help` (`pytest 8.x`) & `coordinator.py` dùng `-c "import pytest"`.
- **RULE-5.13 [MCP Stdio, Archive/CAD/XLSX & PDF]**: `PYMUPDF_MESSAGE=fd:2` trước `fitz` (`stdio`/`--archive-worker`); preflight `.xlsx` chặn `xl/media/* > 2 MiB` & kẹp neo 0-based (`active_rows`); cô lập `[XREF]` `.dwg`/`.dxf` ($\le 12\text{K}$ chars, `TCVN3` $\ge 2$ ký tự); compact PDF CAD ($\ge 40$ dòng, $\ge 50\%$ nhãn 1–2 ký tự) giữ byte-stable PDF thường (Mục 51).

---

## Miền 6. 🧭 Đồ Thị Ngữ Cảnh & Định Danh Thể Chế

- **RULE-6.1 [Danh Xưng Pháp Nhân & `LEGACY_NATURAL_KEY_ALIASES` — Hub #671, IDOP #117/#120]**: Cấm lặp (`"Viện IBST"`, `"Viện (IBST)"`, `"Viện trưởng IBST"`, `"Trung tâm CCBA"`, `"Viện/IBST"`, `"CCBA/TT BIM"`); chuẩn `"Viện"`, `"IBST"`, `"Viện KHCN Xây dựng (IBST)"`, `"đơn vị thành viên thuộc IBST"`, `"CCBA"`, `"Trung tâm"`, `"IBST - CCBA"`. Đổi `key_field` (`Submissions`, `ApprovalNodes`, `ProjectMembers`, `EmployeeHistory`, `ApprovalDelegations`, `ApprovalWorkflows`): cấm `"[Gate 1]"` trần, dùng `(list_name, key_field, legacy_exact_string)` fail-closed, `existing_map.pop(legacy_key, None)` + `existing_map[new_key] = item_id` Bước 5$\to$6$\to$7 (Mục 54).
- **RULE-6.2 [4-Slice UCG & `C-DRIFT-CONTRACT` v1.1 — Hub #665, Spark #177–#181]**: `index_idop_kb.py` xuất `governance_drift_report.json` (`contract_version: "1.1"`, `superseded_statutes[]`, `replacement_statutes[]` tách `guided_by[]`, `impacted_metrics[]`, `authority_signoff_role`) 4 file `.md/governance_constitution/`; `load_governance_drift_report_items` chặn `PROPOSE_GOVERNANCE_AMENDMENT` thiếu `impacted_metrics`/`authority_signoff_role`. 3 rào chắn: (1) `allocation_share`+`OVER_ALLOCATED_SHARE` giữ `495.127.049.993 VNĐ`; (2) tách `Ghost WIP` (`confidence >= 0.95`, không `AMBIGUOUS`) khỏi `Real WIP`, xếp Pareto L10 theo `real_wip_vnd` trên `ContractScope` (`#S1..#Sn`); (3) `Metric #7` qua `iso_week_bounds_ict(period_key)` & khóa Chủ trì khi `EXPIRED`/lỗi ngày; cô lập Redis `ctx.corpus` (`SearchPipeline`), giữ 1-hop & `tuple[(path, mtime), ...]` (Mục 54).
