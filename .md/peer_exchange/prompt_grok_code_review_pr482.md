---
request_id: "req-code-review-pr482-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "code_review"
subject: "Peer Code Review PR #482: CLI apply-anchor-patch và Transactional Rollback"
timestamp: "2026-10-05T21:36:00+07:00"
source_documents: []
output_path: ".md/peer_exchange/grok_code_review_pr482.md"
context: "Thẩm định chất lượng mã nguồn PR #482 đối chiếu theo 10 Bugbot Invariants (.github/bugbot-rules.md) và chuẩn mực kỹ thuật CCBA."
---

# 🔍 Yêu Cầu Peer Code Review: Pull Request #482

> ⚠️ **Chỉ Dẫn Cho Reviewer**: Toàn bộ diff logic cốt lõi của PR #482 đã được đính kèm trực tiếp dưới đây. Bạn **KHÔNG CẦN** gọi các công cụ đọc đĩa tốn lượt (, ). Hãy tiến hành rà soát kỹ thuật đối kháng và xuất ngay báo cáo thẩm định mã nguồn kèm khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra!

## 1. Mục Tiêu Của PR #482
PR #482 hoàn thiện giao thức Level-2 Peer Delegation (ADR-0063 / ADR-0064):
- Tích hợp CLI `ccba-harness apply-anchor-patch` (aliases: `peer-apply`, `apply-patch`) với hỗ trợ `-f -` (stdin piping), `--root`, `--dry-run`, `--backup` (`.bak`), `--quiet`, và `--json`.
- Đảm bảo tính nguyên tử giao dịch (ACID):
  - Phase 1: Chặn Path Traversal, chặn trùng lặp file đích (`target_files_seen`), chuẩn hóa CRLF `
` $	o$ LF `
`.
  - Phase 2: Transactional Rollback tự động phục hồi đĩa qua `written_backups` nếu phát sinh ngoại lệ ghi.
- Mở rộng Profiles `code_review` và `arch_audit`.
- Bóc tách frontmatter mềm dẻo khi có markdown fence.

## 2. Tiêu Chí Đánh Giá (10 Bugbot Invariants & CCBA Standards)
1. **Toàn Vẹn & Khôi Phục Giao Dịch (Transactional Rollback)**: Có kẽ hở nào khiến rollback thất bại hoặc rò rỉ trạng thái dở dang không?
2. **An Toàn Hệ Thống Tệp (Filesystem & Path Traversal)**: `is_relative_to` và xử lý đường dẫn tuyệt đối/tương đối có lỗ hổng nào không?
3. **Chuẩn Hóa Đa Nền Tảng (Cross-OS & CRLF)**: Việc chuẩn hóa newline có ảnh hưởng ngược đến file nhị phân hoặc logic khác không?
4. **Xử Lý Lỗi (Exception Handling)**: Có sử dụng bare except không? Thông báo lỗi có rõ ràng không?
5. **Giao Diện CLI & Usability**: Các cờ CLI và cơ chế stdin piping có đúng chuẩn Unix conventions không?

## 3. Toàn Văn Git Diff Của PR #482 (`packages/ccba-harness/src/`)

```diff
diff --git a/packages/ccba-harness/src/ccba_harness/__init__.py b/packages/ccba-harness/src/ccba_harness/__init__.py
index 791ed70c..dd193eef 100644
--- a/packages/ccba-harness/src/ccba_harness/__init__.py
+++ b/packages/ccba-harness/src/ccba_harness/__init__.py
@@ -33,6 +33,10 @@
     extract_ast_references,
     recommend_tests,
 )
+from .cli import (
+    run_apply_anchor_patch_cli,
+    run_peer_dispatch_cli,
+)
 from .dashboard import (
     generate_swarm_dashboard_html,
     render_swarm_dashboard,
@@ -419,4 +423,6 @@
     "print_summary_table",
     "run_full_gate",
     "write_verdict_file",
+    "run_apply_anchor_patch_cli",
+    "run_peer_dispatch_cli",
 ]
diff --git a/packages/ccba-harness/src/ccba_harness/cli.py b/packages/ccba-harness/src/ccba_harness/cli.py
index eb8af307..011ff1ac 100644
--- a/packages/ccba-harness/src/ccba_harness/cli.py
+++ b/packages/ccba-harness/src/ccba_harness/cli.py
@@ -1481,9 +1481,9 @@ def run_peer_dispatch_cli(args_list: Sequence[str] | None = None) -> int:
     parser.add_argument(
         "--profile",
         type=str,
-        choices=["audit_plan", "agentic_code", "patch_fast"],
+        choices=["audit_plan", "agentic_code", "patch_fast", "code_review", "arch_audit"],
         default=None,
-        help="Execution profile ('audit_plan', 'agentic_code', 'patch_fast').",
+        help="Execution profile ('audit_plan', 'agentic_code', 'patch_fast', 'code_review', 'arch_audit').",
     )
     parser.add_argument(
         "--tier",
@@ -1610,6 +1610,115 @@ def run_peer_dispatch_cli(args_list: Sequence[str] | None = None) -> int:
     return 1
 
 
+def run_apply_anchor_patch_cli(args_list: Sequence[str] | None = None) -> int:
+    """CLI entry point for applying anchor patches (`ccba-harness apply-anchor-patch` - ADR-0063)."""
+    parser = argparse.ArgumentParser(
+        prog="ccba-harness apply-anchor-patch",
+        description="Apply Level-2 anchor patches with two-phase commit and transactional rollback (ADR-0063).",
+    )
+    parser.add_argument(
+        "--patch-file",
+        "-f",
+        type=str,
+        required=True,
+        help="Path to patch markdown/JSON file, or '-' to read from standard input.",
+    )
+    parser.add_argument(
+        "--root",
+        "-r",
+        type=str,
+        default=None,
+        help="Project workspace root directory (default: current working directory).",
+    )
+    parser.add_argument(
+        "--dry-run",
+        action="store_true",
+        help="Validate patch integrity and check target anchors without writing changes to disk.",
+    )
+    parser.add_argument(
+        "--backup",
+        action="store_true",
+        help="Create .bak backups before overwriting target files.",
+    )
+    parser.add_argument(
+        "--quiet",
+        "-q",
+        action="store_true",
+        help="Suppress informational stdout output (only errors will be emitted).",
+    )
+    parser.add_argument(
+        "--json",
+        action="store_true",
+        help="Output structured JSON results instead of human-readable text.",
+    )
+
+    args = parser.parse_args(args_list)
+
+    if args.patch_file == "-":
+        raw_content = sys.stdin.read()
+    else:
+        patch_path = Path(args.patch_file).resolve()
+        if not patch_path.exists():
+            err_msg = f"Patch file not found: {patch_path}"
+            if args.json:
+                print(json.dumps({"status": "ERROR", "error": err_msg}))
+            else:
+                print(f"[FAIL] {err_msg}", file=sys.stderr)
+            return 1
+        raw_content = patch_path.read_text(encoding="utf-8")
+
+    from .peer import apply_anchor_patch, extract_anchor_payload
+
+    payload = extract_anchor_payload(raw_content)
+    if payload is None:
+        err_msg = "No valid AnchorPatchPayload found in input"
+        if args.json:
+            print(json.dumps({"status": "ERROR", "error": err_msg}))
+        else:
+            print(f"[FAIL] {err_msg}", file=sys.stderr)
+        return 1
+
+    root_path = Path(args.root).resolve() if args.root else Path.cwd()
+    try:
+        modified_paths = apply_anchor_patch(
+            root=root_path,
+            payload=payload,
+            dry_run=args.dry_run,
+            backup=args.backup,
+        )
+    except Exception as exc:
+        if args.json:
+            print(json.dumps({"status": "ERROR", "error": str(exc)}))
+        else:
+            print(f"[FAIL] Failed to apply anchor patch: {exc}", file=sys.stderr)
+        return 1
+
+    rel_paths = [
+        str(p.relative_to(root_path)) if p.is_relative_to(root_path) else str(p)
+        for p in modified_paths
+    ]
+    status_label = "DRY_RUN_OK" if args.dry_run else "APPLIED"
+
+    if args.json:
+        print(
+            json.dumps(
+                {
+                    "status": status_label,
+                    "count": len(rel_paths),
+                    "files": rel_paths,
+                    "dry_run": args.dry_run,
+                }
+            )
+        )
+    elif not args.quiet:
+        action_verb = "Validated" if args.dry_run else "Successfully applied"
+        print(f"[OK] {action_verb} {len(rel_paths)} file(s):")
+        for f in rel_paths:
+            print(f"  - {f}")
+
+    return 0
+
+
 def main(argv: Sequence[str] | None = None) -> int:
     """Main CLI entry point for ccba-harness."""
     if argv is None:
@@ -1970,9 +2079,9 @@ def main(argv: Sequence[str] | None = None) -> int:
     dispatch_parser.add_argument(
         "--profile",
         type=str,
-        choices=["audit_plan", "agentic_code", "patch_fast"],
+        choices=["audit_plan", "agentic_code", "patch_fast", "code_review", "arch_audit"],
         default=None,
-        help="Execution profile ('audit_plan', 'agentic_code', 'patch_fast').",
+        help="Execution profile ('audit_plan', 'agentic_code', 'patch_fast', 'code_review', 'arch_audit').",
     )
     dispatch_parser.add_argument(
         "--tier",
@@ -2011,6 +2120,48 @@ def main(argv: Sequence[str] | None = None) -> int:
         help="Print constructed command without executing.",
     )
 
+    # Subcommand: apply-anchor-patch
+    apply_patch_parser = subparsers.add_parser(
+        "apply-anchor-patch",
+        aliases=["peer-apply", "apply-patch"],
+        help="Apply Level-2 anchor patches with two-phase commit and transactional rollback (ADR-0063).",
+    )
+    apply_patch_parser.add_argument(
+        "--patch-file",
+        "-f",
+        type=str,
+        required=True,
+        help="Path to patch markdown/JSON file, or '-' to read from standard input.",
+    )
+    apply_patch_parser.add_argument(
+        "--root",
+        "-r",
+        type=str,
+        default=None,
+        help="Project workspace root directory (default: current working directory).",
+    )
+    apply_patch_parser.add_argument(
+        "--dry-run",
+        action="store_true",
+        help="Validate patch integrity and check target anchors without writing changes to disk.",
+    )
+    apply_patch_parser.add_argument(
+        "--backup",
+        action="store_true",
+        help="Create .bak backups before overwriting target files.",
+    )
+    apply_patch_parser.add_argument(
+        "--quiet",
+        "-q",
+        action="store_true",
+        help="Suppress informational stdout output (only errors will be emitted).",
+    )
+    apply_patch_parser.add_argument(
+        "--json",
+        action="store_true",
+        help="Output structured JSON results instead of human-readable text.",
+    )
+
     if not argv:
         parser.print_help()
         return 0
@@ -2034,6 +2185,8 @@ def main(argv: Sequence[str] | None = None) -> int:
         return run_peer_watch_cli(argv[1:])
     if argv[0] in ("peer-dispatch", "dispatch-peer"):
         return run_peer_dispatch_cli(argv[1:])
+    if argv[0] in ("apply-anchor-patch", "peer-apply", "apply-patch"):
+        return run_apply_anchor_patch_cli(argv[1:])
     if argv[0] == "blast-radius":
         return run_blast_radius_cli(argv[1:])
     if argv[0] in ("why", "explain-why"):
@@ -2057,6 +2210,10 @@ def main(argv: Sequence[str] | None = None) -> int:
         return run_peer_gate_cli(argv[1:])
     if parsed.subcommand in ("peer-watch", "watch-peer"):
         return run_peer_watch_cli(argv[1:])
+    if parsed.subcommand in ("peer-dispatch", "dispatch-peer"):
+        return run_peer_dispatch_cli(argv[1:])
+    if parsed.subcommand in ("apply-anchor-patch", "peer-apply", "apply-patch"):
+        return run_apply_anchor_patch_cli(argv[1:])
     if parsed.subcommand == "blast-radius":
         return run_blast_radius_cli(argv[1:])
     if parsed.subcommand in ("why", "explain-why"):
diff --git a/packages/ccba-harness/src/ccba_harness/peer.py b/packages/ccba-harness/src/ccba_harness/peer.py
index 356e79f0..68b0a876 100644
--- a/packages/ccba-harness/src/ccba_harness/peer.py
+++ b/packages/ccba-harness/src/ccba_harness/peer.py
@@ -26,7 +26,13 @@
 from ._mutex import FileMutexLock
 
 AgentIdentity = Literal["antigravity", "grok"]
-PeerExecutionProfile = Literal["audit_plan", "agentic_code", "patch_fast"]
+PeerExecutionProfile = Literal[
+    "audit_plan",
+    "agentic_code",
+    "patch_fast",
+    "code_review",
+    "arch_audit",
+]
 ModelTier = Literal["local", "gateway", "cloud"]
 RequestType = Literal[
     "review",
@@ -110,6 +116,34 @@
             "Respond immediately with the required formatted blocks."
         ),
     },
+    "code_review": {
+        "model": "gemini-38-flash",  # ccba:allow-raw-model
+        "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
+        "max_turns": 6,
+        "tools": ["read_file", "grep", "list_dir"],
+        "disallowed_tools": [
+            "run_terminal_command",
+            "search_replace",
+            "write_file",
+            "spawn_subagent",
+        ],
+        "reasoning_effort": "high",
+        "timeout": 300.0,
+    },
+    "arch_audit": {
+        "model": "grok-4.7",  # ccba:allow-raw-model
+        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
+        "max_turns": 8,
+        "tools": ["read_file", "grep", "list_dir"],
+        "disallowed_tools": [
+            "run_terminal_command",
+            "search_replace",
+            "write_file",
+            "spawn_subagent",
+        ],
+        "reasoning_effort": "xhigh",
+        "timeout": 600.0,
+    },
 }
 
 FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
@@ -229,13 +263,20 @@ def extract_frontmatter(md_content: str) -> tuple[dict[str, Any] | None, str]:
     Returns:
         A tuple of (parsed_dict, body_text). If absent or invalid, returns (None, md_content).
     """
-    if not md_content or not md_content.startswith("---"):
+    if not md_content:
         return None, md_content
-    match = FRONTMATTER_PATTERN.match(md_content)
+
+    content = md_content.lstrip()
+    if content.startswith("```"):
+        content = re.sub(r"^```[a-zA-Z0-9_-]*\r?\n", "", content)
+
+    if not content.startswith("---"):
+        return None, md_content
+    match = FRONTMATTER_PATTERN.match(content)
     if not match:
         return None, md_content
     yaml_text = match.group(1)
-    body = md_content[match.end() :]
+    body = content[match.end() :]
     try:
         data = yaml.safe_load(yaml_text)
         if isinstance(data, dict):
@@ -767,18 +808,23 @@ def extract_anchor_payload(text: str) -> AnchorPatchPayload | None:
 def apply_anchor_patch(
     root: Path,
     payload: AnchorPatchPayload | dict[str, Any],
+    dry_run: bool = False,
+    backup: bool = False,
 ) -> list[Path]:
-    """Applies a Level-2 anchor patch payload atomically with SHA-256 pre-verification (ADR-0063).
+    """Applies a Level-2 anchor patch payload atomically with SHA-256 pre-verification and rollback (ADR-0063).
 
     Args:
         root: Workspace root directory.
         payload: AnchorPatchPayload instance or equivalent dictionary.
+        dry_run: If True, validates integrity and returns target files without modifying disk.
+        backup: If True, creates .bak copies before writing modified content.
 
     Returns:
-        List of Path instances successfully modified.
+        List of Path instances successfully modified (or validated if dry_run=True).
 
     Raises:
-        ValueError: If SHA-256 mismatch occurs or anchor string is not unique.
+        ValueError: If SHA-256 mismatch occurs, duplicate target files exist, anchor string is not unique,
+            or write transaction aborts.
     """
     if isinstance(payload, dict):
         patch = AnchorPatchPayload.model_validate(payload)
@@ -786,7 +832,10 @@ def apply_anchor_patch(
         patch = payload
 
     root_resolved = root.resolve()
-    prepared_writes: list[tuple[Path, str]] = []
+    target_files_seen: set[Path] = set()
+    prepared_writes: list[
+        tuple[Path, str, str]
+    ] = []  # (target_file, original_content, new_content)
 
     # Phase 1: Pre-validation of all files and content preparation (Fail-Fast)
     for file_patch in patch.files:
@@ -794,6 +843,10 @@ def apply_anchor_patch(
         # Security invariant: prevent path traversal outside workspace root
         if not target_file.is_relative_to(root_resolved):
             raise ValueError(f"Path traversal detected in patch: {file_patch.path}")
+        if target_file in target_files_seen:
+            raise ValueError(f"Payload contains duplicate target file: {file_patch.path}")
+        target_files_seen.add(target_file)
+
         if not target_file.exists():
             raise ValueError(f"Target patch file does not exist: {file_patch.path}")
 
@@ -806,27 +859,47 @@ def apply_anchor_patch(
             )
 
         text = raw_bytes.decode("utf-8")
+        # Line ending normalization (\r\n -> \n) for cross-OS resilience
+        text_normalized = text.replace("\r\n", "\n")
+        new_text = text_normalized
         for rep in file_patch.replacements:
-            count = text.count(rep.old)
+            old_normalized = rep.old.replace("\r\n", "\n")
+            new_normalized = rep.new.replace("\r\n", "\n")
+            count = new_text.count(old_normalized)
             if count == 0:
                 raise ValueError(
-                    f"Target old anchor text not found in {file_patch.path}: '{rep.old[:50]}...'"
+                    f"Target old anchor text not found in {file_patch.path}: '{old_normalized[:50]}...'"
                 )
             if count > 1:
                 raise ValueError(
-                    f"Target old anchor text is not unique in {file_patch.path} (found {count} matches): '{rep.old[:50]}...'"
+                    f"Target old anchor text is not unique in {file_patch.path} (found {count} matches): '{old_normalized[:50]}...'"
                 )
-            text = text.replace(rep.old, rep.new, 1)
+            new_text = new_text.replace(old_normalized, new_normalized, 1)
 
-        prepared_writes.append((target_file, text))
+        prepared_writes.append((target_file, text, new_text))
 
-    # Phase 2: Atomic commit of all prepared changes
-    modified_paths: list[Path] = []
-    for target_file, new_content in prepared_writes:
-        atomic_write_text(target_file, new_content)
-        modified_paths.append(target_file)
+    if dry_run:
+        return [target_file for target_file, _, _ in prepared_writes]
 
-    return modified_paths
+    # Phase 2: Atomic commit with automatic rollback on error
+    written_backups: dict[Path, str] = {}
+    modified_paths: list[Path] = []
+    try:
+        for target_file, original_content, new_content in prepared_writes:
+            written_backups[target_file] = original_content
+            if backup:
+                bak_file = target_file.with_suffix(target_file.suffix + ".bak")
+                atomic_write_text(bak_file, original_content)
+            atomic_write_text(target_file, new_content)
+            modified_paths.append(target_file)
+        return modified_paths
+    except Exception as exc:
+        for failed_file, old_content in written_backups.items():
+            try:
+                atomic_write_text(failed_file, old_content)
+            except Exception:
+                pass
+        raise ValueError(f"Transaction aborted during write phase: {exc}") from exc
 
 
 def extract_grok_session_telemetry(

```

## 4. Định Dạng Đầu Ra Yêu Cầu
Bắt đầu bằng YAML Frontmatter:
```yaml
---
request_id: "req-code-review-pr482-001"
verdict: APPROVE | APPROVE_WITH_CONDITIONS | REJECT
conditions: []
risk_score: 1-5
effort: XS | S | M | L | XL
summary: "Tóm tắt 1-2 câu kết luận thẩm định mã nguồn."
---
```
Tiếp theo là phần nhận xét chi tiết, chỉ ra các điểm tốt và các rủi ro tiềm ẩn (nếu có).
