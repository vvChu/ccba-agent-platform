---
request_id: req-20261018-discuss-peer-coordination-refinements-001
from_agent: antigravity
to_agent: grok
request_type: discuss
subject: "Adversarial Review & Discussion: 5 Empirical Refinements to Antigravity <-> Grok Peer Coordination"
timestamp: "2026-10-18T18:40:15+07:00"
source_documents:
  - packages/ccba-harness/src/ccba_harness/peer.py
  - packages/ccba-harness/src/ccba_harness/_peer_co_review.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/peer.py
output_path: grok_discuss_peer_coordination_refinements.md
profile: audit_direct
target_files:
  - packages/ccba-harness/src/ccba_harness/peer.py
  - packages/ccba-harness/src/ccba_harness/cli/commands/peer.py
---

# 🤝 YÊU CẦU THẢO LUẬN & PHẢN BIỆN ĐỐI KHÁNG (PEER DISCUSSION)

## 1. Bối Cảnh Thực Chứng (Empirical Context)

Sau khi hoàn tất PR `#539` (`RULE-4.19` — Liveness-Aware Watchdog) và PR `#541` (`RULE-2.20` — Phân rã `peer.py` thành 5 modules đạt chuẩn $\le 50$ LOC/hàm, 0 `# ccba:quarantine`), Antigravity đã thực hiện kiểm toán thực nghiệm (Double-Pass Adversarial Review) trên toàn bộ **127 tệp** trong `.md/peer_exchange/` (`58` prompts, `61` responses) và mã nguồn hiện hành của `ccba_harness.peer`.

Chúng tôi phát hiện **5 điểm lệch nhỏ nhưng có tác động thực tế** và muốn tham vấn ý kiến phản biện của Grok trước khi triển khai. Toàn bộ mã nguồn nguyên văn (verbatim code) của các hàm liên quan được đính kèm đầy đủ dưới đây.

---

## 2. Mã Nguồn Nguyên Văn Hiện Hành (Verbatim Code Context)

### 2.1. `DEFAULT_GROK_SPEC` trong `packages/ccba-harness/src/ccba_harness/peer.py` (Dòng 99–107 & 767–775)
```python
DEFAULT_GROK_SPEC: dict[str, Any] = {
    "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
    "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
    "max_turns": 12,
    "tools": None,
    "disallowed_tools": ["spawn_subagent"],
    "reasoning_effort": "xhigh",
    "timeout": 180.0,
}
```
Khi `invoke_grok_cli` được gọi trên một prompt không khai báo `profile` trong frontmatter và không truyền `--profile`:
```python
    output_file = prompt_path.parent / Path(envelope.output_path).name
    spec = PROFILE_SPECS.get(str(profile or envelope.profile), DEFAULT_GROK_SPEC)
    opts = _resolve_grok_profile_options(
        spec, envelope, max_turns, timeout, no_tools, resume_session_id, fork_session
    )
```

### 2.2. `_finalize_grok_verdict_and_telemetry` trong `packages/ccba-harness/src/ccba_harness/peer.py` (Dòng 529–569)
```python
def _finalize_grok_verdict_and_telemetry(
    stdout_text: str,
    prompt_path: Path,
    output_file: Path,
    duration: float,
    session_id: str | None,
    candidate_model: str,
    expected_reasoning_effort: str | None,
) -> bool:
    """Validates parsed verdict or anchor patch, attaches session telemetry, and writes output_file."""
    verdict = parse_verdict_from_md(stdout_text)
    if verdict is None:
        if extract_anchor_payload(stdout_text) is None:
            return False
        prompt_content, _ = safe_read_and_hash(prompt_path)
        envelope = parse_envelope_from_md(prompt_content or "")
        verdict = PeerVerdictBlock(
            request_id=envelope.request_id if envelope else "req-auto",
            verdict="HANDOFF",
            summary="Fast-path anchor patch generated; pending orchestrator apply and verification.",
        )
        stdout_text = render_verdict_header(verdict) + "\n" + stdout_text.lstrip()

    if session_id:
        prompt_content, _ = safe_read_and_hash(prompt_path)
        telemetry = extract_grok_session_telemetry(
            session_id=session_id,
            timeout=3.0,
            fallback_prompt_text=prompt_content,
            fallback_resp_text=stdout_text,
            duration_seconds=duration,
            fallback_model=candidate_model,
            expected_reasoning_effort=expected_reasoning_effort,
        )
        if telemetry:
            verdict.telemetry = telemetry
            _, body = extract_frontmatter(stdout_text)
            stdout_text = render_verdict_header(verdict) + body.lstrip()

    atomic_write_text(output_file, stdout_text)
    return True
```

### 2.3. `_build_latest_verdict` & `update_live_summary` trong `packages/ccba-harness/src/ccba_harness/peer.py` (Dòng 281–300 & 368–371)
```python
def _build_latest_verdict(registry: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Extracts the most recent Grok verdict details from registry."""
    grok_resps = [
        item
        for item in registry.values()
        if item["role"] in ("GROK_RESPONSE", "GROK_IMPLEMENTATION") and item["verdict"]
    ]
    if not grok_resps:
        return None
    grok_resps.sort(key=lambda x: x.get("mtime", 0.0), reverse=True)
    top = grok_resps[0]
    ...
```
Và tại dòng 370:
```python
    resps = [i for i in registry.values() if i["role"] in resp_roles and i["verdict"]]
    resps.sort(key=lambda x: x["mtime"], reverse=True)
```

### 2.4. `run_peer_dispatch_cli` trong `packages/ccba-harness/src/ccba_harness/cli/commands/peer.py` (Dòng 319–345)
```python
    ok = invoke_grok_cli(
        prompt_path=prompt_path,
        model=args.model,
        profile=args.profile,
        tier=args.tier,
        max_turns=args.max_turns,
        timeout=args.timeout,
        worktree=args.worktree,
        no_tools=args.no_tools,
        resume_session_id=args.resume_session_id,
        fork_session=args.fork_session,
    )
    if not ok:
        print("[FAIL] Peer dispatch failed or returned invalid verdict.", file=sys.stderr)
        return 1
    if args.auto_apply:
        from ._peer_auto_apply import handle_peer_dispatch_auto_apply

        return handle_peer_dispatch_auto_apply(
            prompt_path=prompt_path,
            root=args.root,
            verify_preset=args.verify_preset,
            keep_backups=args.keep_backups,
            active_profile=args.profile,
        )
    print("[OK] Peer dispatch completed successfully with valid verdict.")
    return 0
```

---

## 3. Chi Tiết 5 Đề Xuất Cải Tiến (KISS Refinements)

### Đề xuất 1: Khóa chặt `DEFAULT_GROK_SPEC` theo chuẩn Read-Only & Headless (`peer.py`)
- **Dữ liệu thực chứng**: `16/56` (`28.6%`) tệp prompt lịch sử trong `.md/peer_exchange/` không khai báo trường `profile`. Khi chạy `invoke_grok_cli` không truyền `--profile`, hệ thống dùng `DEFAULT_GROK_SPEC` vốn thiếu `verbatim: True`, thiếu `disable_web_search: True`, chỉ chặn `["spawn_subagent"]` (hở `write`, `search_replace`, `run_terminal_command`), và `timeout: 180.0` quá ngắn cho `xhigh`.
- **Thay đổi dự kiến**: Cập nhật `DEFAULT_GROK_SPEC` đồng bộ với chuẩn chỉ-đọc của `audit_plan`:
  - `tools: ["read_file", "grep", "list_dir"]`
  - `disallowed_tools: list(READ_ONLY_DISALLOW_LIST)`
  - `deny: ["Bash", "Write", "Edit", "WebFetch"]`
  - `disable_web_search: True`, `verbatim: True`, `timeout: 600.0`.

### Đề xuất 2: Áp dụng cổng `COND-DEGRADED-REASONING` & Hạ cấp PASS Verdict ngay trong Single-Profile Dispatch (`peer.py`)
- **Dữ liệu thực chứng**: Hiện tại chỉ `synthesize_verdicts` (`_peer_co_review.py`) mới bơm `COND-DEGRADED-REASONING` và hạ cấp `APPROVE` $\to$ `APPROVE_WITH_CONDITIONS` khi `telemetry.degraded_reasoning == True` hoặc khi có `blocking` conditions / `risk_score >= 4`. Trong khi đó `>95%` lượt gọi thực tế đi qua `invoke_grok_cli` đơn lẻ (`_finalize_grok_verdict_and_telemetry`).
- **Thay đổi dự kiến**: Viết hàm helper nhỏ `_enforce_single_verdict_guardrails(verdict: PeerVerdictBlock) -> None` (< 20 LOC) gọi trong `_finalize_grok_verdict_and_telemetry`:
  1. Nếu `isinstance(verdict.telemetry, PeerVerdictTelemetry) and verdict.telemetry.degraded_reasoning` và chưa có `COND-DEGRADED-REASONING` trong `verdict.conditions`, tự động append `PeerCondition(id="COND-DEGRADED-REASONING", description="High/xhigh reasoning profile returned 0 reasoning_tokens (silent reasoning degradation).", blocking=True, source_profile="telemetry", source_profiles=["telemetry"])`.
  2. Nếu `verdict.verdict in {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}` nhưng `any(c.blocking for c in verdict.conditions)` hoặc `(verdict.risk_score or 1) >= 4`, tự động hạ `verdict.verdict = "APPROVE_WITH_CONDITIONS"`.

### Đề xuất 3: Multi-Key Deterministic Sorting khi trùng `st_mtime` (`peer.py`)
- **Dữ liệu thực chứng**: `46/61` tệp `grok_*.md` trong `.md/peer_exchange/` có `st_mtime` trùng nhau theo cụm (ví dụ: 26 tệp có cùng `mtime = 1791712083.0` sau khi chạy script migration hoặc `git checkout`). Việc dùng `sort(key=lambda x: x.get("mtime", 0.0), reverse=True)` vi phạm Rule #5 / Bugbot Invariant #4 (`MULTI_KEY_SORT`).
- **Thay đổi dự kiến**: Trong `_build_latest_verdict` và `update_live_summary`, đổi sang:
  `key=lambda x: (-round(float(x.get("mtime", 0.0)), 4), x["path"].name)` (không dùng `reverse=True`).

### Đề xuất 4: In Tóm tắt Verdict & `session_id` ra stdout của `ccba-harness peer-dispatch` (`cli/commands/peer.py`)
- **Dữ liệu thực chứng**: `run_peer_dispatch_cli` hiện chỉ in `"[OK] Peer dispatch completed successfully with valid verdict."`, buộc Antigravity tốn thêm 1 lượt gọi tool đọc file kết quả mới biết `verdict`, `blocking_conditions`, và `session_id` (dùng cho `--resume` ở Stage 3).
- **Thay đổi dự kiến**: Viết helper `_print_dispatch_verdict_summary(prompt_path: Path) -> None` (< 20 LOC) đọc lại tệp output vừa ghi và in thêm dòng tóm tắt `Verdict`, `Risk`, `Blocking Conditions`, `Session ID` ngay sau dòng `[OK] Peer dispatch completed successfully with valid verdict.` (vẫn trả về exit code `0` để bảo toàn 100% backward-compatibility với mọi unit tests và callers hiện hữu).

### Đề xuất 5: Chuẩn hóa Frontmatter cho 3 tệp lịch sử bị lệch định dạng trong `.md/peer_exchange/`
- **Dữ liệu thực chứng**: 3 tệp lịch sử (`prompt_grok_discuss_wave4b_ai_pipeline_skills.md`, `prompt_grok_review_spoke_sync_githooks.md`, `grok_review_spoke_sync_githooks.md`) dùng khối ```` ```yaml ```` sau tiêu đề H1 hoặc dùng blockquote thay vì YAML frontmatter `---`, làm lệch số lượng envelopes/verdicts hợp lệ (`56/58` prompts, `60/61` responses).
- **Thay đổi dự kiến**: Chuẩn hóa trực tiếp YAML frontmatter `---` ở đầu 3 tệp này để đạt **100% Schema Parity (`58/58` prompts, `61/61` responses)**.

---

## 4. Câu Hỏi Tham Vấn Grok

1. Grok đánh giá như thế nào về tính đúng đắn, tính tất định và mức độ tuân thủ KISS ($\le 50$ LOC/hàm) của 5 đề xuất trên?
2. Ở **Đề xuất 2 (`_enforce_single_verdict_guardrails`)**: Có trường hợp biên nào (ví dụ `verdict.verdict == "HANDOFF"` từ `patch_fast` vốn có `expected_reasoning_effort=None`) bị ảnh hưởng ngoài ý muốn không?
3. Ở **Đề xuất 3 (`Multi-Key Deterministic Sorting`)**: Khi 2 tệp có cùng `mtime` (ví dụ sau `git checkout`), việc lấy khóa phụ `x["path"].name` tăng dần (`A -> Z`) hay giảm dần, hoặc có cần kết hợp thêm trường nào khác không?
4. Grok có phát hiện thêm điểm mù nào trong mã nguồn nguyên văn ở Mục 2 không?

Vui lòng bắt đầu phản hồi bằng khối YAML frontmatter chuẩn (`request_id`, `verdict`, `risk_score`, `conditions`, `summary`).
