---
name: verify-ccba-xia
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng trích xuất và chuyển dịch tính năng /ccba-xia (ADR-0009 / ADR-0022 / ADR-0044 / ADR-0057).
user-invocable: true
command: /verify-ccba-xia
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-xia và bộ máy upstream_evaluator.py.
category: verification
bundle: _software
tier: kernel
scope: spoke
disable-model-invocation: true
gpi:
  s: 4.0
  k: 3.0
  a: 2.0
  p: 1.0
metadata:
  author: CCBA
  version: 1.0.2
sync_commit: "4676c8d46ccfcf5aa15545abfde541fc6ef09a2a"
covered_sha256:
  .agents/skills/ccba-xia/SKILL.md: "a09c0f61e9e0a287f8f6307f786b3d15653254d7860188a63e5c57001e83ed60"
  .agents/skills/ccba-xia/references/modes.md: "6784b9c698268d5ba798513034af572d276a3419295d7ce1ecb9293531a1b3bc"
  scripts/spoke/upstream_evaluator.py: "9eb4754d3894711f3cdf2cecc6733c3799632d12ba8412897df008ba6c649208"
  scripts/spoke/_upstream_helpers.py: "3599e91c703a0d93384b91e53f743132866e4ef7bff3c6517458c149ff62084f"
  docs/adr/0022-restrict-fast-flag-in-xia-challenge-gate.md: "a1fbc89c32c407e5dab2685038ad44bc9434a3b567b3ef2818fc967672abd512"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-xia/SKILL.md
  - .agents/skills/ccba-xia/references/modes.md
  - scripts/spoke/upstream_evaluator.py
  - scripts/spoke/_upstream_helpers.py
  - docs/adr/0022-restrict-fast-flag-in-xia-challenge-gate.md
triggers:
  - verify-ccba-xia
  - kiểm định ccba-xia
  - test ccba-xia harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-xia`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-xia` (Trích xuất, Phân tích, Phản biện & Chuyển dịch Tính năng qua 6 pha) và động cơ hỗ trợ `scripts/spoke/upstream_evaluator.py`, tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0022, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 6 pha của `.agents/skills/ccba-xia/SKILL.md`, bảng chế độ `.agents/skills/ccba-xia/references/modes.md`, chốt chặn `docs/adr/0022-restrict-fast-flag-in-xia-challenge-gate.md`, cùng các hàm thực thi trong `scripts/spoke/upstream_evaluator.py` (`check_repo_license`, `check_is_duplicate`, `generate_xia_command`) và `ccba_harness.SkillValidator`.
- **Version Anchor (`sync_commit` & `covered_sha256`)**: Neo tại commit trên `main` `4676c8d46ccfcf5aa15545abfde541fc6ef09a2a` kèm bảng băm SHA-256 chuẩn hóa LF (`covered_sha256`) bảo vệ toàn bộ `covered_paths` (chống xanh giả trên shallow clone hoặc squash-merge).

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / upstream_evaluator)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 6 pha Xia & Statechart Bug-Path)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-xia/SKILL.md`, `.agents/skills/ccba-xia/references/modes.md`, và `scripts/spoke/upstream_evaluator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_xia_suite.py` đối chiếu toàn bộ 9 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng 6 pha của `/ccba-xia`:

```mermaid
stateDiagram-v2
    [*] --> Recon
    Recon --> LicenseCheck : clone_depth_1
    LicenseCheck --> MapPhase : license_permissive
    LicenseCheck --> HaltedCopyleft : license_copyleft_or_unknown
    MapPhase --> AnalyzePhase : catalog_and_gate0_checked
    AnalyzePhase --> ChallengeGate : flow_mapped
    ChallengeGate --> RejectedCombo : copy_raw_plus_fast
    ChallengeGate --> PlanPhase : socratic_or_fast_3q_approved
    PlanPhase --> DeliverPhase : plan_and_scan_deps_ready
    DeliverPhase --> [*] : scratch_cleaned
    HaltedCopyleft --> [*]
    RejectedCombo --> [*]
```

- `bug_path`: `[{"from": "Recon", "to": "LicenseCheck", "when": "clone_depth_1"}, {"from": "LicenseCheck", "to": "HaltedCopyleft", "when": "license_copyleft_or_unknown"}]` và `[{"from": "AnalyzePhase", "to": "ChallengeGate", "when": "flow_mapped"}, {"from": "ChallengeGate", "to": "RejectedCombo", "when": "copy_raw_plus_fast"}]` — được replay trực tiếp trên code thật tại `test_xia_suite.py::test_feat_xia_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-xia`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-xia/harness/run_verify_xia.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 9 bài kiểm thử trong `test_xia_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths` (`.agents/skills/ccba-xia/SKILL.md`, `.agents/skills/ccba-xia/references/modes.md`, `scripts/spoke/upstream_evaluator.py`, `scripts/spoke/_upstream_helpers.py`, `docs/adr/0022-restrict-fast-flag-in-xia-challenge-gate.md`).
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi phân loại giấy phép GPL trong `scripts/spoke/_upstream_helpers.py::classify_license_text` từ `"COPYLEFT"` sang `"PERMISSIVE"`).
- Chạy lại `run_verify_xia.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$) và lưu nhật ký phản chứng (*counterexample failure log*).
- Hoàn nguyên tức thì (`git checkout -- scripts/spoke/_upstream_helpers.py`), xác nhận `git diff` sạch và chạy lại `run_verify_xia.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
