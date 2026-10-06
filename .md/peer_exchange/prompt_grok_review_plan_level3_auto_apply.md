---
request_id: "req-plan-level3-auto-apply-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Kế hoạch Kỹ thuật: Level-3 Autonomous Loopback (--auto-apply) & Self-Healing Rollback Engine"
timestamp: "2026-10-06T09:27:00+07:00"
max_turns: 15
source_documents: []
output_path: ".md/peer_exchange/grok_review_plan_level3_auto_apply.md"
context: "Thẩm định kế hoạch thiết kế và rào chắn an toàn cho Level-3 Autonomous Loopback theo các điều kiện COND-LEVEL3-GATE và ADR-0065."
---

# 🎯 Yêu Cầu Thẩm Tra Kế Hoạch (Audit Plan): Level-3 Autonomous Loopback (--auto-apply)

> ⚠️ **Chỉ Dẫn Cho Reviewer**: Toàn bộ bản kế hoạch kỹ thuật chi tiết đã được đính kèm trực tiếp tại Mục 1 dưới đây. Bạn **KHÔNG CẦN** gọi các công cụ đọc đĩa tốn lượt. Hãy tiến hành rà soát kỹ thuật đối kháng, trả lời 3 câu hỏi kiến trúc và xuất ngay phán quyết `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra theo đúng mẫu ở Mục 2!

---

## 1. Toàn Văn Bản Kế Hoạch Kỹ Thuật (Implementation Plan)

# 📋 Implementation Plan: Level-3 Autonomous Loopback (`--auto-apply`) & Self-Healing Rollback Engine

> **Trạng thái**: 🟡 **DRAFT - CHUẨN BỊ GỬI GROK-4.7 XHIGH PHẢN BIỆN ĐỐI KHÁNG (PEER REVIEW)**  
> **Mục tiêu**: Tự động hóa toàn trình chu trình ủy thác ngang hàng: Sinh patch neo $\to$ Thẩm tra an toàn $\to$ Áp dụng nguyên tử $\to$ Kiểm định tất định (`verify-patch`) $\to$ Tự động hoàn nguyên (Rollback) nếu phát sinh lỗi.  
> **Tiêu chuẩn tuân thủ**: ADR-0058 (Deterministic Hard Completion Lock), ADR-0061 (Reuse-First Gate), ADR-0063 / ADR-0064 / ADR-0065 (Level-2/2.5 Hardening).

---

## 1. Bối Cảnh & Mục Tiêu Kỹ Thuật

Hiện tại, nền tảng CCBA đã hoàn thành vững chắc:
1. **Level-2 Single-Agent Delegation (`peer-dispatch`)**: Điều phối prompt qua Grok CLI với các profile chuyên trách (`patch_fast`, `agentic_code`, `audit_plan`...).
2. **Level-2.5 Multi-Agent Co-Review (`peer-co-review`)**: Điều phối song song nhiều agent (`code_review`, `arch_audit`), tổng hợp phán quyết tất định theo mạng lưới Lattice 11 tokens.
3. **Transactional Patch Engine (`apply-anchor-patch`)**: Áp dụng bản vá neo với kiểm tra SHA-256, path traversal guard, chuẩn hóa CRLF, và khôi phục transactional rollback khi phát sinh ngoại lệ ghi.

**Khoảng trống kỹ thuật hiện tại**:
Khi tác nhân (`patch_fast`) tạo ra bản vá neo JSON (`AnchorPatchPayload`), người dùng hoặc tác nhân điều phối vẫn phải gọi thủ công lệnh `apply-anchor-patch` và sau đó tự chạy `verify-patch`. Nếu bản vá làm hỏng bài kiểm tra (regression/test failure), mã nguồn đã bị sửa đổi dở dang trên đĩa mà không tự động khôi phục.

**Mục tiêu của Level-3 Autonomous Loopback**:
- Cho phép truyền cờ `--auto-apply` trực tiếp vào `peer-dispatch` (và `peer-co-review`).
- Tự động áp dụng bản vá ngay sau khi worker hoàn tất sinh patch hợp lệ.
- Tự động kích hoạt cổng kiểm định tất định `verify_patch_execution(preset="ci")`.
- **Closed-Loop Self-Healing Rollback**: Nếu bài kiểm định không đạt 100% pass (`all_passed == False`), hệ thống **lập tức hoàn nguyên 100% mã nguồn** từ các bản sao lưu `.bak`, xóa bỏ mọi thay đổi dở dang và hạ phán quyết xuống `GATE_FAIL`.

---

## 2. Rào Chắn Kiểm Soát An Toàn (COND-LEVEL3-GATE Invariants)

Theo khuyến nghị kiến trúc từ đợt Dogfooding của `arch_audit` (Grok-4.7 xhigh), hệ thống bắt buộc thực thi 5 rào chắn bất biến:

1. **Cấm Tin Tưởng Phán Quyết Giả Lập Từ Worker (`COND-PATCHFAST-APPROVE`)**:
   - Bản vá từ `patch_fast` chỉ mang vai trò `HANDOFF` (hoặc payload thô). Tuyệt đối không cho phép model tự tuyên bố `APPROVE` để vượt cổng an toàn.
   - Chỉ khi bản vá vượt qua `verify-patch` exit code 0, phán quyết mới được thăng cấp thành `GATE_PASS` hoặc `FINAL_ACCEPT`.
2. **Pre-Apply Security & Hash Barrier (Fail-Fast)**:
   - Trước khi ghi bất kỳ byte nào lên đĩa, bắt buộc thực hiện kiểm tra `dry_run=True` của `apply_anchor_patch`:
     - So khớp SHA-256 hash của từng tệp đích.
     - Phát hiện và chặn đứng tấn công Path Traversal ngoài `root`.
     - Ngăn ngừa tệp đích trùng lặp (`target_files_seen`).
     - Xác nhận chuỗi neo gốc xuất hiện duy nhất 1 lần trong tệp đích.
3. **Transactional Backup Barrier**:
   - Khi ghi tệp thực tế, bắt buộc tạo bản sao lưu `.bak` nguyên vẹn cho mọi tệp bị sửa đổi.
4. **Hard Verification Gate (ADR-0058)**:
   - Sau khi ghi tệp, bắt buộc chạy `verify_patch_execution(preset=preset, cwd=root)`.
   - Nếu exit code $\ne 0$ hoặc `all_passed == False`: **Rollback cưỡng bức không điều kiện**.
5. **Anti-Tampering on Consensus Reports**:
   - Cấm áp dụng `--auto-apply` trên các báo cáo đồng thuận `peer-co-review` nếu phán quyết tổng hợp tồn tại bất kỳ điều kiện chặn nào (`blocking=True`), hoặc điểm rủi ro `risk_score >= 4`, hoặc phán quyết rơi vào `REVISE_PLAN` / `REJECT` / `HANDOFF`.

---

## 3. Thiết Kế Kiến Trúc & Chi Tiết Triển Khai

### 3.1. Deep Seam Mới: `auto_apply_and_verify_patch`
Vị trí: `packages/ccba-harness/src/ccba_harness/peer.py` (xuất khẩu công khai qua `__init__.py`).

```python
def auto_apply_and_verify_patch(
    root: Path,
    patch_payload: dict[str, Any],
    verify_preset: str = "ci",
    timeout: float = 180.0,
    keep_backups: bool = False,
) -> tuple[bool, PatchVerificationReport | None, str]:
    """Atomically applies anchor patch with mandatory closed-loop verify-patch gate and auto-rollback (Level-3).

    Args:
        root: Workspace repository root directory.
        patch_payload: Dict containing AnchorPatchPayload.
        verify_preset: Verification preset to execute ('ci', 'code', 'skill', etc.). Default: 'ci'.
        timeout: Execution timeout for verification commands.
        keep_backups: Whether to preserve .bak backup files on verification pass.

    Returns:
        tuple of (success: bool, report: PatchVerificationReport | None, summary: str).
    """
```

**Quy trình 4 pha (4-Phase Autonomous Execution)**:
- **Pha 1 (Validation)**: Chạy `apply_anchor_patch(root, patch_payload, dry_run=True)`. Bắt lỗi `ValueError` $\to$ nếu lỗi trả về `(False, None, f"Pre-apply validation failed: {exc}")`.
- **Pha 2 (Commit with Backups)**: Chạy `modified_paths = apply_anchor_patch(root, patch_payload, backup=True)`.
- **Pha 3 (Closed-Loop Verify)**: Chạy `report = verify_patch_execution(preset=verify_preset, cwd=root, timeout=timeout)`.
- **Pha 4 (Decision & Self-Healing)**:
  - Nếu `report.all_passed`:
    - Nếu không `keep_backups`: Xóa các tệp `.bak`.
    - Trả về `(True, report, f"Patch successfully applied and verified with preset '{verify_preset}'.")`.
  - Nếu `not report.all_passed`:
    - **Tự động khôi phục (Rollback)**: Đọc lại nội dung từ từng tệp `.bak` và ghi đè lại vào các tệp trong `modified_paths`.
    - Dọn sạch tệp `.bak`.
    - Trả về `(False, report, f"Verification failed ({report.failed_count}/{report.total_commands} commands failed). Workspace rolled back cleanly.")`.

### 3.2. Cập Nhật CLI `ccba-harness peer-dispatch`
Vị trí: `packages/ccba-harness/src/ccba_harness/cli.py`.

Bổ sung các tham số:
- `--auto-apply`: Tự động áp dụng và kiểm định bản vá nếu output chứa `AnchorPatchPayload`.
- `--verify-preset`: Preset kiểm định sau khi áp dụng (mặc định: `ci`).
- `--keep-backups`: Giữ lại các tệp sao lưu `.bak`.

**Logic xử lý trong `run_peer_dispatch_cli`**:
```python
    if args.auto_apply:
        # 1. Trích xuất anchor payload từ output file
        content, _ = safe_read_and_hash(output_file)
        payload = extract_anchor_payload(content or "")
        if not payload:
            print("[FAIL] --auto-apply requested but output contains no AnchorPatchPayload.", file=sys.stderr)
            return 1
            
        # 2. Thực thi auto_apply_and_verify_patch
        success, report, msg = auto_apply_and_verify_patch(
            root=prompt_path.parent.parent.parent, # hoặc cwd
            patch_payload=payload,
            verify_preset=args.verify_preset or "ci",
            keep_backups=args.keep_backups,
        )
        
        # 3. Cập nhật phán quyết vào file output
        if success:
            # Thăng cấp verdict lên FINAL_ACCEPT / GATE_PASS
            ...
            return 0
        else:
            # Ghi nhận GATE_FAIL kèm điều kiện thất bại
            ...
            return 4 # GATE_FAIL
```

### 3.3. Cập Nhật CLI `ccba-harness peer-co-review`
- Bổ sung `--auto-apply`:
  - Chỉ cho phép nếu Consensus Verdict là `APPROVE` / `APPROVE_PLAN` / `FINAL_ACCEPT` và `risk_score < 4` và không có bất kỳ điều kiện `blocking=True` nào.
  - Nếu có điều kiện chặn: Từ chối auto-apply và thoát với mã `2` (`APPROVE_WITH_CONDITIONS`) kèm cảnh báo.

---

## 4. Kế Hoạch Kiểm Thử Đối Kháng & Đảm Bảo Chất Lượng (QA / Testing)

1. **Unit Tests (`packages/ccba-harness/tests/test_peer_auto_apply.py`)**:
   - `test_auto_apply_success_flow`: Giả lập patch hợp lệ, mock `verify_patch_execution` trả về `all_passed=True` $\to$ kiểm tra tệp đích được sửa, file `.bak` được dọn sạch, trả về `success=True`.
   - `test_auto_apply_verify_failure_triggers_clean_rollback`: Giả lập patch hợp lệ nhưng mock `verify_patch_execution` trả về `all_passed=False` $\to$ kiểm tra **100% nội dung gốc của tệp đích được phục hồi**, không bị lưu trạng thái hỏng.
   - `test_auto_apply_pre_validation_sha_mismatch`: Giả lập SHA-256 sai $\to$ dừng ngay từ Pha 1, không sửa file, không tạo backup.
   - `test_auto_apply_cli_flag_integration`: Kiểm tra luồng gọi từ CLI `peer-dispatch --auto-apply` và `peer-co-review --auto-apply`.
   - `test_auto_apply_blocks_on_fake_approve_or_risk`: Xác nhận từ chối auto-apply khi consensus có `blocking=True`.
2. **Benchmark & Regression Test**:
   - Đảm bảo toàn bộ 70 unit tests hiện tại tiếp tục pass 100%.
   - Đảm bảo thời gian chạy của test suite mới dưới 1.5 giây.
3. **CI Matrix Parity**:
   - Chạy `python -m ccba_harness verify-patch --preset ci` đạt 6/6 passed.

---

## 5. Các Vấn Đề Cần Tham Vấn Đối Kháng Với Grok-4.7 (Peer Review Questions)

Trước khi viết code, Antigravity sẽ gửi bản kế hoạch này tới Grok-4.7 xhigh qua `peer-dispatch --profile audit_plan` để phản biện 3 vấn đề kiến trúc:
1. **Root Directory Resolution**: Khi gọi từ CLI, thư mục `root` nên mặc định là `Path.cwd()` hay suy diễn từ vị trí của `prompt-file`?
2. **Backup Extension Collision**: Việc dùng đuôi cố định `.bak` có nguy cơ trùng lặp nếu tệp gốc đã là `.bak` không? Có nên dùng `.bak.<timestamp>` hoặc UUID tạm không?
3. **Exit Code Semantics**: Khi `verify-patch` fail và kích hoạt rollback sạch sẽ, mã thoát CLI nên là `4` (`GATE_FAIL`) hay `5` (`HANDOFF`)?

---

*Bản kế hoạch được xây dựng tuân thủ nghiêm ngặt Hiến pháp Nền tảng CCBA (ADR-0058, ADR-0061, ADR-0065).*


---

## 2. Định Dạng Đầu Ra Bắt Buộc (Mandatory Output Format)

Bắt đầu NGAY LẬP TỨC bằng YAML Frontmatter (không có bất kỳ ký tự nào trước dấu `---`):



Tiếp theo là phần nhận xét chi tiết, trả lời 3 câu hỏi kiến trúc và chỉ ra các kẽ hở/rủi ro tiềm ẩn (nếu có).
