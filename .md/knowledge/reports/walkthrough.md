# Báo Cáo Nghiệm Thu Hoàn Tất: Sprint 2 — Maskara Diff Sanitizer, Two-way Door Auto-Approval & Live Gate Verification (Issue #408)

> **Mã công việc**: Issue #408  
> **Pull Request**: [#409](https://github.com/vvChu/ccba-agent-platform/pull/409) (`feat/issue-408-sprint-2-ci-gates`)  
> **Trạng thái CI Remote**: ✅ 8/8 checks PASSED (100% Green)

---

## 1. Kết Quả Triển Khai Thực Tế

### 1.1. Sửa Lỗi Cốt Lõi Multi-byte UTF-8 trong `ccba-maskara`
- **Vấn đề phát hiện**: Trước đó hàm `scan_text()` trả về character offset trên Python string, trong khi `apply_raw_redactions()` cắt lát trên `bytearray(raw_bytes)`. Khi văn bản chứa tiếng Việt có dấu hoặc emojis, độ dài byte lớn hơn độ dài ký tự dẫn đến cắt lẹm text và làm lộ phần đuôi của secret.
- **Giải pháp**:
  - [`_scanner.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-maskara/src/ccba_maskara/_scanner.py): Tính toán bổ sung `byte_start` và `byte_end` vào dictionary finding. Sửa hàm `redact_text()` thực hiện thay thế trực tiếp trên chuỗi (`str`) theo thứ tự từ cuối lên đầu (`reversed(findings)`).
  - [`_redactor.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-maskara/src/ccba_maskara/_redactor.py): Cập nhật `apply_raw_redactions()` ưu tiên sử dụng `byte_start, byte_end`.
  - [`test_scanner.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-maskara/tests/test_scanner.py): Bổ sung bài kiểm tra văn bản tiếng Việt và emojis (`test_redact_text_multibyte_vietnamese_and_emojis`).

### 1.2. Công Cụ Maskara Diff Sanitizer & Pre-merge Audit Gate
- **Tệp mới**: [`scripts/governance/sanitize_review_diff.py`](file:///home/vvc/ccba/ccba-agent-platform/scripts/governance/sanitize_review_diff.py)
  - Hỗ trợ nạp diff từ: đường dẫn file, standard input (`sys.stdin`), hoặc git revision range (`--base origin/main --head HEAD`).
  - Cờ `--check`: Quét và phát hiện secret trong diff; nếu phát hiện, in danh sách vi phạm ra `stderr` và thoát với mã 1 (Hard Gate).
  - Cờ `-o / --output <file>`: Xuất file diff đã che giấu (redacted) toàn bộ credentials để nạp vào AI Reviewers an toàn.
  - Cờ `--report-json <file>`: Xuất báo cáo cấu trúc JSON.
- **Unit Test Suite**: [`tests/governance/test_sanitize_review_diff.py`](file:///home/vvc/ccba/ccba-agent-platform/tests/governance/test_sanitize_review_diff.py) (9/9 tests PASS).

### 1.3. Nâng Cấp Workflow `pr-verifier.yml` & Rào Chắn Two-way Door
- **Defense-in-Depth Triage**:
  - *Denylist tuyệt đối*: Chặn `*AGENTS.md`, `.agents/**`, `.github/**`, `docs/adr/**`, `docs/rules/**`, `docs/governance/**`, `packages/**`, `scripts/**`, và các tệp cấu hình/thực thi (`*.py`, `*.sh`, `*.yml`, `*.yaml`, `*.json`, `*.toml`, `*.lock`, `Dockerfile`, `Makefile`).
  - *Allowlist nghiêm ngặt*: Chỉ chấp nhận tệp thuần tài liệu ghi chép nằm trong `.md/**`, `docs/**` (trừ governance/adr), `README.md`, `WALKTHROUGH.md`, `CONTRIBUTING.md`.
- **Pre-Verifier Gate (Secret Leak Blocker)**: Chạy `sanitize_review_diff.py --check` chặn đứng commit lộ credentials trước khi cho phép merge.
- **Cơ chế Auto-Approval**: Bổ sung `addLabels('two-way-door')` và `createReview('APPROVE')` an toàn qua REST API bọc trong `try/catch`.
- **Deduplication Comment**: Nâng `per_page: 100` khi truy vấn comments cũ, giúp bot cập nhật in-place thay vì tạo comment mới.

---

## 2. Bằng Chứng Thực Nghiệm Live (Acceptance Verification)

### Bảng đối chiếu Tiêu chí Nghiệm thu (Issue #408)

| Tiêu chí | Trạng thái | Bằng chứng thực nghiệm |
| :--- | :---: | :--- |
| **AC1: Live PR Verification** | ✅ PASS | Đã mở **[PR #409](https://github.com/vvChu/ccba-agent-platform/pull/409)**. Bot đã đăng và cập nhật in-place bảng báo cáo `### 🛡️ CCBA PR Quality Gate Report` (xem chi tiết bên dưới). |
| **AC2: Maskara Diff Sanitizer** | ✅ PASS | 20/20 unit tests (`test_scanner.py` & `test_sanitize_review_diff.py`) đạt PASS trong 0.28s. Khi commit đầu tiên chứa mock secret thô, bot đã phát hiện và chặn merge thành công trước khi được sửa thành dynamic mock. |
| **AC3: Two-way Door Fast Path** | ✅ PASS | Logic Denylist/Allowlist hoạt động chính xác (`is_two_way_door=false` trên PR #409 vì PR có chứa code/workflows). Nhãn `two-way-door` đã được khởi tạo sẵn trên remote. |
| **AC4: Governance Parity** | ✅ PASS | Lệnh `python -m ccba_harness verify-patch --preset ci` hoàn tất 6/6 checks (Exit 0). Cập nhật `PLATFORM.md`. Toàn bộ 8 checks trên GitHub Actions đều Green. |

### Telemetry Trực Tiếp từ Bot trên PR #409

```markdown
### 🛡️ CCBA PR Quality Gate Report

| Metric | Assessment |
| :--- | :--- |
| **Danger Triage Level** | `HIGH` (🔴 Hard Blocking Gate) |
| **Logic Diff Size** | `543 LOC` ⚠️ *(Exceeds 300 LOC micro-PR budget)* |
| **Two-way Door Fast Path** | `false` 🔒 *(Standard review flow)* |
| **Maskara Secret Audit** | ✅ PASSED (Clean) |
| **Verifier Status** | ✅ PASSED (Exit 0) |

> ⚠️ **Micro-PR Notice:** This PR introduces 543 lines of logic changes. Per CCBA guidelines, please consider splitting large changes into smaller tracer-bullet vertical slices (≤ 200 LOC per PR) to reduce review fatigue and conflict risk.
```

---

## 3. Danh Sách Tệp Thay Đổi

- `.github/workflows/pr-verifier.yml`: Tích hợp Maskara gate, Two-way Door Defense-in-Depth, in-place comment deduplication và auto-approval.
- `PLATFORM.md`: Đăng ký `sanitize_review_diff.py` trong cấu trúc nền tảng.
- `packages/ccba-maskara/src/ccba_maskara/_scanner.py`: Sửa lỗi tính toán `byte_start`, `byte_end` và chuỗi redaction.
- `packages/ccba-maskara/src/ccba_maskara/_redactor.py`: Cập nhật `apply_raw_redactions()` theo byte offset.
- `packages/ccba-maskara/tests/test_scanner.py`: Test case Unicode tiếng Việt và emojis.
- `scripts/governance/sanitize_review_diff.py`: Script CLI sanitization và audit gate.
- `tests/governance/test_sanitize_review_diff.py`: Bộ unit test 9 kịch bản cho diff sanitizer.
