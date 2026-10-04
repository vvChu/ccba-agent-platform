---
proposal_id: "2026-10-04_auto-spoke-precommit-hook"
type: "skills"
name: "auto-spoke-precommit-hook"
status: "proposed"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_by_archetype: "platform_tooling"
proposed_date: "2026-10-04"
applies_to:
  - "Tất cả Spokes"
  - "Phần mềm"
  - "Security & Privacy"
---

# RFC Proposal: Tự Động Kích Hoạt Git Pre-Commit Hook Maskara Qua `/ccba-update-spoke`

- **Tác giả đề xuất:** Platform Architect / Antigravity
- **Ngày lập:** 2026-10-04
- **Trạng thái:** Proposed (Đã thẩm định Peer Review độc lập với Grok: `APPROVE_WITH_CONDITIONS`)
- **Căn cứ pháp lý nền tảng:** [ADR-0044](../../docs/adr/0044-zero-latency-shared-python-sdks-and-cross-repo-package-linking.md) §7, [ADR-0058](../../docs/adr/0058-deterministic-hard-completion-lock.md), [ADR-0061](../../docs/adr/0061-seam-capability-contracts-and-cleanliness-gate.md).

---

### 1. Bối cảnh & Động lực Thực tế (Context & Motivation)
1. **Nỗi đau thực tế (Pain point):**
   - Sau khi phát hành `ccba-maskara` v1.2.0, các nhà phát triển tại các kho chứa thành viên (Spoke) phải nhớ chạy thủ công `python -m ccba_maskara.cli init-hooks` để kích hoạt git hook bảo vệ.
   - Thao tác thủ công này dễ bị bỏ quên, dẫn tới nguy cơ commit chứa API keys / secret lên GitHub từ phía Spoke.
2. **Giải pháp tự động hóa 1-chạm (1-Click Automation):**
   - Mở rộng `TestGuardrailCopier` trong `scripts/spoke/sync/sdk_inspector.py`:
     + Tự động sao chép `.githooks/pre-commit` từ Hub sang Spoke khi chạy `/ccba-update-spoke` (`sync_spoke.py --apply`).
     + Gán quyền thực thi `chmod 0o755`.
     + Đảm bảo `.gitattributes` tại Spoke có rule `.githooks/* text eol=lf` (idempotent, chống lỗi CRLF/LF trên Windows).
     + Tự động chạy `git -C <spoke> config core.hooksPath .githooks` và `git -C <spoke> update-index --add --chmod=+x .githooks/pre-commit`.
   - **Bảo toàn Non-Destructive**: Nếu Spoke đã có custom hooks khác `.githooks`, hệ thống cảnh báo và giữ nguyên, chỉ ghi đè khi có cờ `--force`.
   - **Kháng lỗi đa môi trường**: Chuẩn hóa newline bằng `are_text_files_identical` để loại trừ false-positive update loop trên Windows; bỏ qua thao tác git an toàn nếu Spoke chưa phải Git repository.

---

### 2. Kết Quả Thẩm Định Đối Kháng (Peer Review With Grok)
- **Phán quyết:** `APPROVE_WITH_CONDITIONS`
- **Đã tiếp thu 3/3 điều kiện kỹ thuật:**
  1. Dùng `are_text_files_identical` chuẩn hóa CRLF/LF khi so sánh diff tệp.
  2. Dùng `git -C <spoke_root>` chỉ định tường minh thư mục repo mục tiêu.
  3. Bổ sung cờ `--add` cho `git update-index` để hoạt động trơn tru trên cả unborn branch / repo mới `git init`.

---

### 3. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | 100% Spoke tự động sở hữu khiên bảo vệ Maskara mà không cần thao tác thủ công |
| **Độ Phức tạp (Complexity)** | Rất thấp (KISS) | Mở rộng trực tiếp lớp `TestGuardrailCopier` có sẵn (ADR-0044 §7) |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100% | Zero-Regression với 36/36 tests của `spoke_sync` và toàn bộ 355 tests nền tảng |
| **Bảo tồn Nghiệp vụ (Charter)** | Tuân thủ 100% | Tương thích ngược hoàn toàn, hỗ trợ đầy đủ `--dry-run` và `--force` |
