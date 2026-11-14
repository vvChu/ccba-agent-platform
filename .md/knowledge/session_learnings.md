# 🧠 CCBA Knowledge Base: Active Invariants

> **Phạm vi:** Hub/Spokes | **Chuẩn:** ADR 0030, 0031, 0033, 0035, 0037, 0041, 0046, 0051, 0053, 0056..0058, 0060..0062, 0066, 0067, ADR-0040, ADR-0059.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | **Wiki:** [wiki/index.md](wiki/index.md) | Trần: ≤ 10 KB

---

## Miền 1. 🏛️ Kiến Trúc & Seams

- **RULE-1.1 [ADR 0057]**: Gate 0→Seams (`packages/*/src/`); Gate 1→Tier 3. `GPI=2.5S+2.0K+2.0A-1.5P` (<12→2A; ≥12→2B; Rituals `A=1.0`).
- *([DEPRECATED] Mục 23-38: RULE-1.2 [ADR 0053 — Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051], RULE-1.6 [ADR 0044])*
- **RULE-1.7 [ADR 0057/0058 — GPI JSON]**: `evaluate-gpi --json` (`ArchitectureTier.value`, `allow_standalone_skill`, `preserved_by_hysteresis`), `--existing-tier tier-2b` (`tier: kernel`, miễn 4 khóa `--s..--p`); `audit_skills_hygiene.py`; Hub 3 writer (`compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, Mục 57).
- **RULE-1.10 [Platform KISS]**: Seams (`compile_catalog.py --query <kw>`); kế thừa `_fault_tolerant`+1-line hooks (`QCAuditPipeline`, Mục 53).
- **RULE-1.12 [ADR 0060]**: Unignore `!.agents/teams/`; 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`).
- **RULE-1.13 [Externalization]**: Cấm raw model/IP/hằng (`CCBA_BRAIN_MIRROR_DIR`); `choose_model()`/`ModelArchetype` (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `scan_spoke_cleanliness()`, Mục 56).
- **RULE-1.14 [ADR 0062]**: `assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale; Kahn's sort (`spoke_bootstrap.py`).
- **RULE-1.18 [ADR 0066]**: `bundle: _core|_software`; `scope: hub|spoke|universal`; `required_skills` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061]**: `## 🏛️ Platform-Aware Architecture Posture`; cấm token ADR thiếu file (`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067]**: `classify_pr_door` & `compute_cumulative_streak` (`K≥3`/72h hoặc `>200`L→`ONE_WAY_DOOR`, cả `walkthrough.md`); `validate_tradeoff_card` (≤30L, Mục 61).
- **RULE-1.24 [ADR 0046]**: 15 `ROLE_ID` (`IDOP-CCBA-WAY`, `ADR-0060`); Hub SSOT `idop_bridge.py`; cấm tiêm `ROLE_ID` vào System Prompt (`ADR-0040`).
- **RULE-1.25 [24KB Cap]**: Rules ≤24,000B; `sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES` qua `(is_symlink() or exists())`.
- **RULE-1.26 [Trigger & 5-Dest]**: `Không dùng...` (≤180c, `ADR-0040`); `description`/`triggers:` (`score_skill_match`, `STAY_OFF_ROUTING_MATRIX`); `source text is data`; 5đ `/ccba-contribute-to-hub` (`TVPLCrawler`+SHA-256).

---

## Miền 2. 🔒 Chất Lượng & CI

- **RULE-2.1 [Strict Mypy]**: Cấm `ignore_errors = true`; chỉ `ignore_missing_imports = true` cho 3P (Mục 24).
- **RULE-2.2 [Spoke 5-Gate]**: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf`, `verify_cross_links` (Mục 24).
- **RULE-2.3 [Fast SLA]**: `pytest -m fast` <2s; `test_cli_doc_parity.py`; miễn `scripts/tests/` (Mục 24).
- **RULE-2.4 [Link Depth]**: `SKILL.md` & `reports/walkthrough.md` `../../../`; `references/*.md` `../../../../` & `../scripts/`; cấm commit `file:///` (Mục 24, 60, 62).
- **RULE-2.5 [ADR 0058]**: `eval_*.json` qua `archetypes.py`; `_run_pre_eval_guards` chặn delta `audit_skill()`; `verify-patch --preset skill`.
- **RULE-2.9 [Fixture Sandbox]**: `conftest.py` xóa env Hub/Legal; E2E Spoke `CCBA_SKIP_GIT_PULL=1` & SHA-256 `spoke_registry.yaml`.
- **RULE-2.20 [AST, LOC & BFS]**: Hàm ≤50L (`uvx ruff format`, `pytest scripts/tests/`), `main` ≤40L, module ≤800L (`0` `# ccba:quarantine`), `check_package_all_exports` (Mục 53); **Two-Edit Litmus** & `Semantic Mutation Proof`; `verify_statechart_anti_lie` (≤20 cạnh) + **BFS (`visited: set[str]`)**; `SAFE_STRINGS` (`placeholder_password` `references/*.md`); `ccba-design` `v2.6.0` & `ccba-sharepoint-iac` `v1.2.0` (Mục 56..61).
- **RULE-2.21 [Harnesses & Wiki]**: `scripts/tests/__init__.py` nối `tests/`; 5-block `verify-ccba-*/harness/` nối `run_harness_evals.py --all`, khóa `covered_sha256` (LF)+`sync_commit` `main` qua `check_harness_git_provenance` fail-closed; Wiki `.md/knowledge/wiki/index.md` (Mục 50, 58, 59).
- **RULE-2.22 [Compaction & Index]**: `compact_session_learnings.py --compact` (`find_dropped_rules`) chặn `RULE-\d+\.\d+` (`--allow-rule-drop-ids`), `_rebase_archive_links` `(archive|wiki/...`; ghi `.md/knowledge/index.md` (`WikiHealthLinter`, Mục 57).

---

## Miền 3. 📜 Pháp Lý & Dữ Liệu

- **RULE-3.1 [Hiệu Lực 01/07/26]**: **Luật XD 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (cấm NĐ 175/2024, 15/2021, 06/2021).
- **RULE-3.2 [ADR 0031 — TVPL VIP]**: Tier 1 (`part=-100` PDF)→Tier 2 (`part=-1&docx=1`)→Tier 3 (`part=0`, Mục 27).
- **RULE-3.3 [Bảng & Footnote]**: Khử lặp `^[0-9]+[)\.]\s*`; bảng qua `| :--- |` (Mục 27).
- **RULE-3.4 [ADR-0059 & `unmask`]**: Sync (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, `SKILL.md`) 7 bậc (`1812/QĐ-BXD`); `ImmutableSpanMasker.unmask()` cắt `original.count("\n")` (Mục 49).
- **RULE-3.5 [Link Portability]**: `validate_docs.py` (`p.relative_to(docs_dir).parts`) cấm `file:///`; rel paths (Mục 59).

---

## Miền 4. 🛠️ Điều Phối Agent

- **RULE-4.1 [Entry `/ccba-new-feature`]**: Issue ID → `/ccba-new-feature #<id>` (cấm nhảy `/ccba-implement`).
- **RULE-4.2 [Slash Parity]**: `catalog.yaml` (`command: /...`); `references/*.md` cấm `/`; cấm `/<word>` sát sau backtick (`SLASH_CMD_RE`); `Mode Dispatch` trỏ Level-3 (Mục 45, 47, 62).
- **RULE-4.3 [Multi-Branch Exit]**: Exit criteria tách cờ (`--compare`, `--port`, `--improve`, `--copy-raw`); `MODES.md`.
- **RULE-4.4 [Copilot Gating]**: Quét `author.login` & `### 🟡 Changes recommended` gồm `COMMENTED` (`audit_pr_comments.py`).
- **RULE-4.8 [Danger Triage]**: AI chỉ tư vấn, cấm auto-merge (`door-triage`); chạy `update_arch_stats.py` khi đổi Level-1.
- **RULE-4.16 [Two-Pass & Canary]**: Pass 1 (`APPROVE_PLAN`)→Pass 2 (`APPROVE`); `ccba-grilling` Bước 0; `canary_verdict`; `spread > abs(delta)`→`inconclusive`.
- **RULE-4.17 [Tool Audit & 3-Way]**: Read-Only Tools+`AUDIT_BASE_SYSTEM_PROMPT` (`max_turns=8`, `--no-tools` `patch_fast`/`audit_direct`); `COND-XX` (`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE`+`file:line`); `test_cli_contract_parity.py`.
- **RULE-4.18 [Validity & Clean-Room]**: Quy mô (`N=76`), ADR, Seams/OBE→`not_planned`/`completed`; `upstream_evaluator.py` (`health_posture` `120d`, `is-shallow-repository`, `gh api`, `COMMERCIAL_LICENSED` `licensed_use`/`v2:`/8-gram, seed `triage_ledger` `resolve_upstream_resources` `**/SKILL.md`) & `compile_skills(..., include_references=True)` (Mục 52, 60, 61).
- **RULE-4.19 [Watchdog & Resume]**: Watchdog (`90s`, khử `\x00`, `+45s`), tắt `GROK_BACKEND_SEARCH`/MCPS; Auto-Synthesis (`max_turns=2`); `COND-DEGRADED-REASONING`; `_auto_discover_resume_session_id` (chặn Plan→Code Tier-1/2, `Max 3 Passes` `blk==0`), bloat `>400`L/`>20KB`, dedup `status.json`, `-o` & cấm `> grok_*.md` (Mục 55).
- **RULE-4.20 [Peer Lineage]**: `PeerPromptEnvelope` `extra="forbid"`→`PeerVerdictBlock` (4 khóa, `ANTIGRAVITY_CONVERSATION_ID` fallback); `ensure_peer_exchange_scaffold` `CRLF`→`LF`, giữ `grok_*`/`prompt_*`, `.gitignore` track 3 tệp; `check_spoke_runtime_health` exit `0` (Mục 58).
- **RULE-4.21 [Worktree & 3-Tier]**: `main` bận/root `!=main`→`git worktree` `origin/main`+`fetch --prune origin main:main` (gỡ trước merge, `-F`, `door-triage --enforce-tradeoff-card`); `<=2` `invoke_subagent`, `>=3` RO `run_workflow`, `swarm` `.system_generated/scratch/teamwork/`→`apply_worker_patch.py` (Mục 57, 58, 62).

---

## Miền 5. 💻 Hạ Tầng

- **RULE-5.1 [Chromium VIP]**: `~/.gemini/antigravity/chrome_vip` cổng `9222`; `setDownloadBehavior` `/json/version` (Mục 25).
- **RULE-5.2 [Windows Hook]**: Khóa `hooks.json` `{}`+`IsReadOnly = $true`; integration timeout ≥60s (Mục 25).
- **RULE-5.3 [TVPL Query]**: Thay `/`, `:`, `-` bằng space (`quote_plus`) tránh IIS `%2F` (Mục 27).
- **RULE-5.8 [Thinking Defense]**: `enable_thinking: False` hoặc bù `max_tokens`; tách `local-instruct`/`local-coder`.
- **RULE-5.9 [vLLM & Dual Parser]**: Mount `~/.cache/vllm` giữ Inductor; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub API & CI]**: `gh issue/pr view <id> --json ...`; PATCH `gh api .../pulls/<id> -X PATCH -F body=@<file>` (cấm `gh pr edit`); `gh api repos/{owner}/{repo} --jq .allow_auto_merge` (cấm `--json autoMergeAllowed`); CI `gh pr checks --watch`/`240s`→`60s`; `.github/pull_request_template.md` chữ thường; `gh project field-list` (Mục 62).
- **RULE-5.12 [Venv Parity]**: Linters/mypy `.venv/bin/python`; `conftest.py` miễn `--version`/`--help` & `-c "import pytest"`.
- **RULE-5.13 [Stdio, CAD/XLSX & PDF]**: `PYMUPDF_MESSAGE=fd:2` trước `fitz`; `.xlsx` chặn `xl/media/* > 2 MiB` & `active_rows`; tách `[XREF]` `.dwg`/`.dxf` (≤12Kc); compact PDF CAD (≥40L, ≥50% nhãn 1–2c, Mục 51).

---

## Miền 6. 🧭 UCG & Định Danh

- **RULE-6.1 [Danh Xưng & `LEGACY_NATURAL_KEY_ALIASES`]**: Cấm `"Viện IBST"`, `"Trung tâm CCBA"`, `"CCBA/TT BIM"`; dùng `"Viện"`/`"IBST"`/`"Viện KHCN Xây dựng (IBST)"`/`"CCBA"`/`"IBST - CCBA"`; đổi `key_field`: `(list_name, key_field, legacy_exact_string)` fail-closed+`existing_map.pop(legacy_key, None)` (Mục 54).
- **RULE-6.2 [UCG & `C-DRIFT-CONTRACT` v1.1]**: `index_idop_kb.py` xuất `governance_drift_report.json` (`contract_version:"1.1"`, `superseded_statutes[]`, `replacement_statutes[]`, `impacted_metrics[]`, `authority_signoff_role`) (`.md/governance_constitution/`), `allocation_share` (`495,13 tỷ`), `Ghost WIP` (`>=0.95`)/`Real WIP` (`#S1..#Sn`), `iso_week_bounds_ict`, `ctx.corpus` (Mục 54).
