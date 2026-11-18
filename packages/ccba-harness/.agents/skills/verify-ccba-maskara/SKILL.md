---
name: verify-ccba-maskara
description: Bộ kỹ năng kiểm định tự động In-Process 5 khối (Profile B) & Statechart Bug-Path Replay cho package ccba-maskara (ADR-0009 / ADR-0044 / ADR-0058).
user-invocable: true
command: /verify-ccba-maskara
when_to_use: Dùng khi cần chạy kiểm định tự động In-Process, kiểm chứng máy trạng thái MaskaraScanner/apply_raw_redactions/resolve_targets hoặc bảo trì sai lệch (drift) cho package ccba-maskara.
category: verification
bundle: _core
tier: kernel
scope: spoke
disable-model-invocation: true
gpi:
  s: 4.0
  k: 3.5
  a: 2.0
  p: 1.0
metadata:
  author: CCBA
  version: 1.0.0
sync_commit: "646cf2d79b382ba8e33bb2540676c272bfc99435"
covered_sha256:
  packages/ccba-maskara/src/ccba_maskara/__init__.py: "b91f469756a712b010193590ca7d524e318a8bafae181917014493b7370830ca"
  packages/ccba-maskara/src/ccba_maskara/_scanner.py: "5dcd85fcd4f5c9e1ab6a0d610706c6d82f5090d0cb04fe2ee9444fd5e59d1536"
  packages/ccba-maskara/src/ccba_maskara/_redactor.py: "1384313848736d9569cc69d1d7bc13cb47b2da0382b838151c54d53e34b3e895"
  packages/ccba-maskara/src/ccba_maskara/_rules.py: "4afe8ba55d8ad0a1f2b6ad4e382637ed3cb788a17f8d3eb759aa101442d5e864"
  packages/ccba-maskara/src/ccba_maskara/_locator.py: "e568f2801703a890835675541fa3cd5a5c2d128b6e528063b6c21f677992891f"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - packages/ccba-maskara/src/ccba_maskara/__init__.py
  - packages/ccba-maskara/src/ccba_maskara/_scanner.py
  - packages/ccba-maskara/src/ccba_maskara/_redactor.py
  - packages/ccba-maskara/src/ccba_maskara/_rules.py
  - packages/ccba-maskara/src/ccba_maskara/_locator.py
triggers:
  - verify-ccba-maskara
  - kiểm định ccba-maskara
  - test maskara statechart
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-maskara`

Bộ kỹ năng kiểm định tự động chuyên biệt cho package `ccba-maskara` (`MaskaraScanner`, `detect_secrets_in_text`, `redact_secrets_in_text`, `apply_raw_redactions`, `backup_and_write`, `is_binary`), được khởi tạo theo **Profile B (In-Process Library)** của `ccba-create-verification-skill` `v1.4.0` và chuẩn **Pstack `statechart` `v0.15.42`**. Toàn bộ mã kiểm định cô lập trong `packages/ccba-harness/.agents/skills/verify-ccba-maskara/harness/`.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Bảo vệ trực tiếp các Public Deep Seams của `ccba_maskara` (`MaskaraScanner`, `detect_secrets_in_text`, `redact_secrets_in_text`, `redact_secrets_and_pii`, `apply_raw_redactions`, `backup_and_write`, `is_binary`, `REGEX_PATTERNS`, `PII_REGEX_PATTERNS`) tương ứng với kỹ năng `ccba-maskara`.
- **Version Anchor (`sync_commit` & `covered_sha256`)**: Neo tại commit PR-2 `646cf2d79b382ba8e33bb2540676c272bfc99435` kèm mã băm SHA-256 chuẩn hóa LF bảo vệ toàn bộ `5` tệp `covered_paths`.
- **Giới Hạn Phạm Vi (`Scope & Limitations`)**:
  - Việc kiểm chứng bằng `use_llm=True` cô lập qua mock `ccba_ai.ai.chat` (`_scanner.py:213-237`), không gọi mạng tới LiteLLM Gateway thực.
  - Khi `scan_file` gặp symlink, thư mục, tệp nhị phân, tệp vượt `25 MB` (`MAX_FILE_SIZE`), hoặc tên tệp không thuộc nhóm session/config text (`_scanner.py:343-348`), hàm trả về `skipped=1` thay vì ném ngoại lệ (`bug_path_2`).

---

## Kiến Trúc 5 Khối Kiểm Định In-Process (`Profile B`)

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra 5 tệp covered_paths ccba-maskara)"] --> B2["2. In-Process Sandbox\n(TemporaryDirectory + CCBA_AI_MOCK=1)"]
    B2 --> B3["3. Seam Readiness Barrier\n(Nạp Public Seams & REGEX_PATTERNS không sleep)"]
    B3 --> B4["4. Evidence-Capture Pytest\n(Hợp đồng 6 tính năng + 4 Statechart Bug-Path Replay)"]
    B4 --> B5["5. Guaranteed Cleanup\n(Dọn sạch TemporaryDirectory & Registry trong finally)"]
```

### 1. Clean-Slate Pre-flight
- Xác nhận đủ `5` tệp trong `covered_paths` tồn tại trên đĩa và `ccba_maskara.__init__.py` không sinh ngoại lệ khi kiểm tra khởi tạo.

### 2. In-Process Sandbox Isolation
- Khởi tạo vùng làm việc tạm `TemporaryDirectory(prefix="verify_ccba_maskara_")`, thiết lập `PYTHONPATH` và `CCBA_AI_MOCK=1` mà **không mở cổng TCP hay dựng HTTP dummy server**.

### 3. Deterministic Seam Readiness Barrier
- Kiểm tra nạp thẳng Public Deep Seams trong `ccba_maskara.__all__` (`MaskaraScanner`, `detect_secrets_in_text`, `redact_secrets_in_text`, `apply_raw_redactions`, `backup_and_write`, `is_binary`, `REGEX_PATTERNS`) bằng lệnh con Python sạch; cấm dùng `time.sleep(N)`.

### 4. Evidence-Capture Pytest & Statechart `v0.15.42` (`Bug-Path Replay`)
- Thực thi `test_maskara_suite.py` đối chiếu toàn bộ `6` tính năng trong `features/INDEX.md` và mô hình hóa luồng chuyển trạng thái bằng `stateDiagram-v2` ($18 \le 20$ cạnh, đủ 4 lớp kiểm định):

```mermaid
stateDiagram-v2
  classDef breaks fill:#f8d0d0,stroke:#b00020,stroke-width:2px,color:#3b0008
  classDef mayBreak fill:#fff3cd,stroke:#8a6d00,stroke-width:2px,color:#3d3200
  classDef bugPath fill:#fde2c8,stroke:#c2410c,stroke-width:2px,color:#3b1204
  classDef repeats fill:#e6e6fa,stroke:#4c1d95,stroke-width:2px,color:#1e1033

  state "ScannerReady: MaskaraScanner Khởi Tạo" as ScannerReady
  state "BREAKS: UnknownAgentRejected - ValueError" as UnknownAgentRejected
  state "BUG-PATH: TargetResolved - Phân Giải Đường Dẫn" as TargetResolved
  state "MAY-BREAK: FileSkippedGuard - Bỏ Qua Binary/Symlink/25MB" as FileSkippedGuard
  state "MAY-BREAK: GatewayErrorFailClosedTrue - Lỗi AI Mặc Định True" as GatewayErrorFailClosedTrue
  state "BUG-PATH: RedactionApplied - Thay Thế Byte An Toàn" as RedactionApplied
  state "MAY-BREAK: OverlappingSpanSkipped - Bỏ Qua Span Trùng/Tràn" as OverlappingSpanSkipped
  state "ScanCleanDone: Quét Sạch Không Lỗi" as ScanCleanDone
  state "RedactedDone: Backup & Ghi Đè Thành Công" as RedactedDone

  [*] --> ScannerReady
  ScannerReady --> UnknownAgentRejected: when resolve_targets receives unsupported agent
  ScannerReady --> TargetResolved: when targets resolved for scan
  TargetResolved --> FileSkippedGuard: when file is binary symlink or over 25MB
  TargetResolved --> RegexRuleLoop: when readable session or config text enters scan_text
  state "Quét Regex Theo Tập Luật" as RegexRuleLoop {
    state "REPEATS: RuleIter - Duyệt REGEX_PATTERNS" as RuleIter
    [*] --> RuleIter
    RuleIter --> RuleIter: when evaluating next regex pattern
  }
  RegexRuleLoop --> GatewayErrorFailClosedTrue: when use_llm gateway raises exception defaulting True
  RegexRuleLoop --> RedactionApplied: when findings passed to apply_raw_redactions
  RegexRuleLoop --> ScanCleanDone: when no unsafe secrets detected
  RedactionApplied --> OverlappingSpanSkipped: when span is out of bounds or overlaps prior edit
  RedactionApplied --> RedactedDone: when backup_and_write persists redacted bytes
  UnknownAgentRejected --> [*]
  FileSkippedGuard --> [*]
  GatewayErrorFailClosedTrue --> [*]
  OverlappingSpanSkipped --> [*]
  ScanCleanDone --> [*]
  RedactedDone --> [*]

  class UnknownAgentRejected breaks
  class FileSkippedGuard,GatewayErrorFailClosedTrue,OverlappingSpanSkipped mayBreak
  class TargetResolved,RedactionApplied bugPath
  class RuleIter repeats
```

**Danh sách đường dẫn phản chứng (`bug_path`) & bước ẩn bàn giao kèm sơ đồ:**
- `bug_path_1` (Unknown Agent Rejected — `ValueError`): `[{"from": "ScannerReady", "to": "UnknownAgentRejected", "when": "resolve_targets receives unsupported agent"}]`
- `bug_path_2` (Binary/Symlink/25MB File Guard Skip): `[{"from": "ScannerReady", "to": "TargetResolved", "when": "targets resolved for scan"}, {"from": "TargetResolved", "to": "FileSkippedGuard", "when": "file is binary symlink or over 25MB"}]`
- `bug_path_3` (Overlapping/Out-of-Bounds Span Skipped): `[{"from": "RegexRuleLoop", "to": "RedactionApplied", "when": "findings passed to apply_raw_redactions"}, {"from": "RedactionApplied", "to": "OverlappingSpanSkipped", "when": "span is out of bounds or overlaps prior edit"}]`
- `bug_path_4` (AI Gateway Exception Defaults `True`): `[{"from": "RegexRuleLoop", "to": "GatewayErrorFailClosedTrue", "when": "use_llm gateway raises exception defaulting True"}]`
- `hidden_steps` (lược bỏ để giữ ngân sách $\le 20$ cạnh):
  - `TargetResolved -> FileSkippedGuard` (khi `perform_scan` gặp thư mục gốc không tồn tại và ghi `warnings`).
  - `RuleIter -> ScanCleanDone` (khi `is_safe_or_template` lọc an toàn `SAFE_STRINGS` hoặc `_KNOWN_TOKEN_METRICS`).
- Cả 4 chuỗi `bug_path` được replay trực tiếp trên mã nguồn thật tại `test_maskara_suite.py`.

### 5. Guaranteed Cleanup
- Xóa toàn bộ thư mục tạm và khôi phục nguyên trạng cấu hình sandbox trong khối `finally:`.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Chạy Bộ Kiểm Định 5 Khối Cho `ccba-maskara`
```bash
.venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-maskara/harness/run_verify_maskara.py
```
- **Tiêu chí hoàn thành:** Toàn bộ `6` ca kiểm thử trong `test_maskara_suite.py` vượt qua 100%, thư mục tạm được giải phóng và lệnh thoát với `exit code 0`.

### Bước 2: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận `git diff --quiet` trên `packages/ccba-maskara`.
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `packages/ccba-maskara/src/ccba_maskara/_scanner.py` (ví dụ đảo điều kiện `is_safe_or_template` hoặc vô hiệu hóa kiểm tra `MAX_FILE_SIZE`), chạy lại `run_verify_maskara.py` để xác nhận bắt được lỗi (`exit code != 0`), hoàn nguyên sạch với `git checkout --`, và chạy lại xác nhận `exit code 0`.
- **Tiêu chí hoàn thành:** Bộ kiểm định bắt được đột biến ngữ nghĩa, mã nguồn hoàn nguyên 100% sạch sẽ và lần chạy nghiệm thu đạt `exit code 0`.
