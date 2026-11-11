# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants

> **Phạm vi:** Hub & Spokes | **Chuẩn:** ADR 0030, 0031, 0033, 0035, 0037, 0041, 0046, 0051, 0053, 0056..0058, 0060..0062, 0066, 0067, ADR-0040, ADR-0059.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | **Wiki:** [wiki/index.md](wiki/index.md) | Trần: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams

- **RULE-1.1 [ADR 0057]**: Gate 0$\to$Seams (`packages/*/src/`); Gate 1$\to$Tier 3. $\mathbf{GPI}=2.5S+2.0K+2.0A-1.5P$ ($<12\to$2A; $\ge 12\to$2B; Rituals $A=1.0$).
- *([DEPRECATED] Lưu trữ tại Mục 23-38: RULE-1.2 [ADR 0053 — Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051], RULE-1.6 [ADR 0044])*
- **RULE-1.7 [ADR 0057/0058 — GPI JSON & Hygiene]**: `evaluate-gpi --json` xuất `ArchitectureTier.value`, `allow_standalone_skill`, `preserved_by_hysteresis`; `--existing-tier tier-2b` chỉ khi sẵn `tier: kernel` & bỏ qua `--s..--p` khi đủ 4 khóa; `audit_skills_hygiene.py` quét văn xuôi; Hub chạy 3 writer (`compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, Mục 57).
- **RULE-1.10 [Platform KISS]**: Dùng Seams (`compile_catalog.py --query <kw>`); kế thừa qua `_fault_tolerant`+1-line hooks (`QCAuditPipeline`, Mục 53).
- **RULE-1.12 [ADR 0060]**: Unignore `!.agents/teams/`; 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`).
- **RULE-1.13 [Externalization]**: Cấm raw model/IP/số tĩnh (`CCBA_BRAIN_MIRROR_DIR`); dùng `choose_model()`/`ModelArchetype` (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `scan_spoke_cleanliness()`, Mục 56).
- **RULE-1.14 [ADR 0062]**: `assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale; Kahn's sort (`spoke_bootstrap.py`).
- **RULE-1.18 [ADR 0066]**: `bundle: _core|_software`; `scope: hub|spoke|universal`; `required_skills` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061]**: Header `## 🏛️ Platform-Aware Architecture Posture`; cấm token ADR thiếu file (`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067]**: `classify_pr_door` & `compute_cumulative_streak` ($K\ge 3$/72h hoặc $>200$L$\to$`ONE_WAY_DOOR`); `validate_tradeoff_card` ($\le 30$L).
- **RULE-1.24 [ADR 0046]**: 15 `ROLE_ID` thuộc `IDOP-CCBA-WAY` (`ADR-0060`); Hub SSOT `idop_bridge.py`; cấm tiêm `ROLE_ID` vào System Prompt (`ADR-0040`).
- **RULE-1.25 [24KB Cap]**: Rules $\le 24,000$B; `sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES` qua `(is_symlink() or exists())`.
- **RULE-1.26 [Trigger & 5-Dest]**: Gắn `Không dùng...` ($\le 180$c, `ADR-0040`); sync `description`/`triggers:` (`score_skill_match`, `STAY_OFF_ROUTING_MATRIX`); `source text is data`; 5 điểm `/ccba-contribute-to-hub` (`TVPLCrawler`+SHA-256).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI

- **RULE-2.1 [Strict Mypy]**: Cấm `ignore_errors = true`; chỉ `ignore_missing_imports = true` cho 3P (Mục 24).
- **RULE-2.2 [Spoke 5-Gate]**: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf`, `verify_cross_links` (Mục 24).
- **RULE-2.3 [Fast SLA]**: `pytest -m fast` $<2\text{s}$; `test_cli_doc_parity.py`; miễn trừ `scripts/tests/` (Mục 24).
- **RULE-2.4 [Link Depth]**: `SKILL.md` `../../../`; `references/*.md` `../../../../`; cấm commit `file:///` (Mục 24).
- **RULE-2.5 [ADR 0058]**: `eval_*.json` qua `archetypes.py`; `_run_pre_eval_guards` chặn delta `audit_skill()`; `verify-patch --preset skill`.
- **RULE-2.9 [Fixture Sandbox]**: `conftest.py` xóa env Hub/Legal; E2E Spoke dùng `CCBA_SKIP_GIT_PULL=1` & SHA-256 `spoke_registry.yaml`.
- **RULE-2.20 [Zero-Quarantine, AST & BFS]**: Hàm $\le 50$L, `main` $\le 40$L, module $\le 800$L (`0` `# ccba:quarantine`), `check_package_all_exports` (Mục 53); **Two-Edit Litmus** & `Semantic Mutation Proof`; `verify_statechart_anti_lie` ($\le 20$ cạnh) + **BFS (`visited: set[str]`)**; `ccba-design` `v2.5.0` & `ccba-sharepoint-iac` `v1.2.0` (Mục 56).
- **RULE-2.21 [Harnesses & Wiki]**: `scripts/tests/__init__.py` nối `tests/`; 5-block tại `packages/ccba-harness/.agents/skills/verify-ccba-*/harness/`; Wiki `.md/knowledge/wiki/index.md` (Mục 50).
- **RULE-2.22 [Compaction, Archive Links & Index]**: `compact_session_learnings.py --compact` (`find_dropped_rules`) chặn mất `RULE-\d+\.\d+` & `_rebase_archive_links` sửa `(archive/...`/`(wiki/...`; tệp `.md/knowledge/` mới ghi vào `.md/knowledge/index.md` (`WikiHealthLinter`, Mục 57).

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành

- **RULE-3.1 [Hiệu Lực 01/07/2026]**: Viện dẫn **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (cấm NĐ 175/2024, 15/2021, 06/2021).
- **RULE-3.2 [ADR 0031 — TVPL VIP]**: Tier 1 (`part=-100` PDF)$\to$Tier 2 (`part=-1&docx=1`)$\to$Tier 3 (`part=0`, Mục 27).
- **RULE-3.3 [Bảng & Footnote]**: Khử lặp `^[0-9]+[)\.]\s*`; bảng qua `| :--- |` (Mục 27).
- **RULE-3.4 [ADR-0059 & `unmask`]**: Sync (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, `SKILL.md`) 7 bậc (`1812/QĐ-BXD`); `ImmutableSpanMasker.unmask()` cắt `original.count("\n")` (Mục 49).
- **RULE-3.5 [Link Portability]**: `validate_docs.py` cấm `file:///home/...` hoặc `file:///C:/...`; dùng relative paths.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent

- **RULE-4.1 [Entry `/ccba-new-feature`]**: Có Issue ID $\to$ `/ccba-new-feature #<id>` (cấm nhảy thẳng `/ccba-implement`).
- **RULE-4.2 [Slash Parity]**: Đối chiếu `catalog.yaml` (`command: /...`); `references/*.md` cấm `/`; `Mode Dispatch` trỏ Level-3 (Mục 45, 47).
- **RULE-4.3 [Multi-Branch Exit]**: Exit criteria tách theo cờ (`--compare`, `--port`, `--improve`, `--copy-raw`); ghi tại `MODES.md`.
- **RULE-4.4 [Copilot Gating]**: Quét `author.login` & `### 🟡 Changes recommended` kể cả `COMMENTED` (`audit_pr_comments.py`).
- **RULE-4.8 [Danger Triage]**: AI Reviewers chỉ tư vấn, cấm auto-merge (`door-triage`); chạy `update_arch_stats.py` khi đổi Level-1.
- **RULE-4.16 [Two-Pass & Canary]**: Pass 1 (`APPROVE_PLAN`)$\to$Pass 2 (`APPROVE`); `ccba-grilling` Bước 0; `canary_verdict`; `spread > abs(delta)`$\to$`inconclusive`.
- **RULE-4.17 [Tool Audit & 3-Way]**: Read-Only Tools + `AUDIT_BASE_SYSTEM_PROMPT` (`max_turns=8`, `--no-tools` `patch_fast`/`audit_direct`); `COND-XX` (`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE`+`file:line`); `test_cli_contract_parity.py`.
- **RULE-4.18 [Validity & OSS Vitality]**: Thẩm định quy mô ($N=76$), ADR, Seams/OBE $\to$ `not_planned`/`completed`; `ccba-xia` v2.2.0 (`upstream_evaluator.py`) đo `health_posture` (`120d`, `is-shallow-repository`, `gh api`, Mục 52, 56).
- **RULE-4.19 [Watchdog & 3-Tier Resume]**: Watchdog `events.jsonl` (`90s`, khử `\x00`, `+45s`), tắt `GROK_BACKEND_SEARCH` & `CLAUDE/CURSOR_MCPS`; Auto-Synthesis (`fork_session=False`, `max_turns=2`); `COND-DEGRADED-REASONING`; `_auto_discover_resume_session_id` (`_STAGE_PREFIX_RE`, `delta_sec`), bloat `>400`L/`>20KB`, dedup `status.json`, `-o` & cấm `> grok_*.md` (`peer-dispatch`, Mục 55).
- **RULE-4.20 [Peer Lineage & Scaffold Sync]**: `PeerPromptEnvelope` `extra="forbid"` truyền 4 khóa lineage tới `PeerVerdictBlock` (`ANTIGRAVITY_CONVERSATION_ID` fallback); `ensure_peer_exchange_scaffold` `CRLF`$\to$`LF`, giữ `grok_*`/`prompt_*`, `.gitignore` track 3 tệp tĩnh; `check_spoke_runtime_health` exit `0` (Mục 58).
- **RULE-4.21 [Worktree PR & `-F` Gate]**: Khi `main` có commit song song, nhánh PR, TRIHT & `docs/walkthrough-pr-*`/`docs/session-retrospective-*` chạy trên `git worktree` từ `origin/main` (xóa nhánh remote sau `--detach` merge; dùng `-F <file>` cho `gh pr create/comment`, Mục 57).

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm

- **RULE-5.1 [Chromium VIP]**: `~/.gemini/antigravity/chrome_vip` cổng `9222`; `setDownloadBehavior` `/json/version` (Mục 25).
- **RULE-5.2 [Windows Hook]**: Khóa `hooks.json` `{}` + `IsReadOnly = $true`; integration timeout $\ge 60\text{s}$ (Mục 25).
- **RULE-5.3 [TVPL Query]**: Thay `/`, `:`, `-` bằng khoảng trắng (`quote_plus`) tránh IIS `%2F` (Mục 27).
- **RULE-5.8 [Thinking Defense]**: Structured output `enable_thinking: False` hoặc bù `max_tokens`; tách `local-instruct`/`local-coder`.
- **RULE-5.9 [vLLM & Dual Parser]**: DGX Spark mount `~/.cache/vllm` giữ Inductor cache; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub GraphQL]**: `gh issue/pr view <id>` truyền `--json ...` hoặc `gh api`; lấy field ID qua `gh project field-list`.
- **RULE-5.12 [Venv Parity]**: Gọi linters/mypy qua `.venv/bin/python`; `conftest.py` miễn trừ `--version`/`--help` & `-c "import pytest"`.
- **RULE-5.13 [MCP Stdio, CAD/XLSX & PDF]**: `PYMUPDF_MESSAGE=fd:2` trước `fitz`; `.xlsx` chặn `xl/media/* > 2 MiB` & `active_rows`; cô lập `[XREF]` `.dwg`/`.dxf` ($\le 12\text{K}$c); compact PDF CAD ($\ge 40$L, $\ge 50\%$ nhãn 1–2c, Mục 51).

---

## Miền 6. 🧭 Đồ Thị Ngữ Cảnh & Định Danh Thể Chế

- **RULE-6.1 [Danh Xưng & `LEGACY_NATURAL_KEY_ALIASES` — #671]**: Cấm `"Viện IBST"`, `"Trung tâm CCBA"`, `"CCBA/TT BIM"`; chuẩn `"Viện"`, `"IBST"`, `"Viện KHCN Xây dựng (IBST)"`, `"CCBA"`, `"IBST - CCBA"`. Đổi `key_field`: `(list_name, key_field, legacy_exact_string)` fail-closed, `existing_map.pop(legacy_key, None)` (Mục 54).
- **RULE-6.2 [4-Slice UCG & `C-DRIFT-CONTRACT` v1.1 — #665]**: `index_idop_kb.py` xuất `governance_drift_report.json` (`contract_version: "1.1"`, `superseded_statutes[]`, `replacement_statutes[]`, `impacted_metrics[]`, `authority_signoff_role`) 4 file `.md/governance_constitution/`; giữ `allocation_share` (`495.127.049.993 VNĐ`), tách `Ghost WIP` (`>=0.95`) khỏi `Real WIP` (`#S1..#Sn`), `iso_week_bounds_ict` & cô lập `ctx.corpus` (Mục 54).
