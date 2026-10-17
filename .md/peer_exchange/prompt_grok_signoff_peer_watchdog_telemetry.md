---
request_id: "req-20261018-signoff-peer-watchdog-telemetry"
from_agent: "antigravity"
to_agent: "grok"
request_type: "verify"
subject: "Stage 3 Implementation Sign-off: Peer Watchdog, Multi-Turn Telemetry & Tool Lockdown"
timestamp: "2026-10-18T05:54:00+07:00"
profile: "signoff_diff"
output_path: "grok_signoff_peer_watchdog_telemetry.md"
---

# Stage 3 Implementation Sign-off Request: Peer Watchdog, Multi-Turn Telemetry & Tool Lockdown

Please review the completed implementation of the 5 peer collaboration improvements in `packages/ccba-harness` (per the approved `implementation_plan.md`) and start your response immediately with YAML frontmatter enclosed in `---` matching `PeerVerdictBlock` (`FINAL_ACCEPT` or `APPROVE`).

## 1. Automated Verification Status
- `python -m ccba_harness peer-gate`: **8/8 PASS** (`flake8_lint`, `ast_function_length` $\le 50$ LOC, `ast_module_length` ratchet `peer.py` $2175 \to 1880$ LOC, `redundant_comments`, `pytest_suite`, `catalog_freshness`, `dependency_contracts`, `maskara_scan`).
- `python -m ccba_harness verify-patch --preset ci`: **6/6 PASS** (`ruff_lint`, `ruff_format`, `skills_audit`, `adr_matrix`, `catalog_freshness`, `fast_tests`).
- `pytest packages/ccba-harness/tests/test_peer*.py`: **94/94 PASS**.

## 2. Summary of the 5 Implemented Items

1. **Item #1 — Schema Synchronization, `.gate.md` Exclusion & `status.json` Recovery**:
   - `PeerVerdictBlock.telemetry` accepts `PeerVerdictTelemetry | CombinedTelemetry | None = None`.
   - `classify_file_role(path)` excludes `*.gate.md` as `"AUXILIARY"`.
   - `PeerVerdictBlock` coerces float `risk_score` in `[0.0, 5.0]` to `1..5` while preserving strict `ValidationError` for `int > 5`.
   - `normalize_peer_telemetry_costs.py` normalized historical files (`qwen-local` cost `0.0`, `CombinedTelemetry` sum, 3 legacy `risk_score > 5` files), and `run_sync_cycle()` always refreshes `status.json` (`pending_grok: []`).

2. **Item #2 — Headless Optimization & 15 Built-in Tools Lockdown**:
   - Enabled `disable_web_search: True` and `verbatim: True` across all 8 profiles in `PROFILE_SPECS`.
   - Defined `NO_TOOLS_DISALLOW_LIST` locking all 15 built-in tools (`read_file`, `grep`, `list_dir`, `glob`, `bash`, `run_terminal_command`, `edit_file`, `search_replace`, `write_file`, `write`, `spawn_subagent`, `todo_write`, `monitor`, `search_tool`, `use_tool`, `workflow`, `enter_plan_mode`, `exit_plan_mode`, `ask_user_question`, `send_feedback`, `web_fetch`) and `READ_ONLY_DISALLOW_LIST` (`Agent`, `run_terminal_command`, `search_replace`, `write_file`, `write`, `spawn_subagent`, `search_tool`, `use_tool`).

3. **Item #3 — Inter-Stage KV-Cache Inheritance (`--resume` / `--fork-session`) & Multi-Turn Telemetry**:
   - In `_build_telemetry_from_usage_json()` (`_peer_telemetry.py`), when `len(turns) > 1`, merges `turns[-1]` over `data["session"]` so resumed sessions report current-turn metrics instead of Turn 1 metrics.
   - `_accumulate_verdict_telemetry()` aggregates both `PeerVerdictTelemetry` and `CombinedTelemetry.profile_breakdown` into `status.json`.

4. **Item #4 — Liveness-Aware Watchdog (`_peer_watchdog.py`) & `chat_history.jsonl` Rescue**:
   - Extracted `_peer_watchdog.py` (`464` LOC, all functions $\le 50$ LOC), reducing `peer.py` to `1,880` LOC (`module_budget_baseline.json` ratcheted from `2,175` to `1,880`).
   - `inspect_session_liveness(session_id, session_root)` reads the latest event in `events.jsonl`:
     - Fail-fast on `turn_ended:error`, `turn_ended:cancelled`, or `mcp_init_completed:` stall $> 90.0\text{s}$ (never kills `phase_changed:waiting_for_model`).
     - Drains `temp_out.seek(0); stdout_text = temp_out.read()` before terminating when `turn_ended:*` exceeds `5.0\text{s}`.
     - Grants a one-time `+45.0\text{s}` grace window at `deadline` if actively streaming (`phase_changed:streaming_text` / `streaming_reasoning` with `age_s < 5.0\text{s}`).
   - `_run_single_grok_attempt()` falls back to `_recover_verdict_from_chat_history()` when `_unwrap_grok_json_stdout()` sees `stopReason != "end_turn"` or missing frontmatter.

5. **Item #5 — Zero-Reasoning Anomaly Detection (`COND-DEGRADED-REASONING`)**:
   - Added `degraded_reasoning: bool = False` to `PeerVerdictTelemetry` (`True` when `expected_reasoning_effort in ("high", "xhigh")` and `reasoning_tokens <= 0`).
   - `_consolidate_peer_conditions()` / `synthesize_verdicts()` injects `PeerCondition(id="COND-DEGRADED-REASONING", blocking=True)` when `degraded_reasoning` is detected, downgrading `APPROVE` $\to$ `APPROVE_WITH_CONDITIONS`.
