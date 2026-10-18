---
request_id: req-20261018-discuss-peer-coordination-refinements-001
verdict: APPROVE_WITH_CONDITIONS
conditions:
- id: COND-RE-RENDER-ON-MUTATION
  description: Tái tạo stdout_text từ verdict header sau khi thực thi guardrail trong
    mọi nhánh thực thi (bao gồm cả khi session_id=None hoặc telemetry=None) để bảo
    đảm output_file luôn phản ánh chính xác verdict đã hạ cấp.
  blocking: true
  source_profiles: []
- id: COND-CHRONOLOGICAL-TIE-BREAKER
  description: Áp dụng bộ tuple khóa giảm dần đồng nhất (mtime, timestamp, path) với
    reverse=True để tệp mới nhất theo dòng thời gian luôn đứng tại vị trí đầu danh
    sách khi st_mtime trùng lặp.
  blocking: true
  source_profiles: []
risk_score: 1
summary: 'Phê duyệt 5 đề xuất cải tiến với 2 điều kiện kỹ thuật: bảo đảm re-render
  frontmatter khi verdict bị biến đổi ở luồng dispatch đơn lẻ và chuẩn hóa cơ chế
  sắp xếp đa khóa phản ánh đúng trình tự thời gian giảm dần.'
telemetry:
  session_id: 04acf64e-4983-457a-b888-b701666ae9dc
  primary_model: gemini-3.8-flash-high
  input_tokens: 14089
  output_tokens: 4526
  reasoning_tokens: 6359
  cached_read_tokens: 0
  total_tokens: 18615
  model_calls: 1
  turn_count: 1
  cost_usd: 0.0402
  cost_mode: estimated
  duration_seconds: 71.11
  degraded_reasoning: false
---
# BÁO CÁO KIỂM TOÁN KIẾN TRÚC & PHẢN BIỆN ĐỐI KHÁNG (PEER AUDIT)

Grok xác nhận đã hoàn tất thẩm tra toàn diện 5 đề xuất cải tiến kiến trúc điều phối ngang hàng Antigravity $\leftrightarrow$ Grok, đối soát trực tiếp với mã nguồn hiện hành tại `packages/ccba-harness/src/ccba_harness/peer.py`, `_peer_co_review.py` và `cli/commands/peer.py`.

---

## 1. Đánh Giá Chi Tiết 5 Đề Xuất Cải Tiến

### Đề xuất 1: Khóa chặt `DEFAULT_GROK_SPEC` theo chuẩn Read-Only & Headless (`peer.py`)
- **Đánh giá**: **HỢP LÝ & AN TOÀN TUYỆT ĐỐI**.
- **Cơ sở kỹ thuật**: Khi prompt không khai báo `profile`, tư thế mặc định của agent phản biện phải là phòng thủ tối đa (Least Privilege). Việc thiết lập danh sách công cụ chỉ-đọc (`read_file`, `grep`, `list_dir`), áp dụng `deny: ["Bash", "Write", "Edit", "WebFetch"]`, bật `disable_web_search: True`, `verbatim: True` và nâng timeout lên `600.0s` loại bỏ triệt để nguy cơ agent tự ý chỉnh sửa tệp ngoài ý muốn và đáp ứng đầy đủ thời gian tính toán cho profile suy luận sâu (`xhigh`).

### Đề xuất 2: Áp dụng cổng `COND-DEGRADED-REASONING` & Hạ cấp PASS Verdict trong Single-Profile Dispatch (`peer.py`)
- **Đánh giá**: **CẦN THIẾT — KÈM ĐIỀU KIỆN KỸ THUẬT (COND-RE-RENDER-ON-MUTATION)**.
- **Cơ sở kỹ thuật**: Đồng bộ hóa quy tắc thẩm tra giữa chế độ chạy đơn (`invoke_grok_cli`) và chế độ tổng hợp đa mô hình (`synthesize_verdicts`) bảo đảm tính nhất quán của hệ thống. 
- **Ràng buộc bắt buộc**: Xem chi tiết phân tích ca biên tại Mục 2 và Mục 4. Quá trình re-render frontmatter phải được thực thi ở điểm tập trung trước khi ghi đĩa để tránh tình trạng verdict trong bộ nhớ đã đổi nhưng tệp `.md` trên đĩa vẫn giữ nguyên nội dung gốc.

### Đề xuất 3: Multi-Key Deterministic Sorting khi trùng `st_mtime` (`peer.py`)
- **Đánh giá**: **CẦN THIẾT — KÈM ĐIỀU KIỆN KỸ THUẬT (COND-CHRONOLOGICAL-TIE-BREAKER)**.
- **Cơ sở kỹ thuật**: Hiện tượng 46/61 tệp có `st_mtime` trùng nhau sau các thao tác Git checkout/sync là thực tế phổ biến trên hệ thống tệp Linux/macOS/NTFS. Việc bổ sung khóa phụ bảo đảm tính tất định 100% giữa các môi trường chạy khác nhau.
- **Ràng buộc bắt buộc**: Chiều sắp xếp của khóa phụ phải đồng bộ theo thứ tự thời gian giảm dần (Xem chi tiết tại Mục 2.3).

### Đề xuất 4: In Tóm tắt Verdict & `session_id` ra stdout của `ccba-harness peer-dispatch` (`cli/commands/peer.py`)
- **Đánh giá**: **HỢP LÝ & TIẾT KIỆM TÀI NGUYÊN (KISS)**.
- **Cơ sở kỹ thuật**: Việc xuất trực tiếp `Verdict`, `Risk Score`, `Blocking Conditions Count`, và `Session ID` ra stdout giúp tiến trình gọi thu nhận ngay thông tin trọng yếu mà không cần thêm một lượt I/O đọc lại tệp kết quả. Việc giữ nguyên mã thoát `0` bảo toàn tính tương thích ngược cho toàn bộ callers và harness test suites hiện hữu.

### Đề xuất 5: Chuẩn hóa Frontmatter cho 3 tệp lịch sử trong `.md/peer_exchange/`
- **Đánh giá**: **HỢP LÝ & TỐI ƯU DỮ LIỆU ĐO KIỂM**.
- **Cơ sở kỹ thuật**: Đưa 100% tệp trao đổi về đúng chuẩn YAML frontmatter (`---`) giúp bộ parser và registry đạt độ chuẩn hóa tuyệt đối (`58/58` prompts, `61/61` responses), loại bỏ các ngoại lệ giả trong quá trình kiểm toán tự động.

---

## 2. Trả Lời Trực Tiếp 4 Câu Hỏi Tham Vấn

### Câu hỏi 1: Tính đúng đắn, tính tất định và mức độ tuân thủ KISS ($\le 50$ LOC/hàm)
Cả 5 đề xuất đều đạt chuẩn kiến trúc:
1. **Tính đúng đắn**: Khắc phục trực tiếp các bất đối xứng giữa đơn luồng và đa luồng, loại bỏ lỗ hổng phân quyền mặc định.
2. **Tính tất định**: Triệt tiêu sự phụ thuộc vào thứ tự sắp xếp không ổn định của hệ điều hành khi `st_mtime` va chạm.
3. **Mức độ tuân thủ KISS**: Mỗi thay đổi được đóng gói thành các hàm thuần túy (pure functions/helpers) độc lập, quy mô dao động từ 12 đến 28 LOC, nằm an toàn dưới ngưỡng 50 LOC theo chuẩn hiến pháp CCBA.

---

### Câu hỏi 2: Phân tích ca biên của Đề xuất 2 (`_enforce_single_verdict_guardrails`)
Xem xét hai trường hợp biên chính:
1. **Trường hợp `verdict.verdict == "HANDOFF"` từ `patch_fast`**:
   - Khi chạy `patch_fast`, `verdict.verdict` được gán cố định là `"HANDOFF"`.
   - Vì `"HANDOFF"` nằm ngoài tập các trạng thái PASS (`{"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}`), logic hạ cấp hoàn toàn bỏ qua trạng thái này.
   - Khi `patch_fast` sử dụng `expected_reasoning_effort=None`, trường `degraded_reasoning` trong telemetry luôn là `False`, do đó điều kiện `COND-DEGRADED-REASONING` không bị kích hoạt ngoài ý muốn. Trạng thái `HANDOFF` được bảo toàn nguyên vẹn.
2. **Trường hợp `session_id is None` hoặc telemetry trích xuất thất bại**:
   - Nếu Grok trả về `APPROVE` nhưng trong phần thân frontmatter tự khai báo `risk_score: 4` hoặc có điều kiện `blocking: true`: guardrail vẫn bắt buộc phải hạ cấp về `APPROVE_WITH_CONDITIONS`.
   - Do đó, `_enforce_single_verdict_guardrails` phải được đặt ở vị trí có thể tác động đến cả hai nhánh (có telemetry hoặc không có telemetry).

---

### Câu hỏi 3: Xác định chiều sắp xếp của khóa phụ khi `st_mtime` trùng nhau
Trong `_build_latest_verdict` và `update_live_summary`, mục tiêu là chọn ra **tệp mới nhất** đưa lên vị trí đầu danh sách (`index 0`).

Nếu sử dụng cấu trúc `key=lambda x: (-round(float(x.get("mtime", 0.0)), 4), x["path"].name)`:
- Khóa chính `mtime` được sắp xếp giảm dần (số âm nhỏ hơn đứng trước).
- Khóa phụ `x["path"].name` lại được sắp xếp tăng dần theo bảng chữ cái (`A -> Z`).
- Hệ quả: Khi hai tệp có cùng `mtime`, tệp có tên `...-001.md` sẽ đứng trước tệp `...-002.md`, dẫn đến việc hệ thống chọn nhầm tệp cũ hơn làm "latest verdict".

**Giải pháp chuẩn hóa**: Sử dụng `reverse=True` đồng nhất cho toàn bộ các trường trong tuple so sánh:
```python
def _sort_key_latest_exchange(item: dict[str, Any]) -> tuple[float, str, str]:
    """Tuple key prioritizing higher mtime, newer ISO timestamp, and lexicographical order."""
    return (
        round(float(item.get("mtime", 0.0)), 4),
        str(item.get("timestamp") or ""),
        item["path"].name,
    )
```
Và thực hiện sắp xếp:
```python
grok_resps.sort(key=_sort_key_latest_exchange, reverse=True)
```
Cơ chế này bảo đảm:
1. `mtime` cao hơn đứng trước.
2. Nếu `mtime` trùng nhau, trường `timestamp` ISO khai báo trong frontmatter (ví dụ `2026-10-18T18:40:15`) mới hơn đứng trước.
3. Nếu vẫn trùng, tên tệp có số thứ tự lớn hơn (`...-002.md`) đứng trước.

---

### Câu hỏi 4: Các điểm mù phát hiện thêm trong mã nguồn nguyên văn Mục 2

#### Điểm mù 1: Vị trí re-render frontmatter trong `_finalize_grok_verdict_and_telemetry`
Trong mã nguồn hiện hành:
```python
if session_id:
    telemetry = extract_grok_session_telemetry(...)
    if telemetry:
        verdict.telemetry = telemetry
        _, body = extract_frontmatter(stdout_text)
        stdout_text = render_verdict_header(verdict) + body.lstrip()

atomic_write_text(output_file, stdout_text)
```
Nếu `_enforce_single_verdict_guardrails` sửa đổi `verdict` nhưng rơi vào một trong các tình huống sau:
- `session_id` là `None` (chạy prompt độc lập không resume/session tracking);
- Quá trình lấy telemetry trả về `None` (do timeout 3.0s hoặc lỗi RPC);

Khi đó, khối lệnh `if telemetry:` không được kích hoạt. Biến `stdout_text` không được cập nhật lại từ `verdict`, dẫn đến tệp `output_file` ghi xuống đĩa vẫn chứa verdict cũ chưa được hạ cấp. 
*Giải pháp*: Thực thi `_enforce_single_verdict_guardrails` và re-render `stdout_text` ở bước cuối cùng, ngay trước lệnh `atomic_write_text`.

#### Điểm mù 2: Đọc đĩa và băm tệp lặp lại (Redundant I/O)
Tại dòng 539 và dòng 549:
- Dòng 539: `prompt_content, _ = safe_read_and_hash(prompt_path)`
- Dòng 549: `prompt_content, _ = safe_read_and_hash(prompt_path)`
Khi verdict ban đầu trả về rỗng (nhưng có anchor payload) và có `session_id`, tệp `prompt_path` bị đọc từ đĩa và tính SHA-256 hai lần liên tiếp. Cần đọc một lần duy nhất.

#### Điểm mù 3: Đồng bộ khoảng trắng phân tách header và body
Tại dòng 545:
`stdout_text = render_verdict_header(verdict) + "\n" + stdout_text.lstrip()`
Tại dòng 564:
`stdout_text = render_verdict_header(verdict) + body.lstrip()`
Hàm `render_verdict_header` đã kết thúc bằng ký tự dòng mới `---\n`. Việc dùng thêm `"\n"` ở dòng 545 tạo ra 2 dòng trống, trong khi dòng 564 tạo ra 0 dòng trống trước tiêu đề Markdown đầu tiên. Cần chuẩn hóa thống nhất một quy cách nối chuỗi duy nhất: `render_verdict_header(verdict) + "\n" + body.lstrip()`.

---

## 3. Khung Mã Nguồn Khuyến Nghị Triển Khai (KISS & Clean Refactoring)

### 3.1. Cập nhật `DEFAULT_GROK_SPEC` trong `packages/ccba-harness/src/ccba_harness/peer.py`
```python
DEFAULT_GROK_SPEC: dict[str, Any] = {
    "model": DEFAULT_PRIMARY_AUDITOR_MODEL,
    "fallback_model": DEFAULT_FALLBACK_AUDITOR_MODEL,
    "max_turns": 12,
    "tools": ["read_file", "grep", "list_dir"],
    "disallowed_tools": list(READ_ONLY_DISALLOW_LIST),
    "deny": ["Bash", "Write", "Edit", "WebFetch"],
    "disable_web_search": True,
    "verbatim": True,
    "reasoning_effort": "xhigh",
    "timeout": 600.0,
}
```

### 3.2. Cập nhật `_finalize_grok_verdict_and_telemetry` và helper trong `peer.py`
```python
_PASS_VERDICTS: frozenset[str] = frozenset(
    {"APPROVE", "APPROVE_PLAN", "FINAL_ACCEPT", "GATE_PASS", "APPROVE_WITH_RESERVATIONS"}
)


def _enforce_single_verdict_guardrails(verdict: PeerVerdictBlock) -> bool:
    """Applies degraded reasoning condition and downgrades pass verdicts if blocking conditions exist."""
    modified = False
    telemetry = verdict.telemetry
    has_degraded = bool(telemetry and getattr(telemetry, "degraded_reasoning", False))
    existing_cond_ids = {c.id for c in verdict.conditions}

    if has_degraded and "COND-DEGRADED-REASONING" not in existing_cond_ids:
        verdict.conditions.append(
            PeerCondition(
                id="COND-DEGRADED-REASONING",
                description="High/xhigh reasoning profile returned 0 reasoning_tokens (silent reasoning degradation).",
                blocking=True,
                source_profile="telemetry",
                source_profiles=["telemetry"],
            )
        )
        modified = True

    has_blocking = any(c.blocking for c in verdict.conditions)
    has_high_risk = (verdict.risk_score or 1) >= 4
    if verdict.verdict in _PASS_VERDICTS and (has_blocking or has_high_risk):
        verdict.verdict = "APPROVE_WITH_CONDITIONS"
        modified = True

    return modified


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
    prompt_content: str | None = None

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

    if session_id:
        if prompt_content is None:
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

    _enforce_single_verdict_guardrails(verdict)
    _, body = extract_frontmatter(stdout_text)
    final_output = render_verdict_header(verdict) + "\n" + body.lstrip()
    atomic_write_text(output_file, final_output)
    return True
```

### 3.3. Helper tóm tắt CLI trong `packages/ccba-harness/src/ccba_harness/cli/commands/peer.py`
```python
def _print_dispatch_verdict_summary(prompt_path: Path) -> None:
    """Prints a concise one-line summary of verdict, risk, conditions, and session ID to stdout."""
    prompt_content, _ = safe_read_and_hash(prompt_path)
    envelope = parse_envelope_from_md(prompt_content or "")
    if not envelope or not envelope.output_path:
        return
    out_file = prompt_path.parent / Path(envelope.output_path).name
    if not out_file.exists():
        return
    text, _ = safe_read_and_hash(out_file)
    verdict = parse_verdict_from_md(text or "")
    if not verdict:
        return
    blocking_count = sum(1 for c in verdict.conditions if c.blocking)
    sess_id = verdict.telemetry.session_id if verdict.telemetry else "none"
    print(
        f"[PEER-SUMMARY] Verdict: {verdict.verdict} | Risk: {verdict.risk_score} | "
        f"Blocking Conditions: {blocking_count} | Session ID: {sess_id}"
    )
```

Gọi hàm trên ngay trong `run_peer_dispatch_cli`:
```python
    print("[OK] Peer dispatch completed successfully with valid verdict.")
    _print_dispatch_verdict_summary(prompt_path)
    return 0
```

---

## 4. Kết Luận

Kế hoạch 5 cải tiến của Antigravity đạt chuẩn kiến trúc cao, giải quyết trúng các điểm nghẽn thực tế từ 127 tệp lịch sử. Antigravity có thể bắt đầu triển khai ngay theo đúng các khuyến nghị và điều kiện kỹ thuật nêu trên.
