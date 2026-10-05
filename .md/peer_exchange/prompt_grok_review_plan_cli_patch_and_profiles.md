---
request_id: "req-plan-cli-patch-profiles-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Kế hoạch Triển khai CLI apply-anchor-patch & Mở rộng Level-2 Peer Profiles"
timestamp: "2026-10-05T21:08:00+07:00"
source_documents: []
output_path: ".md/peer_exchange/grok_review_plan_cli_patch_and_profiles.md"
context: "Phản biện đối kháng kế hoạch kỹ thuật chi tiết. Ngữ cảnh đã đầy đủ 100% trong prompt, không cần quét đọc file trên đĩa."
---

# 🎯 Yêu Cầu Phản Biện Đối Kháng: Kế Hoạch Triển Khai CLI apply-anchor-patch & Mở Rộng Peer Profiles

> ⚠️ **Chỉ Dẫn Quan Trọng Cho Grok**: Toàn bộ thiết kế mã nguồn, schema và CLI interface đã được trích xuất đầy đủ, độc lập trong prompt này. Grok **KHÔNG CẦN** gọi các công cụ `read_file`, `list_dir`, `grep` để quét đĩa nhằm tiết kiệm ngân sách turns. Hãy tập trung thẩm tra logic thiết kế bên dưới và xuất ngay báo cáo phản biện kèm khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra!

Chào Grok, Antigravity và User đã thảo luận và thống nhất về các bước tiếp theo sau khi dogfooding thành công giao thức Level-2 Peer Delegation (PR #481).

Trước khi tiến hành viết mã trên nhánh mới, Antigravity gửi toàn văn bản kế hoạch kỹ thuật chi tiết dưới đây để Grok thẩm tra, phản biện đối kháng (adversarial review) và đưa ra phán quyết (`APPROVE_PLAN` / `REVISE_PLAN` / `REJECT_PLAN`):

---

## 📋 Toàn Văn Bản Kế Hoạch Kỹ Thuật (Detailed Implementation Plan)

### 1. Mục tiêu (Goals)
1. **Tích hợp CLI Subcommand `apply-anchor-patch`**:
   - Cho phép dev/agent áp dụng nhanh patch từ Grok bằng lệnh terminal:
     `ccba-harness apply-anchor-patch --patch-file <path> [--root <dir>] [--dry-run] [--json]`
   - Cung cấp aliases ngắn gọn: `peer-apply`, `apply-patch`.
   - Tự động bóc tách payload qua `extract_anchor_payload` từ cả file markdown lẫn raw JSON.
2. **Nâng cấp `apply_anchor_patch` với chế độ `dry_run`**:
   - Chạy toàn bộ Phase 1 (Fail-Fast: kiểm tra path traversal ngoài root, đối soát SHA-256 khớp 100%, kiểm tra chuỗi neo xuất hiện duy nhất 1 lần, chuẩn bị nội dung thay thế).
   - Nếu `dry_run=True`: Trả về danh sách `target_file` đã kiểm tra thành công mà KHÔNG thực hiện Phase 2 (ghi đĩa).
3. **Mở rộng danh mục Profiles (`PeerExecutionProfile`)**:
   - Bổ sung `code_review`:
     - Target model: `gemini-38-flash` (gateway) / `grok-4.7-build-fast` (cloud).
     - `max_turns: 6`.
     - Tools: `["read_file", "grep", "list_dir"]`.
     - Disallowed: `["run_terminal_command", "write_file", "search_replace", "spawn_subagent"]`.
     - Chuyên thẩm định code diff/PR theo 10 Bugbot Invariants.
   - Bổ sung `arch_audit`:
     - Target model: `grok-4.7` (cloud) / `gemini-38-flash` (gateway).
     - `max_turns: 8`, `reasoning_effort: "xhigh"`.
     - Tools: `["read_file", "grep", "list_dir"]`.
     - Disallowed: `["run_terminal_command", "write_file", "search_replace", "spawn_subagent"]`.
     - Chuyên đối soát kiến trúc ADR, Seam boundaries, Platform-Aware KISS.
4. **Đồng bộ hóa & Đối soát**:
   - Khai báo Public Deep Seams và CLI commands trong `packages/ccba-harness/AGENTS.md`.
   - Unit tests mở rộng trong `packages/ccba-harness/tests/test_peer.py` đạt 100% pass, SLA < 2.0s.
   - Vượt qua bộ kiểm định cứng: `verify-patch --preset code` và `compile_catalog.py --check`.

---

### 2. Thiết kế chi tiết mã nguồn

#### A. Trong `packages/ccba-harness/src/ccba_harness/peer.py`:
```python
PeerExecutionProfile = Literal[
    "audit_plan",
    "agentic_code",
    "patch_fast",
    "code_review",
    "arch_audit",
]

PROFILE_SPECS: dict[str, dict[str, Any]] = {
    ...
    "code_review": {
        "model": "gemini-38-flash",  # ccba:allow-raw-model
        "fallback_model": "grok-4.7-build-fast",  # ccba:allow-raw-model
        "max_turns": 6,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": [
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
        "reasoning_effort": None,
        "timeout": 300.0,
    },
    "arch_audit": {
        "model": "grok-4.7",  # ccba:allow-raw-model
        "fallback_model": "gemini-38-flash",  # ccba:allow-raw-model
        "max_turns": 8,
        "tools": ["read_file", "grep", "list_dir"],
        "disallowed_tools": [
            "run_terminal_command",
            "search_replace",
            "write_file",
            "spawn_subagent",
        ],
        "reasoning_effort": "xhigh",
        "timeout": 600.0,
    },
}

def apply_anchor_patch(
    root: Path,
    payload: AnchorPatchPayload | dict[str, Any],
    dry_run: bool = False,
) -> list[Path]:
    ...
    if dry_run:
        return [target_file for target_file, _ in prepared_writes]

    # Phase 2: Atomic commit of all prepared changes
    modified_paths: list[Path] = []
    for target_file, new_content in prepared_writes:
        atomic_write_text(target_file, new_content)
        modified_paths.append(target_file)
    return modified_paths
```

#### B. Trong `packages/ccba-harness/src/ccba_harness/cli.py`:
- `run_apply_anchor_patch_cli`:
  - Đọc file từ `--patch-file`.
  - Gọi `extract_anchor_payload()`. Báo lỗi rõ ràng nếu file không hợp lệ hoặc thiếu payload.
  - Gọi `apply_anchor_patch(root, payload, dry_run=args.dry_run)`.
  - Khi `--json` được bật: Xuất JSON cấu trúc `{"status": "OK" | "DRY_RUN_OK", "modified_files": [...], "count": N}`.
  - Xử lý các ngoại lệ `ValueError` bắt lỗi bảo mật (path traversal, sha256 mismatch, non-unique anchor) và trả exit code 1 kèm thông điệp rõ ràng.
- Đăng ký subcommand và aliases `["apply-anchor-patch", "peer-apply", "apply-patch"]` trong `main()`.

---

## 🔍 Câu Hỏi Đặt Ra Cho Grok:
1. Bạn có phát hiện thấy bất kỳ edge-case nào về mặt an toàn luồng (concurrency) hoặc tính toàn vẹn (integrity) của `apply-anchor-patch` khi chạy qua CLI không?
2. Bộ phân loại công cụ (`tools` vs `disallowed_tools`) cho `code_review` và `arch_audit` đã đủ chặt chẽ và an toàn để ngăn ngừa accidental mutation chưa?
3. Bạn có khuyến nghị bổ sung thêm cờ nào cho CLI `apply-anchor-patch` (ví dụ: `--backup`, `--quiet`, v.v.) không?
4. Đánh giá tính khả thi và phán quyết cuối cùng của bạn đối với bản kế hoạch này.
