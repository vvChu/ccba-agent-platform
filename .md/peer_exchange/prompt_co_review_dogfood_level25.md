---
request_id: "req-dogfood-co-review-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
subject: "Dogfooding Multi-Agent Co-Review: Thẩm định Toàn Diện PR #487 & PR #489 (ADR-0065 & Level-2.5 Orchestration)"
timestamp: "2026-10-06T07:43:00+07:00"
max_turns: 15
source_documents: []
output_path: ".md/peer_exchange/grok_consensus_co_review_dogfood_level25.md"
context: "Dogfooding thực chiến hệ thống Multi-Agent Co-Review song song (code_review trên Gemini Flash + arch_audit trên Grok-4.7 xhigh)."
---

# 🎯 Yêu Cầu Thẩm Tra Đa Tác Nhân (Multi-Agent Co-Review): PR #487 & PR #489

> ⚠️ **Chỉ Dẫn Cho Reviewers**: Toàn bộ diff mã nguồn cốt lõi của PR #487 & PR #489 đã được đính kèm trực tiếp tại Mục 3 dưới đây. Bạn **KHÔNG CẦN** gọi các công cụ đọc đĩa tốn lượt. Hãy tiến hành rà soát kỹ thuật đối kháng và xuất ngay báo cáo thẩm định bắt đầu bằng khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra theo đúng mẫu ở Mục 4!

Chào các tác nhân đánh giá, hệ thống đang thực hiện phiên **Dogfooding thực chiến Level-2.5 Multi-Agent Co-Review** đối với chuỗi 2 PR nâng cấp nền tảng quan trọng vừa được sáp nhập vào `main`:

1. **PR #487 (ADR-0065: Peer Runtime Hardening & Topological Fail-Closed)**:
   - Cương xương `PROFILE_SPECS` (`patch_fast` max_turns=1, `agentic_code` allowlist tools + high reasoning, `arch_audit` max_turns=8 + xhigh).
   - Xóa bỏ hoàn toàn phán quyết `APPROVE` giả lập khi worker chỉ xuất `AnchorPatchPayload`; thay thế bằng `verdict: HANDOFF`.
   - Dọn dẹp tiến trình con với `_terminate_proc_tree(proc)` qua process group `killpg` với `SIGTERM` / `SIGKILL` và hai lần `wait()`.
   - Cách ly `candidate_session_id` khi fallback model; thu hẹp phạm vi `_SYNC_MUTEX` trong `run_sync_cycle`.
   - Cơ chế Fail-Closed trong `discover_package_topology`: khi phát hiện chu trình, lập tức hoàn nguyên về `DEFAULT_PACKAGE_TOPOLOGY_ORDER`.
   - Thêm retry backoff trong `atomic_write_text` chống race condition khóa tệp trên Windows.

2. **PR #489 (Level-2.5 Multi-Agent Co-Review Orchestration & Consensus Engine)**:
   - Bảng bậc ưu tiên phán quyết toàn diện `VERDICT_LATTICE_RANK` bao phủ 100% 11 tokens của `VerdictType`.
   - Thuật toán đồng thuận tất định `synthesize_verdicts`: hợp nhất rủi ro `risk_score = max(...)`, nâng hạng phán quyết Pass lên `APPROVE_WITH_CONDITIONS` nếu có điều kiện `blocking=True` hoặc `risk_score >= 4`.
   - Hợp nhất điều kiện dedup mô tả bằng phép OR logic (`blocking = c1.blocking or c2.blocking`) và gắn mác nguồn `source_profiles`.
   - Hợp đồng Quorum (`expected_profiles`, `completed_profiles`, `failed_profiles`), profile thất bại lập tức chuyển về `HANDOFF`.
   - Phân lập môi trường thực thi bằng `tempfile.TemporaryDirectory()` với phân quyền `0700` nằm ngoài cây `.md/peer_exchange/` chống watcher loop.
   - Schema `CombinedTelemetry` lưu breakdown chi tiết từng profile, phân tách `wall_seconds` và `sum_agent_seconds`.
   - CLI `ccba-harness peer-co-review` với các mã thoát có cấu trúc (0, 2, 3, 4, 5, 1).
   - Gia cố `ccba-maskara` loại trừ false positive cho các biến LLM token metrics.

---

## 📋 Trọng Tâm Đánh Giá Chuyên Biệt Theo Từng Profile

### A. Dành Cho Profile `code_review`:
- Thẩm định độ an toàn trong xử lý lỗi, ngoại lệ (`try...finally`, `rollback_errors`).
- Đánh giá khả năng rò rỉ tài nguyên, thread pool cleanup, zombie processes.
- Kiểm tra tính đúng đắn của logic hợp nhất conditions, gộp cờ blocking bằng phép OR.
- Phát hiện bất kỳ edge case nào có thể gây crash hoặc ném ngoại lệ không mong muốn.

### B. Dành Cho Profile `arch_audit`:
- Thẩm định tính tuân thủ bất biến kiến trúc ADR-0063, ADR-0064, ADR-0065.
- Đánh giá sự phân lập ranh giới Seams trong `ccba-harness` và `ccba-maskara`.
- Kiểm tra thuật toán đồng thuận Lattice: liệu có kẽ hở nào làm sai lệch phán quyết hay không?
- Đánh giá tính sẵn sàng của kiến trúc để bước tiếp lên **Level-3 Autonomous Loopback (`--auto-apply`)**.

---

## 💻 3. Toàn Văn Git Diff Của PR #487 & PR #489

```diff
diff --git a/packages/ccba-harness/src/ccba_harness/__init__.py b/packages/ccba-harness/src/ccba_harness/__init__.py
index fc31b4fe..03fdf9b9 100644
--- a/packages/ccba-harness/src/ccba_harness/__init__.py
+++ b/packages/ccba-harness/src/ccba_harness/__init__.py
@@ -35,6 +35,7 @@
 )
 from .cli import (
     run_apply_anchor_patch_cli,
+    run_peer_co_review_cli,
     run_peer_dispatch_cli,
 )
 from .dashboard import (
@@ -153,8 +154,10 @@
 from .peer import (
     PROFILE_SPECS,
     TIER_DEFAULT_MODELS,
+    VERDICT_LATTICE_RANK,
     AgentIdentity,
     AnchorPatchPayload,
+    CombinedTelemetry,
     CostMode,
     EffortType,
     FileChange,
@@ -162,10 +165,12 @@
     ModelTier,
     PatchReplacement,
     PeerCondition,
+    PeerConsensusReport,
     PeerExecutionProfile,
     PeerPromptEnvelope,
     PeerVerdictBlock,
     PeerVerdictTelemetry,
+    ProfileTelemetryItem,
     RequestType,
     VerdictType,
     apply_anchor_patch,
@@ -178,14 +183,17 @@
     extract_grok_session_telemetry,
     flush_pending_peer_triggers,
     invoke_grok_cli,
+    orchestrate_peer_co_review,
     parse_envelope_from_md,
     parse_verdict_from_md,
     publish_peer_message,
+    render_consensus_report_markdown,
     render_prompt_header,
     render_verdict_header,
     run_sync_cycle,
     safe_read_and_hash,
     scan_peer_exchange,
+    synthesize_verdicts,
 )
 from .peer_gate import (
     GateCheck,
@@ -428,5 +436,13 @@
     "run_implementation_gate",
     "write_verdict_file",
     "run_apply_anchor_patch_cli",
+    "run_peer_co_review_cli",
     "run_peer_dispatch_cli",
+    "CombinedTelemetry",
+    "PeerConsensusReport",
+    "ProfileTelemetryItem",
+    "VERDICT_LATTICE_RANK",
+    "orchestrate_peer_co_review",
+    "render_consensus_report_markdown",
+    "synthesize_verdicts",
 ]
diff --git a/packages/ccba-harness/src/ccba_harness/cli.py b/packages/ccba-harness/src/ccba_harness/cli.py
index 011ff1ac..00c4306f 100644
--- a/packages/ccba-harness/src/ccba_harness/cli.py
+++ b/packages/ccba-harness/src/ccba_harness/cli.py
@@ -1610,6 +1610,135 @@ def run_peer_dispatch_cli(args_list: Sequence[str] | None = None) -> int:
     return 1
 
 
+def run_peer_co_review_cli(args_list: Sequence[str] | None = None) -> int:
+    """CLI entry point for parallel multi-agent co-review orchestration (`ccba-harness peer-co-review` - ADR-0065)."""
+    parser = argparse.ArgumentParser(
+        prog="ccba-harness peer-co-review",
+        description="Parallel Multi-Agent Co-Review Orchestration and Consensus Engine (Level-2.5 / ADR-0065).",
+    )
+    parser.add_argument(
+        "--prompt-file",
+        type=str,
+        required=True,
+        help="Path to markdown prompt file containing PeerPromptEnvelope.",
+    )
+    parser.add_argument(
+        "--profiles",
+        type=str,
+        nargs="+",
+        default=["code_review", "arch_audit"],
+        help="Profiles to dispatch in parallel (default: code_review arch_audit).",
+    )
+    parser.add_argument(
+        "-o",
+        "--output-file",
+        type=str,
+        default=None,
+        help="Path for saving the consolidated consensus markdown report.",
+    )
+    parser.add_argument(
+        "--max-workers",
+        type=int,
+        default=None,
+        help="Hard cap on parallel worker threads.",
+    )
+    parser.add_argument(
+        "--timeout",
+        type=float,
+        default=None,
+        help="Execution timeout override per profile in seconds.",
+    )
+    parser.add_argument(
+        "--worktree",
+        action="store_true",
+        help="Execute agents in isolated git worktrees.",
+    )
+    parser.add_argument(
+        "--dry-run",
+        action="store_true",
+        help="Print planned co-review dispatch plan and exit without executing.",
+    )
+    parser.add_argument(
+        "--json",
+        action="store_true",
+        help="Output consensus report as JSON to stdout.",
+    )
+
+    args = parser.parse_args(args_list)
+    prompt_path = Path(args.prompt_file).resolve()
+    if not prompt_path.exists():
+        print(f"[FAIL] Prompt file not found: {prompt_path}", file=sys.stderr)
+        return 1
+
+    from .peer import (
+        PROFILE_SPECS,
+        orchestrate_peer_co_review,
+        parse_envelope_from_md,
+        safe_read_and_hash,
+    )
+
+    if args.dry_run:
+        content, _ = safe_read_and_hash(prompt_path)
+        envelope = parse_envelope_from_md(content or "")
+        req_id = envelope.request_id if envelope else "unknown"
+        print(f"[DRY-RUN] Request ID: {req_id}")
+        print(f"[DRY-RUN] Profiles: {', '.join(args.profiles)}")
+        for p in args.profiles:
+            spec = PROFILE_SPECS.get(p, {})
+            model = spec.get("model", "unknown")
+            timeout = args.timeout if args.timeout is not None else spec.get("timeout", 180.0)
+            print(f"  - Profile: {p:12s} | Model: {model:20s} | Timeout: {timeout}s")
+        out_target = (
+            Path(args.output_file)
+            if args.output_file
+            else prompt_path.parent / f"grok_consensus_{prompt_path.stem.replace('prompt_', '')}.md"
+        )
+        print(f"[DRY-RUN] Consensus Output: {out_target}")
+        return 0
+
+    output_path = Path(args.output_file).resolve() if args.output_file else None
+    report = orchestrate_peer_co_review(
+        prompt_path=prompt_path,
+        profiles=args.profiles,
+        output_file=output_path,
+        max_workers=args.max_workers,
+        timeout=args.timeout,
+        worktree=args.worktree,
+    )
+
+    if report is None:
+        print(
+            "[FAIL] Failed to orchestrate peer co-review: prompt is unreadable.",
+            file=sys.stderr,
+        )
+        return 1
+
+    if args.json:
+        print(report.model_dump_json(indent=2))
+    else:
+        print(f"[OK] Consensus Verdict: {report.verdict} (Risk: {report.risk_score}/5)")
+        print(
+            f"Quorum: {len(report.completed_profiles)}/{len(report.expected_profiles)} completed."
+        )
+        if report.conditions:
+            print(f"Conditions ({len(report.conditions)}):")
+            for c in report.conditions:
+                tag = "[BLOCKING]" if c.blocking else "[ADVISORY]"
+                print(f"  - {c.id} {tag}: {c.description}")
+
+    if report.verdict in ("APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS"):
+        return 0
+    if report.verdict in ("APPROVE_WITH_CONDITIONS", "APPROVE_WITH_RESERVATIONS"):
+        return 2
+    if report.verdict == "REVISE_PLAN":
+        return 3
+    if report.verdict in ("REJECT", "REJECT_PLAN", "GATE_FAIL"):
+        return 4
+    if report.verdict == "HANDOFF":
+        return 5
+    return 1
+
+
 def run_apply_anchor_patch_cli(args_list: Sequence[str] | None = None) -> int:
     """CLI entry point for applying anchor patches (`ccba-harness apply-anchor-patch` - ADR-0063)."""
     parser = argparse.ArgumentParser(
@@ -2185,6 +2314,8 @@ def main(argv: Sequence[str] | None = None) -> int:
         return run_peer_watch_cli(argv[1:])
     if argv[0] in ("peer-dispatch", "dispatch-peer"):
         return run_peer_dispatch_cli(argv[1:])
+    if argv[0] in ("peer-co-review", "co-review"):
+        return run_peer_co_review_cli(argv[1:])
     if argv[0] in ("apply-anchor-patch", "peer-apply", "apply-patch"):
         return run_apply_anchor_patch_cli(argv[1:])
     if argv[0] == "blast-radius":
@@ -2212,6 +2343,8 @@ def main(argv: Sequence[str] | None = None) -> int:
         return run_peer_watch_cli(argv[1:])
     if parsed.subcommand in ("peer-dispatch", "dispatch-peer"):
         return run_peer_dispatch_cli(argv[1:])
+    if parsed.subcommand in ("peer-co-review", "co-review"):
+        return run_peer_co_review_cli(argv[1:])
     if parsed.subcommand in ("apply-anchor-patch", "peer-apply", "apply-patch"):
         return run_apply_anchor_patch_cli(argv[1:])
     if parsed.subcommand == "blast-radius":
diff --git a/packages/ccba-harness/src/ccba_harness/peer.py b/packages/ccba-harness/src/ccba_harness/peer.py
index d6f040bf..c329fd23 100644
--- a/packages/ccba-harness/src/ccba_harness/peer.py
+++ b/packages/ccba-harness/src/ccba_harness/peer.py
@@ -11,12 +11,15 @@
 import json
 import os
 import re
+import signal
 import subprocess
+import sys
 import tempfile
 import threading
 import time
 import uuid
-from collections.abc import Callable
+from collections.abc import Callable, Sequence
+from concurrent.futures import ThreadPoolExecutor
 from pathlib import Path
 from typing import Any, Literal, NamedTuple
 
@@ -55,7 +58,28 @@
     "FINAL_ACCEPT",
     "GATE_PASS",
     "GATE_FAIL",
+    "HANDOFF",
 ]
+
+VERDICT_LATTICE_RANK: dict[VerdictType, int] = {
+    # Blocker tokens (highest rank)
+    "REJECT": 100,
+    "REJECT_PLAN": 95,
+    "GATE_FAIL": 90,
+    # Revision required
+    "REVISE_PLAN": 80,
+    # Incomplete review / Handoff
+    "HANDOFF": 70,
+    # Conditional pass
+    "APPROVE_WITH_CONDITIONS": 60,
+    "APPROVE_WITH_RESERVATIONS": 55,
+    # Clean pass tokens
+    "APPROVE_PLAN": 40,
+    "FINAL_ACCEPT": 35,
+    "GATE_PASS": 30,
+    "APPROVE": 20,
+}
+
 EffortType = Literal["XS", "S", "M", "L", "XL"]
 
 DEFAULT_PRIMARY_AUDITOR_MODEL = "grok-4.7"  # ccba:allow-raw-model
@@ -86,15 +110,15 @@
         "model": "grok-4.7-build-fast",  # ccba:allow-raw-model
         "fallback_model": "claude-sonnet-4-6",  # ccba:allow-raw-model
         "max_turns": 8,
-        "tools": None,
-        "disallowed_tools": ["spawn_subagent"],
-        "reasoning_effort": None,
+        "tools": ["read_file", "search_replace", "list_dir"],
+        "disallowed_tools": ["spawn_subagent", "run_terminal_command"],
+        "reasoning_effort": "high",
         "timeout": 600.0,
     },
     "patch_fast": {
         "model": "qwen-local",  # ccba:allow-raw-model
         "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
-        "max_turns": None,
+        "max_turns": 1,
         "tools": None,
         "disallowed_tools": [
             "read_file",
@@ -216,6 +240,8 @@ class PeerCondition(BaseModel):
     id: str
     description: str
     blocking: bool = True
+    source_profile: str | None = None
+    source_profiles: list[str] = Field(default_factory=list)
 
 
 CostMode = Literal["exact", "estimated", "unknown"]
@@ -248,7 +274,7 @@ class PeerVerdictBlock(BaseModel):
     request_id: str
     verdict: VerdictType
     conditions: list[PeerCondition] = Field(default_factory=list)
-    risk_score: int | None = None
+    risk_score: int | None = Field(default=None, ge=1, le=5)
     effort: EffortType | None = None
     summary: str = ""
     telemetry: PeerVerdictTelemetry | None = None
@@ -269,6 +295,58 @@ def _normalize_conditions(cls, v: Any) -> list[Any]:
         return normalized
 
 
+class ProfileTelemetryItem(BaseModel):
+    """Telemetry breakdown item for a single peer agent profile (ADR-0065)."""
+
+    model_config = ConfigDict(extra="ignore")
+
+    model: str
+    input_tokens: int = 0
+    output_tokens: int = 0
+    reasoning_tokens: int = 0
+    cached_read_tokens: int = 0
+    total_tokens: int = 0
+    cost_usd: float = 0.0
+    duration_seconds: float = 0.0
+
+
+class CombinedTelemetry(BaseModel):
+    """Consolidated telemetry aggregated across multi-agent executions (ADR-0065)."""
+
+    model_config = ConfigDict(extra="ignore")
+
+    total_tokens: int = 0
+    input_tokens: int = 0
+    output_tokens: int = 0
+    reasoning_tokens: int = 0
+    cached_read_tokens: int = 0
+    cost_usd: float = 0.0
+    wall_seconds: float = 0.0
+    sum_agent_seconds: float = 0.0
+    cost_mode: CostMode = "exact"
+    profile_breakdown: dict[str, ProfileTelemetryItem] = Field(default_factory=dict)
+
+
+class PeerConsensusReport(BaseModel):
+    """Aggregated consensus report synthesized from multi-agent peer reviews (ADR-0065)."""
+
+    model_config = ConfigDict(extra="ignore")
+
+    request_id: str
+    verdict: VerdictType
+    risk_score: int = Field(default=1, ge=1, le=5)
+    summary: str
+    expected_profiles: list[str]
+    completed_profiles: list[str]
+    failed_profiles: list[str] = Field(default_factory=list)
+    individual_verdicts: dict[str, PeerVerdictBlock] = Field(default_factory=dict)
+    conditions: list[PeerCondition] = Field(default_factory=list)
+    combined_telemetry: CombinedTelemetry | None = None
+    created_at: str = Field(
+        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
+    )
+
+
 def extract_frontmatter(md_content: str) -> tuple[dict[str, Any] | None, str]:
     """Extracts raw YAML frontmatter dictionary and remaining body from markdown content.
 
@@ -384,12 +462,13 @@ def flush_pending_peer_triggers(timeout: float = 5.0) -> None:
     _PENDING_THREADS.clear()
 
 
-def atomic_write_text(target: Path, content: str) -> None:
-    """Writes text content to target file atomically using a temporary file (Grok C2).
+def atomic_write_text(target: Path, content: str, max_retries: int = 3) -> None:
+    """Writes text content to target file atomically using a temporary file with retry (ADR-0063 / ADR-0065).
 
     Args:
         target: Destination file path.
         content: Text string content to persist.
+        max_retries: Retry attempts on transient OS lock errors (e.g. Windows file locking).
     """
     target.parent.mkdir(parents=True, exist_ok=True)
     temp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{time.time_ns()}")
@@ -406,7 +485,14 @@ def atomic_write_text(target: Path, content: str) -> None:
                 os.chmod(temp_file, mode)
             except OSError:
                 pass
-        temp_file.replace(target)
+        for attempt in range(max_retries):
+            try:
+                temp_file.replace(target)
+                break
+            except (PermissionError, OSError):
+                if attempt == max_retries - 1:
+                    raise
+                time.sleep(0.05 * (attempt + 1))
     except Exception:
         if temp_file.exists():
             temp_file.unlink(missing_ok=True)
@@ -685,8 +771,7 @@ def update_live_summary(
         pending_anti: List of file names pending for Antigravity.
         pending_grok: List of file names pending for Grok.
     """
-    tz = datetime.timezone(datetime.timedelta(hours=7))
-    now_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
+    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
     resps = [
         i
         for i in registry.values()
@@ -696,7 +781,7 @@ def update_live_summary(
 
     lines = [
         "# ⚡ Grok & Antigravity Live Peer Summary\n",
-        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0007)\n\n",
+        f"> **Thời điểm cập nhật**: `{now_iso}` | **Cơ chế**: Delta SHA-256 Bridge (ADR-0063)\n\n",
         "## 1. Trạng Thái Vận Hành\n",
         f"- **Antigravity**: `{'waiting_for_grok' if pending_grok else 'idle'}` (Đang chờ Grok: {len(pending_grok)} requests)",
         f"- **Grok**: `{'in_progress' if pending_grok else 'idle'}` (Đang chờ Antigravity: {len(pending_anti)} requests)\n\n",
@@ -709,8 +794,8 @@ def update_live_summary(
         lines.append(f"- `{p}`")
     if pending_anti:
         lines.append("\n### ⏳ Antigravity cần xử lý:")
-        for p in pending_anti[:5]:
-            lines.append(f"- `{p}`")
+    for p in pending_anti[:5]:
+        lines.append(f"- `{p}`")
 
     lines.extend(
         [
@@ -725,7 +810,9 @@ def update_live_summary(
             f"| `{item['path'].name}` | **`{v.verdict}`** | {len(v.conditions)} | {v.summary[:50]}... |"
         )
 
-    atomic_write_text(summary_file, "\n".join(lines) + "\n")
+    lock_path = summary_file.with_name(f"{summary_file.name}.lock")
+    with FileMutexLock(lock_path, timeout=5.0):
+        atomic_write_text(summary_file, "\n".join(lines) + "\n")
 
 
 def run_sync_cycle(
@@ -743,6 +830,10 @@ def run_sync_cycle(
     Returns:
         List of detected file changes in this cycle.
     """
+    actions_to_run: list[tuple[str, Path]] = []
+    changes: list[FileChange] = []
+
+    # COND-01: Narrow _SYNC_MUTEX to the critical section (cache, status, summary updates)
     with _SYNC_MUTEX:
         cache_file = peer_exchange_dir / ".bridge_cache.json"
         status_file = peer_exchange_dir / "status.json"
@@ -759,14 +850,21 @@ def run_sync_cycle(
 
             for change in changes:
                 if auto_grok and change.role == "PROMPT_TO_GROK":
-                    invoke_grok_cli(change.path)
+                    actions_to_run.append(("grok", change.path))
                 elif auto_gate and change.role == "GROK_IMPLEMENTATION":
-                    from .peer_gate import run_full_gate, write_verdict_file
+                    actions_to_run.append(("gate", change.path))
 
-                    result = run_full_gate(peer_exchange_dir.parent.parent)
-                    write_verdict_file(result, peer_exchange_dir)
+    # Long-running subprocesses execute OUTSIDE _SYNC_MUTEX (COND-01 / ADR-0065)
+    for action_type, path in actions_to_run:
+        if action_type == "grok":
+            invoke_grok_cli(path)
+        elif action_type == "gate":
+            from .peer_gate import run_full_gate, write_verdict_file
 
-        return changes
+            result = run_full_gate(peer_exchange_dir.parent.parent)
+            write_verdict_file(result, peer_exchange_dir)
+
+    return changes
 
 
 def publish_peer_message(
@@ -1107,6 +1205,34 @@ def build_grok_cmd(
     return cmd
 
 
+def _terminate_proc_tree(proc: subprocess.Popen[Any]) -> None:
+    """Terminates a process and its child process group safely (COND-03 / ADR-0065)."""
+    pid = proc.pid
+    try:
+        if hasattr(os, "killpg") and hasattr(os, "getpgid"):
+            try:
+                pgid = os.getpgid(pid)
+                os.killpg(pgid, signal.SIGTERM)
+            except OSError:
+                proc.terminate()
+        else:
+            proc.terminate()
+        proc.wait(timeout=2.0)
+    except Exception:
+        try:
+            if hasattr(os, "killpg") and hasattr(os, "getpgid"):
+                try:
+                    pgid = os.getpgid(pid)
+                    os.killpg(pgid, signal.SIGKILL)
+                except OSError:
+                    proc.kill()
+            else:
+                proc.kill()
+            proc.wait(timeout=2.0)
+        except Exception:
+            pass
+
+
 def _run_single_grok_attempt(
     cmd: list[str],
     prompt_path: Path,
@@ -1115,7 +1241,7 @@ def _run_single_grok_attempt(
     session_id: str | None = None,
     candidate_model: str = "unknown",
 ) -> bool:
-    """Executes a single invocation of grok CLI and verifies output verdict (ADR-0064).
+    """Executes a single invocation of grok CLI and verifies output verdict (ADR-0064 / ADR-0065).
 
     Args:
         cmd: Command arguments list to execute.
@@ -1134,15 +1260,17 @@ def _run_single_grok_attempt(
             tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_out,
             tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as temp_err,
         ):
-            proc = subprocess.Popen(
-                cmd,
-                stdout=temp_out,
-                stderr=temp_err,
-                stdin=subprocess.DEVNULL,
-                text=True,
-                encoding="utf-8",
-                errors="replace",
-            )
+            popen_kwargs: dict[str, Any] = {
+                "stdout": temp_out,
+                "stderr": temp_err,
+                "stdin": subprocess.DEVNULL,
+                "text": True,
+                "encoding": "utf-8",
+                "errors": "replace",
+            }
+            if sys.platform != "win32":
+                popen_kwargs["start_new_session"] = True
+            proc = subprocess.Popen(cmd, **popen_kwargs)
             deadline = start_time + timeout
             stdout_text = ""
             while time.time() < deadline:
@@ -1163,28 +1291,27 @@ def _run_single_grok_attempt(
                         parse_verdict_from_md(content) or extract_anchor_payload(content)
                     ):
                         stdout_text = content
-                        try:
-                            proc.terminate()
-                            proc.wait(timeout=2.0)
-                        except Exception:
-                            proc.kill()
+                        _terminate_proc_tree(proc)
                         break
 
                 time.sleep(1.0)
             else:
-                try:
-                    proc.terminate()
-                    proc.wait(timeout=2.0)
-                except Exception:
-                    proc.kill()
+                _terminate_proc_tree(proc)
                 return False
 
         if (not stdout_text.strip() or parse_verdict_from_md(stdout_text) is None) and session_id:
             try:
                 session_root = Path.home() / ".grok" / "sessions"
+                max_bytes = 2 * 1024 * 1024
                 for p in session_root.glob(f"**/{session_id}/chat_history.jsonl"):
                     if p.exists():
-                        for line in reversed(p.read_text(encoding="utf-8").splitlines()):
+                        file_size = p.stat().st_size
+                        with p.open("r", encoding="utf-8", errors="replace") as f:
+                            if file_size > max_bytes:
+                                f.seek(file_size - max_bytes)
+                                f.readline()
+                            lines = f.readlines()
+                        for line in reversed(lines):
                             if line.strip():
                                 d = json.loads(line)
                                 if d.get("type") == "assistant" and d.get("content"):
@@ -1208,10 +1335,11 @@ def _run_single_grok_attempt(
                 prompt_content, _ = safe_read_and_hash(prompt_path)
                 envelope = parse_envelope_from_md(prompt_content or "")
                 req_id = envelope.request_id if envelope else "req-auto"
+                # COND-02: Never fabricate synthetic APPROVE from anchor patch alone
                 verdict = PeerVerdictBlock(
                     request_id=req_id,
-                    verdict="APPROVE",
-                    summary="Fast-path anchor patch generated successfully.",
+                    verdict="HANDOFF",
+                    summary="Fast-path anchor patch generated; pending orchestrator apply and verification.",
                 )
                 stdout_text = render_verdict_header(verdict) + "\n" + stdout_text.lstrip()
             else:
@@ -1313,8 +1441,8 @@ def invoke_grok_cli(
         if fallback and fallback not in target_models:
             target_models.append(fallback)
 
-    session_id = str(uuid.uuid4())
     for candidate in target_models:
+        candidate_session_id = str(uuid.uuid4())
         cmd = build_grok_cmd(
             prompt_path=prompt_path,
             model=candidate,
@@ -1324,7 +1452,7 @@ def invoke_grok_cli(
             deny=deny,
             reasoning_effort=reasoning_effort,
             worktree=worktree,
-            session_id=session_id,
+            session_id=candidate_session_id,
             system_prompt=system_prompt,
         )
         if _run_single_grok_attempt(
@@ -1332,8 +1460,351 @@ def invoke_grok_cli(
             prompt_path,
             output_file,
             spec_timeout,
-            session_id=session_id,
+            session_id=candidate_session_id,
             candidate_model=candidate,
         ):
             return True
     return False
+
+
+def synthesize_verdicts(
+    request_id: str,
+    verdicts: dict[str, PeerVerdictBlock],
+    expected_profiles: Sequence[str] | None = None,
+    duration_seconds: float = 0.0,
+) -> PeerConsensusReport:
+    """Synthesizes multiple peer verdicts into a unified deterministic consensus report (ADR-0065).
+
+    Args:
+        request_id: Request identifier matching the prompt.
+        verdicts: Mapping of profile name to PeerVerdictBlock.
+        expected_profiles: Optional expected profiles list for quorum enforcement.
+        duration_seconds: Execution wall-clock duration in seconds.
+
+    Returns:
+        PeerConsensusReport with synthesized verdict, conditions, and telemetry.
+    """
+    if not verdicts and not expected_profiles:
+        raise ValueError(
+            "Cannot synthesize consensus from empty verdicts and empty expected profiles."
+        )
+
+    exp_profiles = (
+        list(expected_profiles) if expected_profiles is not None else list(verdicts.keys())
+    )
+    comp_profiles = [p for p in exp_profiles if p in verdicts]
+    failed_profiles = [p for p in exp_profiles if p not in verdicts]
+
+    blocker_verdicts: set[VerdictType] = {"REJECT", "REJECT_PLAN", "GATE_FAIL"}
+    pass_verdicts: set[VerdictType] = {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS"}
+
+    # 1. Determine baseline consensus verdict by strict lattice rank
+    if failed_profiles:
+        comp_blockers = [
+            verdicts[p].verdict for p in comp_profiles if verdicts[p].verdict in blocker_verdicts
+        ]
+        if comp_blockers:
+            consensus_verdict: VerdictType = max(
+                comp_blockers, key=lambda t: VERDICT_LATTICE_RANK.get(t, 0)
+            )
+        else:
+            consensus_verdict = "HANDOFF"
+    else:
+        completed_verdicts = [verdicts[p].verdict for p in comp_profiles]
+        if not completed_verdicts:
+            consensus_verdict = "HANDOFF"
+        elif len(set(completed_verdicts)) == 1:
+            consensus_verdict = completed_verdicts[0]
+        else:
+            consensus_verdict = max(
+                completed_verdicts, key=lambda t: VERDICT_LATTICE_RANK.get(t, 0)
+            )
+
+    # 2. Consolidate conditions with deterministic ordering & OR-merge on blocking
+    consolidated_conds: list[PeerCondition] = []
+    seen_cond_descs: dict[str, PeerCondition] = {}
+
+    for prof in comp_profiles:
+        vb = verdicts[prof]
+        for cond in vb.conditions:
+            key = cond.description.strip().lower()
+            if key in seen_cond_descs:
+                existing = seen_cond_descs[key]
+                existing.blocking = existing.blocking or cond.blocking
+                if prof not in existing.source_profiles:
+                    existing.source_profiles.append(prof)
+            else:
+                new_cond = PeerCondition(
+                    id=cond.id,
+                    description=cond.description,
+                    blocking=cond.blocking,
+                    source_profile=prof,
+                    source_profiles=[prof],
+                )
+                seen_cond_descs[key] = new_cond
+                consolidated_conds.append(new_cond)
+
+    if failed_profiles:
+        fail_cond = PeerCondition(
+            id="COND-QUORUM-FAIL",
+            description=f"Missing peer review from profiles: {', '.join(failed_profiles)}",
+            blocking=True,
+            source_profile="orchestrator",
+            source_profiles=["orchestrator"],
+        )
+        consolidated_conds.append(fail_cond)
+
+    # 3. Dynamic escalation: blocking conditions or risk_score >= 4 upgrade PASS to APPROVE_WITH_CONDITIONS
+    has_blocking = any(c.blocking for c in consolidated_conds)
+    if consensus_verdict in pass_verdicts and has_blocking:
+        consensus_verdict = "APPROVE_WITH_CONDITIONS"
+
+    valid_risks = [
+        verdicts[p].risk_score for p in comp_profiles if verdicts[p].risk_score is not None
+    ]
+    consensus_risk = max(valid_risks) if valid_risks else 1
+    if consensus_verdict in pass_verdicts and consensus_risk >= 4:
+        consensus_verdict = "APPROVE_WITH_CONDITIONS"
+
+    # 4. Consolidate telemetry breakdown
+    agg_total = 0
+    agg_input = 0
+    agg_output = 0
+    agg_reasoning = 0
+    agg_cached = 0
+    cost_usd = 0.0
+    sum_agent_seconds = 0.0
+    all_exact = True
+    has_any_telemetry = False
+    profile_breakdown: dict[str, ProfileTelemetryItem] = {}
+
+    for prof in comp_profiles:
+        vb = verdicts[prof]
+        tel = vb.telemetry
+        if tel:
+            has_any_telemetry = True
+            agg_total += tel.total_tokens or 0
+            agg_input += tel.input_tokens or 0
+            agg_output += tel.output_tokens or 0
+            agg_reasoning += tel.reasoning_tokens or 0
+            agg_cached += tel.cached_read_tokens or 0
+            cost_usd += tel.cost_usd or 0.0
+            sum_agent_seconds += tel.duration_seconds or 0.0
+            if tel.cost_mode != "exact":
+                all_exact = False
+            item_payload = {
+                "model": tel.primary_model,
+                "input_tokens": tel.input_tokens or 0,
+                "output_tokens": tel.output_tokens or 0,
+                "reasoning_tokens": tel.reasoning_tokens or 0,
+                "cached_read_tokens": tel.cached_read_tokens or 0,
+                "total_tokens": tel.total_tokens or 0,
+                "cost_usd": round(tel.cost_usd or 0.0, 4),
+                "duration_seconds": round(tel.duration_seconds or 0.0, 2),
+            }
+            profile_breakdown[prof] = ProfileTelemetryItem.model_validate(item_payload)
+        else:
+            all_exact = False
+
+    combined_telemetry: CombinedTelemetry | None = None
+    if has_any_telemetry:
+        comb_payload = {
+            "total_tokens": agg_total,
+            "input_tokens": agg_input,
+            "output_tokens": agg_output,
+            "reasoning_tokens": agg_reasoning,
+            "cached_read_tokens": agg_cached,
+            "cost_usd": round(cost_usd, 4),
+            "wall_seconds": round(duration_seconds, 2),
+            "sum_agent_seconds": round(sum_agent_seconds, 2),
+            "cost_mode": "exact" if all_exact else "estimated",
+            "profile_breakdown": profile_breakdown,
+        }
+        combined_telemetry = CombinedTelemetry.model_validate(comb_payload)
+
+    # 5. Build consolidated summary
+    summary_lines = [
+        f"Consensus Verdict: **{consensus_verdict}** (Risk Score: {consensus_risk}/5).",
+        f"Quorum: {len(comp_profiles)}/{len(exp_profiles)} completed.",
+    ]
+    if failed_profiles:
+        summary_lines.append(f"Failed Profiles: {', '.join(failed_profiles)}.")
+    for prof in comp_profiles:
+        vb = verdicts[prof]
+        summary_lines.append(f"- **{prof}** ({vb.verdict}): {vb.summary}")
+    unified_summary = "\n".join(summary_lines)
+
+    return PeerConsensusReport(
+        request_id=request_id,
+        verdict=consensus_verdict,
+        risk_score=consensus_risk,
+        summary=unified_summary,
+        expected_profiles=exp_profiles,
+        completed_profiles=comp_profiles,
+        failed_profiles=failed_profiles,
+        individual_verdicts=verdicts,
+        conditions=consolidated_conds,
+        combined_telemetry=combined_telemetry,
+    )
+
+
+def render_consensus_report_markdown(report: PeerConsensusReport) -> str:
+    """Renders a complete markdown document for a consensus report with standard frontmatter."""
+    fm_payload: dict[str, Any] = {
+        "request_id": report.request_id,
+        "verdict": report.verdict,
+        "risk_score": report.risk_score,
+        "summary": report.summary,
+        "profiles": report.completed_profiles,
+        "expected_profiles": report.expected_profiles,
+        "failed_profiles": report.failed_profiles,
+        "conditions": [c.model_dump(exclude_none=True) for c in report.conditions],
+    }
+    if report.combined_telemetry:
+        fm_payload["telemetry"] = report.combined_telemetry.model_dump(exclude_none=True)
+
+    yaml_str = yaml.dump(fm_payload, sort_keys=False, allow_unicode=True)
+    header = f"---\n{yaml_str}---\n"
+
+    body_lines = [
+        f"# 🤝 Multi-Agent Peer Consensus Report: `{report.request_id}`\n",
+        f"- **Consensus Verdict**: `{report.verdict}`",
+        f"- **Consolidated Risk Score**: `{report.risk_score}/5`",
+        f"- **Quorum**: `{len(report.completed_profiles)}/{len(report.expected_profiles)}` profiles completed\n",
+        "## 1. Executive Summary\n",
+        report.summary,
+        "\n## 2. Consolidated Conditions\n",
+    ]
+    if report.conditions:
+        for c in report.conditions:
+            blocking_tag = "🔴 [BLOCKING]" if c.blocking else "🟡 [ADVISORY]"
+            sources = (
+                ", ".join(c.source_profiles)
+                if c.source_profiles
+                else (c.source_profile or "unknown")
+            )
+            body_lines.append(f"- **{c.id}** {blocking_tag} ({sources}): {c.description}")
+    else:
+        body_lines.append("*(No conditions attached)*")
+
+    body_lines.append("\n## 3. Individual Profile Verdicts\n")
+    for prof, vb in report.individual_verdicts.items():
+        body_lines.append(f"### Profile: `{prof}`")
+        body_lines.append(f"- **Verdict**: `{vb.verdict}` (Risk: `{vb.risk_score or 'N/A'}`)")
+        body_lines.append(f"- **Summary**: {vb.summary}\n")
+
+    if report.combined_telemetry:
+        tel = report.combined_telemetry
+        body_lines.append("## 4. Telemetry & Cost Provenance\n")
+        body_lines.append(
+            f"- **Total Tokens**: {tel.total_tokens:,} (Input: {tel.input_tokens:,}, Output: {tel.output_tokens:,}, Reasoning: {tel.reasoning_tokens:,})"
+        )
+        body_lines.append(f"- **Total Cost**: ${tel.cost_usd:.4f} (mode: `{tel.cost_mode}`)")
+        body_lines.append(
+            f"- **Duration**: Wall clock `{tel.wall_seconds}s` | Sum agent time `{tel.sum_agent_seconds}s`\n"
+        )
+
+    return header + "\n".join(body_lines) + "\n"
+
+
+def orchestrate_peer_co_review(
+    prompt_path: Path,
+    profiles: Sequence[str] = ("code_review", "arch_audit"),
+    output_file: Path | None = None,
+    max_workers: int | None = None,
+    timeout: float | None = None,
+    worktree: bool = False,
+) -> PeerConsensusReport | None:
+    """Orchestrates multi-agent co-review execution in parallel threads with isolated outputs (ADR-0065).
+
+    Args:
+        prompt_path: Path to markdown prompt file containing PeerPromptEnvelope.
+        profiles: Sequence of peer profile names to dispatch.
+        output_file: Path to final consensus markdown file.
+        max_workers: ThreadPoolExecutor worker count cap.
+        timeout: Optional timeout override for agent executions.
+        worktree: Whether to execute agents inside a git worktree.
+
+    Returns:
+        PeerConsensusReport on success, or None if prompt is unreadable.
+    """
+    for prof in profiles:
+        if not re.match(r"^[a-z0-9_]{1,32}$", prof):
+            raise ValueError(f"Invalid profile name '{prof}': must match ^[a-z0-9_]{{1,32}}$")
+
+    content, _ = safe_read_and_hash(prompt_path)
+    envelope = parse_envelope_from_md(content or "")
+    if not envelope:
+        return None
+
+    request_id = envelope.request_id
+
+    # COND-04: Isolated TemporaryDirectory with 0700 permissions outside peer_exchange
+    temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"peer_co_review_{request_id[:8]}_")
+    temp_dir = Path(temp_dir_obj.name)
+    try:
+        try:
+            os.chmod(temp_dir, 0o700)
+        except Exception:
+            pass
+
+        start_time = time.time()
+        tasks: list[tuple[str, Path, Path]] = []
+
+        for prof in profiles:
+            prof_prompt = temp_dir / f"prompt_{prof}.md"
+            prof_out_name = f"grok_{prof}.md"
+            prof_env = envelope.model_copy()
+            prof_env.profile = prof  # type: ignore[assignment]
+            prof_env.output_path = prof_out_name
+            rendered = render_prompt_header(prof_env)
+            _, body = extract_frontmatter(content or "")
+            atomic_write_text(prof_prompt, rendered + body.lstrip())
+            tasks.append((prof, prof_prompt, temp_dir / prof_out_name))
+
+        def _worker(item: tuple[str, Path, Path]) -> tuple[str, PeerVerdictBlock | None]:
+            p_name, p_prompt, p_out = item
+            spec = PROFILE_SPECS.get(p_name, {})
+            p_model = spec.get("model")
+            p_timeout = timeout if timeout is not None else spec.get("timeout")
+            ok = invoke_grok_cli(
+                prompt_path=p_prompt,
+                model=p_model,
+                profile=p_name,
+                timeout=p_timeout,
+                worktree=worktree,
+            )
+            if not ok or not p_out.exists():
+                return p_name, None
+            out_str, _ = safe_read_and_hash(p_out)
+            vb = parse_verdict_from_md(out_str or "")
+            return p_name, vb
+
+        workers_count = max_workers if max_workers is not None else min(len(profiles), 4)
+        verdicts: dict[str, PeerVerdictBlock] = {}
+
+        with ThreadPoolExecutor(max_workers=max(1, workers_count)) as pool:
+            futures = [pool.submit(_worker, t) for t in tasks]
+            for fut in futures:
+                p_name, vb = fut.result()
+                if vb is not None:
+                    verdicts[p_name] = vb
+
+        elapsed = time.time() - start_time
+        report = synthesize_verdicts(
+            request_id=request_id,
+            verdicts=verdicts,
+            expected_profiles=profiles,
+            duration_seconds=elapsed,
+        )
+
+        final_out = output_file
+        if not final_out:
+            stem = prompt_path.stem.replace("prompt_", "")
+            final_out = prompt_path.parent / f"grok_consensus_{stem}.md"
+
+        report_md = render_consensus_report_markdown(report)
+        atomic_write_text(final_out, report_md)
+        return report
+    finally:
+        temp_dir_obj.cleanup()
diff --git a/packages/ccba-maskara/src/ccba_maskara/_scanner.py b/packages/ccba-maskara/src/ccba_maskara/_scanner.py
index 03412da4..2454545c 100644
--- a/packages/ccba-maskara/src/ccba_maskara/_scanner.py
+++ b/packages/ccba-maskara/src/ccba_maskara/_scanner.py
@@ -73,6 +73,21 @@ def is_safe_or_template(val: str, key_hint: str = "") -> bool:
         or "placeholder" in lower
     ):
         return True
+
+    # Ignore Python expressions, type annotations, collections, and LLM token counter metrics
+    key_lower = key_hint.lower()
+    if any(tok in key_lower for tok in ("token", "tokens")) and not any(
+        cred in key_lower
+        for cred in ("api_key", "secret", "password", "passwd", "auth", "credential", "private")
+    ):
+        if (
+            stripped.startswith(("set[", "set(", "list[", "list(", "dict[", "dict(", "[", "(", "{"))
+            or "." in stripped
+            or stripped.endswith(("tokens", "token", "tokens}", "tokens]"))
+            or stripped.isidentifier()
+        ):
+            return True
+
     return False
 
 
diff --git a/scripts/spoke/spoke_bootstrap.py b/scripts/spoke/spoke_bootstrap.py
index 9cdc3310..f7738f38 100644
--- a/scripts/spoke/spoke_bootstrap.py
+++ b/scripts/spoke/spoke_bootstrap.py
@@ -127,13 +127,8 @@ def discover_package_topology(hub_root: Path | None = None) -> list[str]:
                 in_degree[neighbor] -= 1
                 if in_degree[neighbor] == 0 and neighbor not in ordered and neighbor not in zero_in:
                     zero_in.append(neighbor)
-                    zero_in.sort()
-
-        for p in sorted(dep_graph):
-            if p not in ordered:
-                ordered.append(p)
-
-        if not ordered:
+        if len(ordered) < len(dep_graph):
+            # Circular dependency detected! Fail-closed to static default order (ADR-0062 / ADR-0065 COND-04)
             return list(DEFAULT_PACKAGE_TOPOLOGY_ORDER)
 
         return ordered
@@ -141,7 +136,12 @@ def discover_package_topology(hub_root: Path | None = None) -> list[str]:
         return list(DEFAULT_PACKAGE_TOPOLOGY_ORDER)
 
 
-PACKAGE_TOPOLOGY_ORDER = DEFAULT_PACKAGE_TOPOLOGY_ORDER
+def get_package_topology_order(hub_root: Path | None = None) -> list[str]:
+    """Returns the dynamically discovered topological package order (ADR-0062 / ADR-0065)."""
+    return discover_package_topology(hub_root)
+
+
+PACKAGE_TOPOLOGY_ORDER: list[str] = DEFAULT_PACKAGE_TOPOLOGY_ORDER
 
 
 ARCHETYPE_TIER1_DEFAULTS = {

```

---

## 📝 4. Định Dạng Đầu Ra Bắt Buộc (Mandatory Output Format)

Bắt đầu NGAY LẬP TỨC bằng YAML Frontmatter (không có bất kỳ ký tự nào trước dấu `---`):

```yaml
---
request_id: "req-dogfood-co-review-001"
verdict: APPROVE | APPROVE_WITH_CONDITIONS | REJECT
conditions: []
risk_score: 1-5
effort: XS | S | M | L | XL
summary: "Tóm tắt 1-2 câu kết luận thẩm định theo vai trò profile được giao."
---
```

Tiếp theo là phần phân tích kỹ thuật chi tiết theo các tiêu chí trọng tâm của profile.
