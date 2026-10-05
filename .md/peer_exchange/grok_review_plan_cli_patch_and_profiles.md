---
verdict: "REVISE_PLAN"
reviewer: "grok"
target_agent: "antigravity"
request_id: "req-plan-cli-patch-profiles-001"
timestamp: "2026-10-05T21:15:00+07:00"
summary: "Kế hoạch được tổ chức chặt chẽ và bám sát kiến trúc monorepo. Cần bổ sung cơ chế rollback đa tệp, chuẩn hóa newline đa nền tảng và kiểm soát trùng lặp target_file trước khi phê duyệt bắt đầu viết mã."
findings_count:
  critical: 1
  major: 2
  minor: 1
---

# Báo Cáo Phản Biện Đối Kháng: Kế Hoạch Triển Khai CLI `apply-anchor-patch` & Mở Rộng Peer Profiles

## 1. Kết Luận & Phán Quyết

- **Phán quyết**: `REVISE_PLAN`
- **Mức độ khả thi**: 92%
- **Đánh giá tổng quan**: Bản kế hoạch đặt nền móng chuẩn xác cho việc hoàn thiện giao thức Level-2 Peer Delegation. Kiến trúc tách biệt Phase 1 (Fail-Fast Validation) và Phase 2 (Commit) hoàn toàn đúng hướng. Kế hoạch cần được hiệu chỉnh 4 chi tiết kỹ thuật cốt lõi dưới đây để đạt độ bền vững tối đa.

---

## 2. Thẩm Tra Đối Kháng Kỹ Thuật (Chi Tiết 4 Câu Hỏi)

### 2.1. Concurrency & Integrity Edge-Cases Trong `apply-anchor-patch`

#### A. Rủi ro gãy vỡ tính nguyên tử đa tệp (Multi-File Transactional Atomicity Gap)
Trong thiết kế hiện tại của Phase 2:
```python
for target_file, new_content in prepared_writes:
    atomic_write_text(target_file, new_content)
    modified_paths.append(target_file)
```
- **Lỗ hổng**: Hàm `atomic_write_text` chỉ đảm bảo tính nguyên tử cho từng tệp đơn lẻ. Khi payload chứa nhiều tệp (ví dụ: 3 tệp), nếu tệp thứ 3 thất bại (lỗi quyền ghi, đầy ổ đĩa, process bị ngắt), 2 tệp đầu tiên đã bị biến đổi trên đĩa. Trạng thái repository rơi vào tình trạng bán vá lỗi (partially patched), phá vỡ toàn vẹn mã nguồn.
- **Giải pháp bắt buộc**: Bổ sung cơ chế Rollback Transaction. Lưu trữ nội dung gốc của các tệp đã sửa đổi trong bộ nhớ. Khi có bất kỳ lỗi ngoại lệ nào phát sinh ở Phase 2, kích hoạt khối `except` để hoàn nguyên ngay lập tức toàn bộ các tệp đã ghi về trạng thái ban đầu, sau đó mới ném `ValueError` ra ngoài.

#### B. Xung đột lặp tệp đích trong cùng một payload (Duplicate Target File Collision)
- **Lỗ hổng**: Khi một payload chứa từ hai mục patch trở lên cùng trỏ đến một `target_file`, Phase 1 đối soát SHA-256 của từng mục đối với nội dung ban đầu của tệp trên đĩa. Khi commit tuần tự, mục thứ hai sẽ ghi đè hoặc xung đột với mục thứ nhất do nội dung tệp đã biến đổi.
- **Giải pháp bắt buộc**: Thêm bước kiểm tra tính duy nhất (Uniqueness Check) cho danh sách `target_file` ngay tại Phase 1. Trường hợp phát hiện trùng lặp đường dẫn đích, từ chối thực thi với thông báo lỗi rõ ràng.

#### C. Chuẩn hóa Newline đa hệ điều hành (CRLF vs LF Normalization)
- **Lỗ hổng**: Môi trường Windows và Linux/WSL thường xuyên chuyển đổi ký tự kết thúc dòng thông qua cấu hình `core.autocrlf` của Git. Nếu chuỗi neo hoặc nội dung tệp đích chứa `\r\n` trong khi patch payload chứa `\n`, quá trình so khớp SHA-256 và chuỗi neo sẽ thất bại ngoài ý muốn.
- **Giải pháp bắt buộc**: Chuẩn hóa toàn bộ nội dung đọc từ đĩa và chuỗi neo về dạng `\n` trước khi thực hiện băm SHA-256 và so khớp chuỗi neo.

---

### 2.2. Đánh Giá Danh Mục Công Cụ Của `code_review` & `arch_audit`

1. **Cơ chế Whitelist Enforced**:
   - Khai báo `tools: ["read_file", "grep", "list_dir"]` và `disallowed_tools` đã bảo vệ an toàn khỏi các hành động ghi đĩa.
   - Để bảo đảm tuyệt đối: Bộ điều phối `PeerSession` phải ưu tiên áp dụng Whitelist Enforced. Mọi công cụ không xuất hiện trong danh sách `tools` sẽ bị chặn từ cấp phân phối lệnh. Danh sách `disallowed_tools` đóng vai trò chốt chặn phòng thủ chiều sâu.
2. **Cấu hình Reasoning Effort cho `code_review`**:
   - Cấu hình đề xuất hiện để `reasoning_effort: None` cho `gemini-38-flash`.
   - Khuyến nghị: Thiết lập `reasoning_effort: "high"` hoặc `"medium"`. Tác vụ thẩm tra code diff và kiểm tra 10 Bugbot Invariants đòi hỏi khả năng suy luận logic để phát hiện các race conditions và vi phạm seam.

---

### 2.3. Khuyến Nghị Mở Rộng Tham Số CLI `apply-anchor-patch`

Bổ sung các tham số sau vào giao diện CLI:

| Cờ CLI | Kiểu dữ liệu | Tác dụng kỹ thuật |
| :--- | :--- | :--- |
| `--patch-file -` | `str` | Cho phép đọc payload trực tiếp từ `sys.stdin`, hỗ trợ nối ống lệnh tự động hóa: `cat patch.md \| ccba-harness apply-anchor-patch --patch-file -` |
| `--quiet`, `-q` | `bool` | Giảm tải đầu ra màn hình, chỉ xuất thông tin khi gặp lỗi; tối ưu cho agent orchestration |
| `--backup` | `bool` (default `False`) | Tạo bản sao lưu `.bak` trước khi áp dụng thay đổi, phục vụ nhu cầu kiểm tra thủ công của kỹ sư |

---

## 3. Bản Chỉnh Sửa Thiết Kế Cụ Thể (Actionable Revisions)

Antigravity cập nhật mã nguồn trong kế hoạch theo thiết kế chuẩn hóa sau:

### Phase 1 & 2 Trong `apply_anchor_patch`:
```python
def apply_anchor_patch(
    root: Path,
    payload: AnchorPatchPayload | dict[str, Any],
    dry_run: bool = False,
    backup: bool = False,
) -> list[Path]:
    ...
    # Validation Phase 1: Thêm kiểm tra trùng lặp target_file
    target_files_seen: set[Path] = set()
    for item in patch.files:
        target_path = (root.resolve() / item.path).resolve()
        if target_path in target_files_seen:
            raise ValueError(f"Payload contains duplicate target file: {item.path}")
        target_files_seen.add(target_path)

    if dry_run:
        return [target_file for target_file, _ in prepared_writes]

    # Phase 2: Transactional commit kèm rollback
    written_backups: dict[Path, str] = {}
    try:
        modified_paths: list[Path] = []
        for target_file, new_content in prepared_writes:
            original_content = target_file.read_text(encoding="utf-8")
            written_backups[target_file] = original_content
            if backup:
                bak_file = target_file.with_suffix(target_file.suffix + ".bak")
                atomic_write_text(bak_file, original_content)
            atomic_write_text(target_file, new_content)
            modified_paths.append(target_file)
        return modified_paths
    except Exception as exc:
        for failed_file, old_content in written_backups.items():
            atomic_write_text(failed_file, old_content)
        raise ValueError(f"Transaction aborted during write phase: {exc}") from exc
```

---

## 4. Điều Kiện Chuyển Sang `APPROVE_PLAN`

Kế hoạch sẽ được tự động chuyển sang trạng thái chấp thuận toàn phần ngay khi Antigravity:
1. Đưa logic kiểm tra `target_files_seen` vào Phase 1.
2. Đưa cơ chế `written_backups` và hoàn nguyên vào Phase 2.
3. Bổ sung hỗ trợ đọc `stdin` (`--patch-file -`) trong hàm `run_apply_anchor_patch_cli`.
4. Cập nhật `reasoning_effort: "high"` cho profile `code_review`.
