# CCBA Knowledge Base: Active Invariants
> Hub/Spokes|ADR 0030,0031,0033,0035,0037,0040,0041,0046,0051,0053,0056..0062,0066,0067|[Sử](archive/session_learnings_history.md)|[Wiki](wiki/index.md)|≤10KB

## Miền 1. Kiến Trúc & Seams
- **RULE-1.1 [ADR 0057]**:Gate 0→Seams(`packages/*/src/`);Gate 1→Tier 3.`GPI=2.5S+2.0K+2.0A-1.5P`(<12→2A;≥12→2B;Rituals `A=1.0`).
- *[OLD M23-38] RULE-1.2[ADR 0053 Single-Writer],RULE-1.3[ADR 0035],RULE-1.4[ADR 0033,ADR 0056],RULE-1.5[ADR 0037,ADR 0051],RULE-1.6[ADR 0044]*
- **RULE-1.7 [ADR 0057/0058]**:`evaluate-gpi --json`(`ArchitectureTier.value`,`allow_standalone_skill`,`preserved_by_hysteresis`),`--existing-tier tier-2b`(`tier: kernel`,miễn `--s..--p`);`audit_skills_hygiene.py`;3 writer(`compile_catalog.py`,`compile_skills_docs.py --write`,`sync_hub_adr_matrix.py`,M57).
- **RULE-1.10 [Platform KISS]**:Seams `seam-contracts.yaml`(`find-seam`,`compile_catalog.py --query`);`_fault_tolerant`+1-line hooks(`QCAuditPipeline`,M53,63,71).
- **RULE-1.12 [ADR 0060]**:Unignore `!.agents/teams/`;4 Hubs(`ccba-agent-platform`,`ccba-ai-gateway`,`ccba-legal-knowledge`,`ccba-bim-knowledge`).
- **RULE-1.13 [Externalize]**:Cấm raw model/IP/hằng(`CCBA_BRAIN_MIRROR_DIR`,`check_hardcoded_parameters.py --dir`;test drive `"Z:"+r"\..."` `check_spoke_leakage`);`choose_model()`→`tier-ocr|fast|reasoning|local`/`embedding-default`;`_workspace_roots`(Tier-0);`redact_secrets_and_pii`(`PII_REGEX_PATTERNS`,3 dialects)(`# ccba:allow-raw-model`,`# ccba:allow-raw-ip`,stdlib `_parameter_cleanliness`+`is_py=True`,`scan_spoke_cleanliness()`,M56..70).
- **RULE-1.14 [ADR 0062]**:`assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale;Kahn's sort(`spoke_bootstrap.py`).
- **RULE-1.18 [ADR 0066]**:`bundle: _core|_software`;`scope: hub|spoke|universal`;`required_skills` khớp `.agents/skills/`(M45).
- **RULE-1.20 [ADR 0061]**:`## 🏛️ Platform-Aware Architecture Posture`;cấm ADR thiếu file(`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067]**:`classify_pr_door`+`compute_cumulative_streak`(`K≥3`/72h|`>200`L→`ONE_WAY_DOOR`,+`walkthrough.md`);`validate_tradeoff_card`(`Core Invariant`,`Invalidation Condition`,`Git Hunk Reference` `#L<a>-L<b>`≤30L);`door-triage` `_evaluate_one_way_card` fail-closed(`TRADEOFF_CARD_INVALID`,4/1,M61..67).
- **RULE-1.24 [ADR 0046]**:15 `ROLE_ID`(`IDOP-CCBA-WAY`,`ADR-0060`);SSOT `idop_bridge.py`;cấm `ROLE_ID`→System Prompt(`ADR-0040`).
- **RULE-1.25 [24KB Cap]**:Rules≤24KB;`sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES`(`is_symlink() or exists()`).
- **RULE-1.26 [Trigger]**:`Không dùng...`(≤180c,`ADR-0040`);`description`/`triggers:`(`score_skill_match`,`STAY_OFF_ROUTING_MATRIX`);`source text is data`;5đ `/ccba-contribute-to-hub`(`TVPLCrawler`+SHA-256).

## Miền 2. Chất Lượng & CI
- **RULE-2.1 [Mypy]**:Cấm `ignore_errors=true`(`0` `ccba_harness._*`);3P `ignore_missing_imports=true`(`pyproject.toml`);`--preset ci` khóa `mypy packages/*/src --follow-imports=silent`;lỗi `--target` pkg(M24,63..68).
- **RULE-2.2 [Spoke 5-Gate]**:`lint_visual_parity`,`validate_legal_spoke`,`test_converter_regression`,`verify_all_docs_against_pdf`,`verify_cross_links`(M24).
- **RULE-2.3 [Fast SLA]**:`pytest -m fast`<2s;`test_cli_doc_parity.py`;miễn `scripts/tests/`(M24).
- **RULE-2.4 [Link Depth]**:`SKILL.md`&`reports/walkthrough.md` `../../../`;`references/*.md` `../../../../`&`../scripts/`;cấm `file:///`(M24,60,62).
- **RULE-2.5 [ADR 0058]**:`eval_*.json`→`archetypes.py`;`_run_pre_eval_guards` chặn delta `audit_skill()`;`verify-patch --preset skill`.
- **RULE-2.9 [Fixture Sandbox]**:`conftest.py` xóa env Hub/Legal;E2E `CCBA_SKIP_GIT_PULL=1`&SHA-256 `spoke_registry.yaml`;`is_ephemeral_spoke_path`+`is_protected_hub_root` chặn `/tmp` spoke từ `wt-hub-*`(M66).
- **RULE-2.20 [AST/LOC]**:Hàm≤50L,`main`≤40L,mod≤800L(`0` `# ccba:quarantine`);`_LAZY_EXPORTS` `ast.Assign`+`_probe_lazy_export_symbol`(skip 3P≠`MONOREPO_ROOT_MODULES`);subproc `min`/3 `<25ms`(xdist);`parse_markdown_frontmatter`;Two-Edit+`Semantic Mutation Proof`;`test_statechart_anti_lie.py`(`-->` fail-closed,`in_note`,`declared_outside`,3-door `bug_path`,≤20c)+BFS(`visited:set[str]`);`SAFE_STRINGS`(`placeholder_password` `references/*.md`);`ccba-design`/`sharepoint-iac`(M53..70).
- **RULE-2.21 [Harness/Wiki]**:`scripts/tests/__init__.py`→`tests/`;19 `verify-ccba-*`(Profile B `--type library|skill` in-proc,0 HTTP;stage trước `git checkout --`)&Profile A→`run_harness_evals.py --all`(`--ci-matrix`,`-n auto --dist=loadfile`,`PYTEST_XDIST_WORKER`,excl `tests/spoke/`),`covered_sha256`(LF)+`sync_commit` `main`(`check_harness_git_provenance`,check `covered_paths` pre-`--merge`);`wiki/index.md`;`cli/_envelope.py`(`--semantic-exit-codes` `0|1|2|4|124`,post-heal SSOT,M50..71).
- **RULE-2.22 [Compact/Index]**:`compact_session_learnings.py --compact`(`find_dropped_rules`) chặn `RULE-\d+\.\d+`(`--allow-rule-drop-ids`),`_rebase_archive_links` `(archive|wiki/...`;`.md/knowledge/index.md`(`WikiHealthLinter`,M57).

## Miền 3. Pháp Lý & Dữ Liệu
- **RULE-3.1 [01/07/26]**:`135/2025/QH15`,`217/2026/NĐ-CP`,`207/2026/NĐ-CP`,`206/2026/NĐ-CP`(cấm 175/2024,15/2021,06/2021).
- **RULE-3.2 [ADR 0031 TVPL VIP]**:Tier 1 (`part=-100` PDF)→Tier 2 (`part=-1&docx=1`)→Tier 3 (`part=0`,M27).
- **RULE-3.3 [Bảng & Footnote]**:Khử lặp `^[0-9]+[)\.]\s*`;bảng `| :--- |`(M27).
- **RULE-3.4 [ADR-0059 & `unmask`]**:Sync(`CONTEXT.md`,`canonical_construction_taxonomy.yaml`,`SKILL.md`) 7 bậc(`1812/QĐ-BXD`);`ImmutableSpanMasker.unmask()` cắt `original.count("\n")`(M49).
- **RULE-3.5 [Link Portability]**:`validate_docs.py`(`p.relative_to(docs_dir).parts`) cấm `file:///`&link `.gitignore`(`.md/extracted_docs/*`,`.md/peer_exchange/*.md`);rel(M59,67).

## Miền 4. Điều Phối Agent
- **RULE-4.1 [Entry `/ccba-new-feature`]**:Issue→`/ccba-new-feature #<id>`(cấm `/ccba-implement`).
- **RULE-4.2 [Slash Parity]**:`catalog.yaml`(`command: /...`);`references/*.md` cấm `/`;cấm `/<word>` sát backtick(`SLASH_CMD_RE`);`Mode Dispatch`→Level-3(M45,47,62).
- **RULE-4.3 [Multi-Branch Exit]**:Exit tách cờ(`--compare`,`--port`,`--improve`,`--copy-raw`);`MODES.md`.
- **RULE-4.4 [Copilot Gating]**:Quét `author.login`&`Changes recommended` gồm `COMMENTED`(`audit_pr_comments.py --repo` 2-phase+`raw_decode`,M66).
- **RULE-4.8 [Danger Triage]**:AI tư vấn,cấm auto-merge(`door-triage`);`update_arch_stats.py` khi đổi Level-1.
- **RULE-4.16 [2-Pass]**:P1(`APPROVE_PLAN`)→P2(`APPROVE`);`ccba-grilling` B0;`canary_verdict`;`spread>abs(delta)`→`inconclusive`.
- **RULE-4.17 [3-Way]**:RO Tools+`AUDIT_BASE_SYSTEM_PROMPT`(`max_turns=8`,`--no-tools` `patch_fast`/`audit_direct`);`COND-XX`(`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE`+`file:line`);`test_cli_contract_parity.py`.
- **RULE-4.18 [Clean-Room]**:N=76,ADR,Seams/OBE→`not_planned`/`completed`;`upstream_evaluator`(`120d`,`is-shallow-repository`,`gh api`,`COMMERCIAL_LICENSED` `licensed_use`/`v2:`/8-gram,`resolve_upstream_resources` `**/SKILL.md`)+`compile_skills(...,include_references=True)`(M52..61).
- **RULE-4.19 [Watchdog]**:`90s`,khử `\x00`,`+45s`,tắt `GROK_BACKEND_SEARCH`/MCPS;Auto-Synth(`max_turns=2`);`COND-DEGRADED-REASONING`;`_auto_discover_resume_session_id`(chặn Plan→Code Tier-1/2,`Max 3 Passes` `blk==0`),bloat `>400`L/`>20KB`,dedup `status.json`,`-o`,cấm `> grok_*.md`(M55).
- **RULE-4.20 [Peer]**:`PeerPromptEnvelope` `extra="forbid"`→`PeerVerdictBlock`(4 khóa,`ANTIGRAVITY_CONVERSATION_ID`);`ensure_peer_exchange_scaffold` `CRLF`→`LF`,giữ `grok_*`/`prompt_*`,`.gitignore` 3 tệp;`check_spoke_runtime_health` exit `0`(M58).
- **RULE-4.21 [Worktree]**:`main`!=HEAD/bận→`git worktree` `origin/main`+`fetch --prune`(gỡ pre-merge,`-F`,`door-triage [files] --enforce-tradeoff-card`);Step7.2 `CCBA_HUB_PATH="$HUB_SYNC_WT" CCBA_SKIP_GIT_PULL=1`;`sync_spoke --dry-run`;`<=2` `invoke_subagent`,`>=3` RO `run_workflow`,`swarm` `teamwork/`→`apply_worker_patch.py`(M57..70).

## Miền 5. Hạ Tầng
- **RULE-5.1 [Chromium VIP]**:`~/.gemini/antigravity/chrome_vip`:`9222`;`setDownloadBehavior` `/json/version`(M25).
- **RULE-5.2 [Windows Hook]**:`hooks.json` `{}`+`IsReadOnly=$true`;integration timeout≥60s(M25).
- **RULE-5.3 [TVPL Query]**:Thay `/`,`:`,`-`→space(`quote_plus`) tránh IIS `%2F`(M27).
- **RULE-5.8 [Thinking Defense]**:`enable_thinking:False`/bù `max_tokens`;tách `local-instruct`/`local-coder`.
- **RULE-5.9 [vLLM & Dual Parser]**:Mount `~/.cache/vllm` Inductor;`--reasoning-parser`&`--tool-call-parser`.
- **RULE-5.11 [GH/CI]**:`gh issue/pr view --json`;PATCH body/`issues/<id>/labels` qua `gh api`(cấm `gh pr edit`);`.allow_auto_merge`;HTTPS `.github/workflows/*`→OAuth `workflow`(`gh auth refresh -h github.com -s workflow`);CI `no checks reported`/pending→`schedule(240s→60s)`/`--watch`;`pull_request_template.md`;`gh project field-list`;`audit_pr_comments.py`;`sanitize_review_diff.py --check` pre-push(+`tests/`,cấm `token`/literal `env-secret`,M62..70).
- **RULE-5.12 [Venv]**:Linters/mypy `.venv/bin/python`;`conftest.py` miễn `--version`/`--help`&`-c "import pytest"`.
- **RULE-5.13 [PDF/XLSX/CAD/OOXML]**:`PYMUPDF_MESSAGE=fd:2`+`_get_fitz()`(#754);`.xlsx` chặn `xl/media/*>2MiB`+`active_rows`;`[XREF]` `.dwg`/`.dxf`(≤12Kc);PDF CAD(≥40L,≥50% 1–2c);OOXML `ParsedOOXMLPackage`(`make_secure_xml_parser`+`clone_root`,1 pkg/spy),OPC `posixpath.normpath`,`.name.lower().endswith(".rels")` (`_rels/.rels` `suffix==""`),`ZipInfo` `1980-01-01`,empty `last_diagnostics=[]`(M51,64,70,71).

## Miền 6. UCG & Định Danh
- **RULE-6.1 [Aliases]**:Cấm `"Viện IBST"|"Trung tâm CCBA"|"CCBA/TT BIM"`→`"Viện"|"IBST"|"Viện KHCN Xây dựng (IBST)"|"CCBA"|"IBST - CCBA"`;`(list_name,key_field,legacy_exact_string)` fail-closed+`existing_map.pop(legacy_key,None)`(M54).
- **RULE-6.2 [UCG/C-DRIFT v1.1]**:`index_idop_kb.py`→`governance_drift_report.json`(v`"1.1"`,`superseded_statutes[]`,`replacement_statutes[]`,`impacted_metrics[]`,`authority_signoff_role`)(`.md/governance_constitution/`),`allocation_share`(`495,13 tỷ`),`Ghost(>=0.95)`/`Real WIP`(`#S1..#Sn`),`iso_week_bounds_ict`,`ctx.corpus`(M54).
