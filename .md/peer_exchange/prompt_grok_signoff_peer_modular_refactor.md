---
request_id: req-20261018-peer-modular-refactor-signoff
from_agent: antigravity
to_agent: grok
request_type: verify
subject: "Stage 3 Post-Code Sign-Off: Modular Decomposition of peer.py & Removal of 5 CLI Quarantines"
timestamp: "2026-10-18T09:26:30+07:00"
source_documents:
  - packages/ccba-harness/src/ccba_harness/peer.py
  - packages/ccba-harness/src/ccba_harness/_peer_models.py
  - packages/ccba-harness/src/ccba_harness/_peer_anchor.py
  - packages/ccba-harness/src/ccba_harness/_peer_co_review.py
  - packages/ccba-harness/src/ccba_harness/_peer_telemetry.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/peer.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/_peer_auto_apply.py
  - packages/ccba-harness/src/ccba_harness/module_budget_baseline.json
output_path: grok_signoff_peer_modular_refactor.md
profile: signoff_diff
target_files:
  - packages/ccba-harness/src/ccba_harness/peer.py
  - packages/ccba-harness/src/ccba_harness/_peer_models.py
  - packages/ccba-harness/src/ccba_harness/_peer_anchor.py
  - packages/ccba-harness/src/ccba_harness/_peer_co_review.py
  - packages/ccba-harness/src/ccba_harness/_peer_telemetry.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/peer.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/_peer_auto_apply.py
  - packages/ccba-harness/src/ccba_harness/module_budget_baseline.json
---

# Stage 3 Post-Code Sign-Off Request: `peer.py` Modular Decomposition & CLI Quarantine Removal

Please review and sign off on the completed refactoring of `packages/ccba-harness/src/ccba_harness/peer.py` and its related modules (`P1 + P2`).

## 1. Architectural Changes Implemented

### P1 — Modular Decomposition of `peer.py` (`1,879` LOC $\to$ `775` LOC, removed from `module_budget_baseline.json`)
1. **`_peer_models.py` (`324` lines, `max_func=31` lines):**
   - Extracted all 12 Pydantic/NamedTuple schemas (`FileChange`, `PatchReplacement`, `FilePatch`, `AnchorPatchPayload`, `PeerPromptEnvelope`, `PeerCondition`, `PeerVerdictTelemetry`, `ProfileTelemetryItem`, `CombinedTelemetry`, `PeerVerdictBlock`, `PeerConsensusReport`, `AutoApplyResult`) and 5 YAML frontmatter helpers (`extract_frontmatter`, `parse_envelope_from_md`, `parse_verdict_from_md`, `render_prompt_header`, `render_verdict_header`) into a leaf module.
2. **`_peer_telemetry.py` (`181` lines, `max_func=46` lines):**
   - Replaced lazy circular imports (`from .peer import PeerVerdictTelemetry`) and `Any` return annotations with direct static imports (`from ._peer_models import PeerVerdictTelemetry`, `from ._peer_watchdog import CostMode`).
3. **`_peer_anchor.py` (`408` lines, `max_func=44` lines):**
   - Extracted Level-2/3 Anchor Patch Engine and transactional byte-journal rollback (`extract_anchor_payload`, `apply_anchor_patch`, `get_git_toplevel`, `recover_pending_anchor_transactions`, `auto_apply_and_verify_patch`, and private helpers).
   - Preserved all existing test mock targets (`ccba_harness.peer.atomic_write_text`, `ccba_harness.peer.atomic_write_bytes`, `ccba_harness.peer.verify_patch_execution`) via `_peer_mod` namespace lookup.
4. **`_peer_co_review.py` (`365` lines, `max_func=48` lines):**
   - Extracted Multi-Agent Co-Review & Consensus Synthesis (`synthesize_verdicts`, `render_consensus_report_markdown`, `orchestrate_peer_co_review`, and private helpers).
   - Preserved `ccba_harness.peer.invoke_grok_cli`, `atomic_write_text`, and `safe_read_and_hash` mock targets via `_peer_mod` namespace lookup.
5. **`peer.py` (`775` lines < `800` LOC hard cap, `max_func=48` lines):**
   - Removed `"packages/ccba-harness/src/ccba_harness/peer.py": 1880` from `packages/ccba-harness/src/ccba_harness/module_budget_baseline.json`.
   - Deduplicated `atomic_write_text` to delegate directly to `atomic_write_bytes(target, content.encode("utf-8"), max_retries=max_retries)`.
   - Exported `DEFAULT_GROK_SPEC` and preserved 100% backward-compatible re-exports on `ccba_harness.peer`.

### P2 — Removal of All 5 `# ccba:quarantine` Bypasses (Issue #494) & Dry-Run Parity
1. **`cli/commands/peer.py` (`650` lines, `0` quarantines, all CLI post-parse bodies $\le 38$ lines):**
   - Removed `# ccba:quarantine` on `run_peer_dispatch_cli`, `run_peer_co_review_cli`, and `run_apply_anchor_patch_cli`.
   - Extracted `_print_dispatch_dry_run` reusing `DEFAULT_GROK_SPEC`, `_resolve_target_models`, and `_resolve_grok_profile_options` from `ccba_harness.peer`, fixing the `reasoning_effort` drift (`"high"` vs `"xhigh"`) between `--dry-run` and live execution.
   - Extracted `_validate_co_review_preconditions`, `_print_co_review_dry_run`, `_render_co_review_cli_result`, `_emit_patch_cli_error`, and `_emit_patch_cli_success`.
2. **`cli/commands/_peer_auto_apply.py` (`206` lines, `max_func=49` lines, `0` quarantines):**
   - Removed `# ccba:quarantine` on `handle_peer_dispatch_auto_apply` and `handle_peer_co_review_auto_apply` by extracting `_validate_dispatch_output_for_auto_apply` and `_validate_co_review_for_auto_apply`.

## 2. Deterministic Verification Receipts (`[đo thực tế]`)
- `python -m ccba_harness peer-gate`: **PASS (8/8 checks: `pytest_suite`, `flake8_lint`, `ast_function_length`, `redundant_comment_sanitation`, `import_cycle_check`, `hub_import_depth`, `secret_ip_cleanliness`, `module_size_budget`)**.
- `python -m ccba_harness verify-patch --preset code`: **PASS (3/3 commands: `ruff check .`, `ruff format --check .`, `pytest tests/ -q` — 525 passed)**.
- `pytest packages/ccba-harness/tests/test_peer*.py tests/governance/test_module_budget_ratchet.py -q`: **105 passed**.

## 3. Audit Instructions
1. You may inspect any of the target files if needed (keep tool calls minimal, $\le 4$ turns) and verify:
   - Module budget compliance (`peer.py` removed from `module_budget_baseline.json` and $\le 800$ LOC).
   - Function length compliance ($\le 50$ LOC for domain functions, $\le 40$ LOC post-parse for CLI handlers, `0` quarantines).
   - Backward compatibility of public seams and mock patch targets on `ccba_harness.peer`.
2. Start your response immediately with YAML frontmatter enclosed in `---` containing `request_id: req-20261018-peer-modular-refactor-signoff`, `verdict` (`FINAL_ACCEPT` | `APPROVE` | `APPROVE_WITH_CONDITIONS` | `REJECT`), `risk_score` (1-5), `conditions`, and `summary`, followed by a concise verification table.
