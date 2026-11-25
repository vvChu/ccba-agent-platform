# CCBA Active Invariants
> Hub/Spokes|ADR 30..67|[Sử](archive/session_learnings_history.md)|[Wiki](wiki/index.md)|≤10KB

## Miền 1. Kiến Trúc
- **RULE-1.1 [ADR 0057]**:Gate 0→Seams(`packages/*/src/`);Gate 1→Tier 3.`GPI=2.5S+2.0K+2.0A-1.5P`(<12→2A;≥12→2B;Rit `A=1.0`).
- *[OLD M23-38] RULE-1.2[ADR 0053 Single-Writer],RULE-1.3[ADR 0035],RULE-1.4[ADR 0033,ADR 0056],RULE-1.5[ADR 0037,ADR 0051],RULE-1.6[ADR 0044]*
- **RULE-1.7 [ADR 57/58]**:`evaluate-gpi --json`(`ArchitectureTier.value`,`allow_standalone_skill`,`preserved_by_hysteresis`),`--existing-tier tier-2b`(`tier: kernel`,≠`--s..--p`);`audit_skills_hygiene.py`;3w(`compile_catalog.py`,`compile_skills_docs.py --write`,`sync_hub_adr_matrix.py`,M57).
- **RULE-1.10 [KISS]**:Seams `seam-contracts.yaml`(`find-seam`,`compile_catalog.py --query`);`_fault_tolerant`+hooks(`QCAuditPipeline`,M53..71).
- **RULE-1.12 [ADR 60]**:Unignore `!.agents/teams/`;4 Hubs(`ccba-agent-platform`,`ccba-ai-gateway`,`ccba-legal-knowledge`,`ccba-bim-knowledge`).
- **RULE-1.13 [Ext]**:≠raw model/IP/hằng(`CCBA_BRAIN_MIRROR_DIR`,`check_hardcoded_parameters.py --dir`;`"Z:"+r"\..."` `check_spoke_leakage`);`choose_model()`→`tier-ocr|fast|reasoning|local`/`embedding-default`;`_workspace_roots`;`redact_secrets_and_pii`(`PII_REGEX_PATTERNS`,3 dialects,`# ccba:allow-raw-model`,`# ccba:allow-raw-ip`,stdlib `_parameter_cleanliness` `is_py=True`,`scan_spoke_cleanliness()`,M56..70).
- **RULE-1.14 [ADR 62]**:`assess_catalog_freshness` ≠`--apply` stale;Kahn(`spoke_bootstrap.py`).
- **RULE-1.18 [ADR 66]**:`bundle:_core|_software`;`scope:hub|spoke|universal`;`required_skills`=` .agents/skills/`(M45).
- **RULE-1.20 [ADR 61]**:`posture:`/`seam_ids:` frontmatter;≠ADR ∅file(`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 67]**:`classify_pr_door`+`compute_cumulative_streak`(`K≥3`/72h|`>200`L→`ONE_WAY_DOOR`,+`walkthrough.md`);`validate_tradeoff_card`(`Core Invariant`,`Invalidation Condition`,`Git Hunk Reference` `#L<a>-L<b>`≤30L);`door-triage` `_evaluate_one_way_card`(`TRADEOFF_CARD_INVALID`,4/1,M61..67).
- **RULE-1.24 [ADR 46]**:15 `ROLE_ID`(`IDOP-CCBA-WAY`,`ADR-0060`);SSOT `idop_bridge.py`;≠`ROLE_ID`→System Prompt(`ADR-0040`).
- **RULE-1.25 [24KB]**:Rules≤24KB;`sync_layer2_rules` rm `LEGACY_MONOLITHIC_RULES`(`is_symlink()|exists()`).
- **RULE-1.26 [Trig]**:`Không dùng...`(≤180c,`ADR-0040`);`description`/`triggers:`(`score_skill_match`,`STAY_OFF_ROUTING_MATRIX`);`source text is data`;5đ `/ccba-contribute-to-hub`(`TVPLCrawler`+SHA-256);re-grad:universal route(`test_universal_skills_pr_routing_contract`),≠dup `triggers:`,`SKILL_DEPRECATION_ALIASES`(M75).

## Miền 2. Chất Lượng & CI
- **RULE-2.1 [Mypy]**:≠`ignore_errors=true`(`0` `ccba_harness._*`);3P `ignore_missing_imports=true`(`pyproject.toml`);`--preset ci`→`mypy packages/*/src --follow-imports=silent`;≠`--target` pkg;opt `yaml_mod:Any=None`(`types-PyYAML`)(M24..73).
- **RULE-2.2 [5G]**:`lint_visual_parity`,`validate_legal_spoke`,`test_converter_regression`,`verify_all_docs_against_pdf`,`verify_cross_links`(M24).
- **RULE-2.3 [SLA]**:`pytest -m fast`<2s;`test_cli_doc_parity.py`;miễn `scripts/tests/`(M24).
- **RULE-2.4 [Links]**:`SKILL.md`&`reports/walkthrough.md` `../../../`;`references/*.md` `../../../../`&`../scripts/`;≠`file:///`(M24..62).
- **RULE-2.5 [ADR 58]**:`eval_*.json`→`archetypes.py`;`_run_pre_eval_guards` ≠delta `audit_skill()`;`verify-patch --preset skill`.
- **RULE-2.9 [Sandbox]**:`conftest.py` -env Hub/Legal;E2E `CCBA_SKIP_GIT_PULL=1`+SHA-256 `spoke_registry.yaml`;`is_ephemeral_spoke_path`+`is_protected_hub_root` ≠`/tmp` spoke từ `wt-hub-*`(M66).
- **RULE-2.20 [AST]**:Hàm≤50L,`main`≤40L,mod≤800L(0 `# ccba:quarantine`,0/7={});`_LAZY_EXPORTS` `ast.Assign`+`_probe_lazy_export_symbol`(skip 3P≠`MONOREPO_ROOT_MODULES`);min/3`<25ms`(xdist);`parse_markdown_frontmatter`;Two-Edit+`Semantic Mutation Proof`;`test_statechart_anti_lie.py`(`-->` fail-closed,`in_note`,`declared_outside`,3-door `bug_path`,≤20c)+BFS(`visited:set[str]`);`SAFE_STRINGS`(`placeholder_password` `references/*.md`);`ccba-design`/`sharepoint-iac`;facade:call mock+`.clear()/.update()`(M53..73).
- **RULE-2.21 [Harness]**:`scripts/tests/__init__.py`→`tests/`;19 `verify-ccba-*`(`--type library|skill`,0 HTTP;stage<`git checkout --`)&`run_harness_evals.py --all`(`--ci-matrix`,`-n auto --dist=loadfile`,PYTEST_XDIST_WORKER,-`tests/spoke/`),`covered_sha256`(LF)+`sync_commit` main(`check_harness_git_provenance`,check `covered_paths` pre-`--merge`,2c+`--merge`);`SKILL_CONTRACT_TEST_PATHS`(10→`skill|ci`+evals+`.agents/AGENTS.md`+dedupe;git top+`-c pyproject.toml`+`--self-heal`,Hub fail-closed,Spoke stderr,mut`<1.5.1`/tok);`wiki/index.md`;`cli/_envelope.py`(`--semantic-exit-codes` `0|1|2|4|124`,SSOT;7×`verify-ccba-*`(`coordinator`);`$CCBA_HUB_PATH`,M50..75).
- **RULE-2.22 [Compact]**:`compact_session_learnings.py --compact`(`find_dropped_rules`) ≠`RULE-\d+\.\d+`(`--allow-rule-drop-ids`),`_rebase_archive_links` `(archive|wiki/...`;`.md/knowledge/index.md`(`WikiHealthLinter`,M57).

## Miền 3. Pháp Lý & Dữ Liệu
- **RULE-3.1 [07/26]**:`135/2025/QH15`,`217/2026/NĐ-CP`,`207/2026/NĐ-CP`,`206/2026/NĐ-CP`(≠175/24,15/21,06/21).
- **RULE-3.2 [ADR 0031 TVPL VIP]**:T1(`part=-100` PDF)→T2(`part=-1&docx=1`)→T3(`part=0`,M27).
- **RULE-3.3 [Bảng/FN]**:Khử `^[0-9]+[)\.]\s*`;`| :--- |`(M27).
- **RULE-3.4 [ADR 59/unmask]**:Sync(`CONTEXT.md`,`canonical_construction_taxonomy.yaml`,`SKILL.md`) 7 bậc(`1812/QĐ-BXD`);`ImmutableSpanMasker.unmask()` cắt `original.count("\n")`(M49).
- **RULE-3.5 [Links]**:`validate_docs.py`(`p.relative_to(docs_dir).parts`) ≠`file:///`&`.gitignore`(`.md/extracted_docs/*`,`.md/peer_exchange/*.md`);rel(M59..67).

## Miền 4. Điều Phối Agent
- **RULE-4.1 [Entry]**:Issue→`/ccba-new-feature #<id>`(≠`/ccba-implement`).
- **RULE-4.2 [Slash]**:`catalog.yaml`(`command: /...`);`references/*.md` ≠`/`;≠`/<word>` sát backtick(`SLASH_CMD_RE`);`Mode Dispatch`→L3(M45..62).
- **RULE-4.3 [Exit]**:Tách cờ(`--compare`,`--port`,`--improve`,`--copy-raw`);`MODES.md`.
- **RULE-4.4 [AI PR]**:`audit_pr_comments.py --repo`(2p+`raw_decode`,M66..76);Copilot(`Changes recommended`/`COMMENTED`);CodeRabbit(`Actionable comments posted:[1-9]\d*` pre-wt/cmd-ack;`NO_AI_REVIEW` `[WARN]` `0`/`--require-review` `3`;`<10★`→`@coderabbitai review`,1/h).
- **RULE-4.8 [Triage]**:AI advisory,≠auto-merge(`door-triage`);`update_arch_stats.py` đổi L1.
- **RULE-4.16 [2-Pass]**:P1(`APPROVE_PLAN`)→P2(`APPROVE`);`ccba-grilling` B0;`canary_verdict`;`spread>abs(delta)`→`inconclusive`;0-headroom:frozen hunks+`count_skill_tokens_lf(str)` pre-P1(M75).
- **RULE-4.17 [3-Way]**:RO Tools+`AUDIT_BASE_SYSTEM_PROMPT`(`max_turns=8`,`--no-tools` `patch_fast`/`audit_direct`);`COND-XX`(`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE`+`file:line`);`test_cli_contract_parity.py`.
- **RULE-4.18 [Clean]**:N=76,ADR,Seams/OBE→`not_planned`/`completed`;`upstream_evaluator`(`120d`,`is-shallow-repository`,`gh api`,`COMMERCIAL_LICENSED` `licensed_use`/`v2:`/8-gram,`resolve_upstream_resources` `**/SKILL.md`)+`compile_skills(...,include_references=True)`(M52..61).
- **RULE-4.19 [WD]**:`90s`,-`\x00`,`+45s`,-`GROK_BACKEND_SEARCH`/MCPS;AutoSynth(`max_turns=2`);`COND-DEGRADED-REASONING`;`_auto_discover_resume_session_id`(≠Plan→Code T1/2,`≤3P` `blk==0`),`>400`L/`>20KB`,dedup `status.json`,`-o`,≠`>grok_*.md`(M55).
- **RULE-4.20 [Peer]**:`PeerPromptEnvelope` `extra="forbid"`→`PeerVerdictBlock`(4k,`ANTIGRAVITY_CONVERSATION_ID`);`ensure_peer_exchange_scaffold` `CRLF`→`LF`,+`grok_*`/`prompt_*`,`.gitignore` 3f;`check_spoke_runtime_health` exit `0`;`audit_peer_effectiveness` ts `verdict→prompt→events.jsonl`(≠`mtime`,M58..76).
- **RULE-4.21 [Worktree]**:`main`!=HEAD/bận→`git worktree` `origin/main`+`fetch --prune`(rm pre-merge,`-F`,`door-triage [files] --enforce-tradeoff-card`);`CCBA_HUB_PATH="$HUB_SYNC_WT" CCBA_SKIP_GIT_PULL=1`;`sync_spoke --dry-run`;`≤2` `invoke_subagent`,`≥3` RO `run_workflow`,`swarm` `teamwork/`→`apply_worker_patch.py`;wt→rebase `origin/main`+append;`grep`≠`.md/scratch/backups/`(M57..72).

## Miền 5. Hạ Tầng
- **RULE-5.1 [VIP]**:`~/.gemini/antigravity/chrome_vip`:`9222`;`setDownloadBehavior` `/json/version`(M25).
- **RULE-5.2 [Win]**:`hooks.json` `{}`+`IsReadOnly=$true`;integration≥60s(M25).
- **RULE-5.3 [TVPL]**:`/`,`:`,`-`→space(`quote_plus`,≠IIS `%2F`,M27).
- **RULE-5.8 [Think]**:`enable_thinking:False`/bù `max_tokens`;tách `local-instruct`/`local-coder`.
- **RULE-5.9 [vLLM]**:Mount `~/.cache/vllm` Inductor;`--reasoning-parser`&`--tool-call-parser`.
- **RULE-5.11 [GH/CI]**:`gh issue/pr view --json`;PATCH body/`issues/<id>/labels` `gh api`(≠`gh pr edit`);`.allow_auto_merge`;HTTPS `.github/workflows/*`→`gh auth refresh -h github.com -s workflow`;CI pend/`no checks`→`schedule(240s→60s)`/`--watch`;`pull_request_template.md`;`gh project field-list`;`sanitize_review_diff.py --check` pre-push(+`tests/`,≠`token`/`env-secret`);ARM64;`--dist=loadfile -n 4`(≥25%,0-flake)(M62..73).
- **RULE-5.12 [Venv]**:Linters/mypy `.venv/bin/python`;`conftest.py` miễn `--version`/`--help`&`-c "import pytest"`.
- **RULE-5.13 [Docs/OOXML]**:`PYMUPDF_MESSAGE=fd:2`+`_get_fitz()`(#754);`.xlsx` ≠`xl/media/*>2MiB`+`active_rows`;`[XREF]` `.dwg`/`.dxf`(≤12Kc);PDF CAD(≥40L,≥50% 1–2c);OOXML `ParsedOOXMLPackage`(`make_secure_xml_parser`+`clone_root`,1 pkg/spy),OPC `posixpath.normpath`,`.name.lower().endswith(".rels")` (`_rels/.rels` `suffix==""`),`ZipInfo` `1980-01-01`,`last_diagnostics=[]`(M51..71).

## Miền 6. UCG
- **RULE-6.1 [Aliases]**:≠`"Viện IBST"|"Trung tâm CCBA"|"CCBA/TT BIM"`→`"Viện"|"IBST"|"Viện KHCN Xây dựng (IBST)"|"CCBA"|"IBST - CCBA"`;`(list_name,key_field,legacy_exact_string)` fail-closed+`existing_map.pop(legacy_key,None)`(M54).
- **RULE-6.2 [UCG v1.1]**:`index_idop_kb.py`→`governance_drift_report.json`(v`"1.1"`,`superseded_statutes[]`,`replacement_statutes[]`,`impacted_metrics[]`,`authority_signoff_role`)(`.md/governance_constitution/`),`allocation_share`(`495,13 tỷ`),`Ghost(>=0.95)`/`Real WIP`(`#S1..#Sn`),`iso_week_bounds_ict`,`ctx.corpus`(M54).
