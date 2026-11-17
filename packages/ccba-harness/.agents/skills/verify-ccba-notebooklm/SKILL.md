---
name: verify-ccba-notebooklm
description: Bộ kỹ năng kiểm định tự động In-Process 5 khối (Profile B) & Statechart Bug-Path Replay cho package ccba-notebooklm (ADR-0009 / ADR-0044 / ADR-0058).
user-invocable: true
command: /verify-ccba-notebooklm
when_to_use: Dùng khi cần chạy kiểm định tự động In-Process, kiểm chứng máy trạng thái Maskara Gate / Registry / Quota GC / Summary Post-Processor hoặc bảo trì sai lệch (drift) cho package ccba-notebooklm.
category: verification
bundle: _software
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
sync_commit: "704f2ac7941792dfd7f5a0fe150a288f149ee536"
covered_sha256:
  packages/ccba-notebooklm/src/ccba_notebooklm/__init__.py: "37a7984aa97c3eca44cde4c345b2c44da4b972796ddd335a160f4146899f4ac7"
  packages/ccba-notebooklm/src/ccba_notebooklm/_artifacts.py: "389c84e850f68512333de01099d841fcab81d426752125fcb57c3090661c8e3e"
  packages/ccba-notebooklm/src/ccba_notebooklm/_gc.py: "3a311e3478bb4ee7f758e885f24e818623c74943e66c7f23d7083d4d834feb8b"
  packages/ccba-notebooklm/src/ccba_notebooklm/_registry.py: "2a26db55a36d0a564852ad4f3f64751a8555b6c922a0a5cb080b3b64abb7de75"
  packages/ccba-notebooklm/src/ccba_notebooklm/_security.py: "688f7c07fa78293d1675d5bf0de6ef27bf309b436331301fe091dc22466ab2ec"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - packages/ccba-notebooklm/src/ccba_notebooklm/__init__.py
  - packages/ccba-notebooklm/src/ccba_notebooklm/_artifacts.py
  - packages/ccba-notebooklm/src/ccba_notebooklm/_gc.py
  - packages/ccba-notebooklm/src/ccba_notebooklm/_registry.py
  - packages/ccba-notebooklm/src/ccba_notebooklm/_security.py
triggers:
  - verify-ccba-notebooklm
  - kiểm định ccba-notebooklm
  - test notebooklm statechart
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-notebooklm`

Bộ kỹ năng kiểm định tự động chuyên biệt cho package `ccba-notebooklm` (`CCBANotebookLMClient`, `NotebookLMClient`, `run_maskara_gate`, `sanitize_prompt_for_query`, `update_registry`, `check_quota_and_warn`, `run_garbage_collection`, `post_process_summary`), được khởi tạo theo **Profile B (In-Process Library)** của `ccba-create-verification-skill` `v1.4.0` và chuẩn **Pstack `statechart` `v0.15.42`**. Toàn bộ mã kiểm định cô lập trong `packages/ccba-harness/.agents/skills/verify-ccba-notebooklm/harness/`.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Bảo vệ trực tiếp `15` Public Deep Seams 2 tầng trong `ccba_notebooklm.__all__` (`HAS_NOTEBOOKLM`, `CCBANotebookLMClient`, `NotebookLMClient`, `check_auth`, `get_client` và `10` workflow functions) cùng `4` module điều phối lõi (`_security.py`, `_registry.py`, `_gc.py`, `_artifacts.py`) tương ứng với kỹ năng `ccba-notebooklm-connector`.
- **Version Anchor (`sync_commit` & `covered_sha256`)**: Neo tại commit `704f2ac7941792dfd7f5a0fe150a288f149ee536` kèm mã băm SHA-256 chuẩn hóa LF bảo vệ toàn bộ `5` tệp `covered_paths`.
- **Giới Hạn Phạm Vi (`Scope & Limitations`)**:
  - Toàn bộ thao tác tệp (`.md/scratch/redacted/`, `sources_registry.yaml`, `workspace_context.yaml`, `notebooklm_task_state.yaml`) được cô lập tuyệt đối trong `tmp_path` bằng `monkeypatch.chdir(tmp_path)` và patch đường dẫn module `_registry`, tuyệt đối không ghi ra `.md/` của repo thật.
  - Phản hồi của `detect_secrets_in_text` và client NotebookLM bất đồng bộ được mock in-memory để chạy `< 0.2s` không cần mạng hay cookie xác thực, đồng thời tuân thủ `RULE-5.11` (không nhúng secret literal hay tên biến nhạy cảm vào bộ test).

---

## Kiến Trúc 5 Khối Kiểm Định In-Process (`Profile B`)

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra 5 tệp covered_paths ccba-notebooklm)"] --> B2["2. In-Process Sandbox\n(TemporaryDirectory + Cô Lập .md/ Registry & Redacted)"]
    B2 --> B3["3. Seam Readiness Barrier\n(Nạp 15 Public Seams 2 Tầng ccba_notebooklm không sleep)"]
    B3 --> B4["4. Evidence-Capture Pytest\n(Hợp đồng 6 tính năng + 4 Statechart Bug-Path Replay)"]
    B4 --> B5["5. Guaranteed Cleanup\n(Dọn sạch TemporaryDirectory & Env trong finally)"]
```

### 1. Clean-Slate Pre-flight
- Xác nhận đủ `5` tệp trong `covered_paths` tồn tại trên đĩa và `ccba_notebooklm.__init__.py` nạp sạch không sinh ngoại lệ.

### 2. In-Process Sandbox Isolation
- Khởi tạo vùng làm việc tạm `TemporaryDirectory(prefix="verify_ccba_notebooklm_")`, thiết lập `PYTHONPATH` và biến `CCBA_NOTEBOOKLM_SANDBOX` trong process thuần **không kết nối mạng hay mở tiến trình Chrome**.

### 3. Deterministic Seam Readiness Barrier
- Kiểm tra nạp thẳng toàn bộ `15` Public Deep Seams trong `ccba_notebooklm.__all__` và kiểm chứng `NotebookLMClient is CCBANotebookLMClient` bằng lệnh con Python sạch; cấm dùng `time.sleep(N)`.

### 4. Evidence-Capture Pytest & Statechart `v0.15.42` (`Bug-Path Replay`)
- Thực thi `test_notebooklm_suite.py` đối chiếu toàn bộ `6` tính năng trong `features/INDEX.md` và mô hình hóa luồng chuyển trạng thái bằng `stateDiagram-v2` ($18 \le 20$ cạnh, vượt qua 5 Anti-Lie invariants):

```mermaid
stateDiagram-v2
  classDef breaks fill:#f8d0d0,stroke:#b00020,stroke-width:2px,color:#3b0008
  classDef mayBreak fill:#fff3cd,stroke:#8a6d00,stroke-width:2px,color:#3d3200
  classDef bugPath fill:#fde2c8,stroke:#c2410c,stroke-width:2px,color:#3b1204
  classDef repeats fill:#e6e6fa,stroke:#4c1d95,stroke-width:2px,color:#1e1033

  state "GateReady: ccba_notebooklm Ingestion & Quota" as GateReady
  state "MAY-BREAK: BypassOriginalPath - URL/Binary/Missing Trả False" as BypassOriginalPath
  state "BUG-PATH: MaskaraScan - run_maskara_gate Quét Tệp" as MaskaraScan
  state "BREAKS: UploadBlockedValueError - Phát Hiện API Key Chặn Cứng" as UploadBlockedValueError
  state "MAY-BREAK: ScannerWarnFallback - Lỗi Ngoài Trả (path, False)" as ScannerWarnFallback
  state "BUG-PATH: QuotaCheck - check_quota_and_warn Kiểm Tra 90%" as QuotaCheck
  state "MAY-BREAK: DeleteOrphanWarn - Cảnh Báo Lỗi Xóa Nguồn Mồ Côi" as DeleteOrphanWarn
  state "NotebookSyncedDone: Registry & Summary Đã Sẵn Sàng" as NotebookSyncedDone

  [*] --> GateReady
  GateReady --> BypassOriginalPath: when source is URL binary or missing
  GateReady --> MaskaraScan: when local text file enters run_maskara_gate
  MaskaraScan --> UploadBlockedValueError: when critical rule_id detected
  MaskaraScan --> ScannerWarnFallback: when non-blocking scanner error prints Warn
  MaskaraScan --> NotebookSyncedDone: when file clean or redacted temp written
  GateReady --> QuotaCheck: when check_quota_and_warn inspects notebook
  QuotaCheck --> OrphanGcLoop: when sources count reaches 90 percent of limit
  state "Dọn Nguồn Mồ Côi" as OrphanGcLoop {
    state "REPEATS: OrphanIter - Duyệt Nguồn Ngoài Registry" as OrphanIter
    [*] --> OrphanIter
    OrphanIter --> OrphanIter: when checking next unregistered source
  }
  OrphanGcLoop --> DeleteOrphanWarn: when delete_source raises exception on orphan
  OrphanGcLoop --> NotebookSyncedDone: when orphan sources cleaned within quota
  QuotaCheck --> NotebookSyncedDone: when sources count below 90 percent limit
  BypassOriginalPath --> [*]
  UploadBlockedValueError --> [*]
  ScannerWarnFallback --> [*]
  DeleteOrphanWarn --> [*]
  NotebookSyncedDone --> [*]

  class UploadBlockedValueError breaks
  class BypassOriginalPath,ScannerWarnFallback,DeleteOrphanWarn mayBreak
  class MaskaraScan,QuotaCheck bugPath
  class OrphanIter repeats
```

**Danh sách đường dẫn phản chứng (`bug_path`) & bước ẩn bàn giao kèm sơ đồ:**
- `bug_path_1` (Critical Finding Upload Blocked — `ValueError`): `[{"from": "GateReady", "to": "MaskaraScan", "when": "local text file enters run_maskara_gate"}, {"from": "MaskaraScan", "to": "UploadBlockedValueError", "when": "critical rule_id detected"}]`
- `bug_path_2` (URL/Binary/Missing File Bypass Returns `(source_path, False)`): `[{"from": "GateReady", "to": "BypassOriginalPath", "when": "source is URL binary or missing"}]`
- `bug_path_3` (Unexpected Scanner Error Fail-Open Warning in `run_maskara_gate`): `[{"from": "GateReady", "to": "MaskaraScan", "when": "local text file enters run_maskara_gate"}, {"from": "MaskaraScan", "to": "ScannerWarnFallback", "when": "non-blocking scanner error prints Warn"}]`
- `bug_path_4` (Quota $\ge 90\%$ Triggers Orphan GC Loop & Warns on `delete_source` Error): `[{"from": "GateReady", "to": "QuotaCheck", "when": "check_quota_and_warn inspects notebook"}, {"from": "QuotaCheck", "to": "OrphanGcLoop", "when": "sources count reaches 90 percent of limit"}, {"from": "OrphanGcLoop", "to": "DeleteOrphanWarn", "when": "delete_source raises exception on orphan"}]`
- `hidden_steps` (lược bỏ để giữ ngân sách $\le 20$ cạnh):
  - `sanitize_prompt_for_query` ngược lại với `run_maskara_gate` theo cơ chế **Fail-Closed** (`RuntimeError` khi `detect_secrets_in_text` ném lỗi hoặc `ValueError` qua fallback regex), đã kiểm định trực tiếp tại `test_feat_nlm_002`.
  - `_registry.route_session_to_workflow` ưu tiên biến môi trường `NOTEBOOKLM_<BUNDLE>_ID` trước `catalog.yaml` và lưu vào `workspace_context.yaml`.
- Cả 4 chuỗi `bug_path` được replay trực tiếp trên mã nguồn thật tại `test_notebooklm_suite.py`.

### 5. Guaranteed Cleanup
- Xóa toàn bộ thư mục tạm và khôi phục trạng thái môi trường trong khối `finally:`.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Chạy Bộ Kiểm Định 5 Khối Cho `ccba-notebooklm`
```bash
.venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-notebooklm/harness/run_verify_notebooklm.py
```
- **Tiêu chí hoàn thành:** Toàn bộ `6` ca kiểm thử trong `test_notebooklm_suite.py` vượt qua 100%, thư mục tạm được giải phóng và lệnh thoát với `exit code 0`.

### Bước 2: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận `git diff --quiet` trên `packages/ccba-notebooklm`.
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `packages/ccba-notebooklm/src/ccba_notebooklm/_security.py` (ví dụ đổi giá trị trả về nhánh URL tại dòng `45` thành `return source_path, True`), chạy lại `run_verify_notebooklm.py` để xác nhận bắt được lỗi (`exit code != 0`), hoàn nguyên sạch với `git checkout --`, và chạy lại xác nhận `exit code 0`.
- **Tiêu chí hoàn thành:** Bộ kiểm định bắt được đột biến ngữ nghĩa, mã nguồn hoàn nguyên 100% sạch sẽ và lần chạy nghiệm thu đạt `exit code 0`.
