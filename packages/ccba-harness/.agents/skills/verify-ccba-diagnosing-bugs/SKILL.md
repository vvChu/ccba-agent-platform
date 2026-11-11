---
name: verify-ccba-diagnosing-bugs
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng chẩn đoán lỗi 6 pha /ccba-diagnosing-bugs (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-diagnosing-bugs
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-diagnosing-bugs và references/mock_debugging_patterns.md.
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
  version: 1.0.1
sync_commit: "6bd71548c72d04e9b7372f37961d5f43d13ddaa9"
covered_sha256:
  .agents/skills/ccba-diagnosing-bugs/SKILL.md: "c94b18ef24609169bc861ebd414261da6a4a46748f6407709eaccaeb2418a8bd"
  .agents/skills/ccba-diagnosing-bugs/references/mock_debugging_patterns.md: "0ae74b2d19482e5c5fef385a6632d160c369fe119ab29d3dbc20c659dbe98a06"
  scripts/spoke/sync/coordinator.py: "5ed1d0785a30a5505b630786ef7450cee2e5127ed864aa5e80e381cdfb64988f"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-diagnosing-bugs/SKILL.md
  - .agents/skills/ccba-diagnosing-bugs/references/mock_debugging_patterns.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-diagnosing-bugs
  - kiểm định ccba-diagnosing-bugs
  - test ccba-diagnosing-bugs harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-diagnosing-bugs`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-diagnosing-bugs` (Chẩn đoán lỗi khó & hồi quy hiệu năng qua 6 pha: Feedback Loop, Reproduce + Minimise, Hypothesise, Instrument, Fix + Regression Test với `git diff` Forced Mutation Gate, Cleanup + Post-mortem), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 6 pha của `.agents/skills/ccba-diagnosing-bugs/SKILL.md`, rào chắn che giấu bí mật `## Redact` (`<REDACTED>`), cổng kiểm chứng đột biến `git diff` tại Phase 5 (`v1.3.2 #1209`), tài liệu tham chiếu `references/mock_debugging_patterns.md`, cùng ánh xạ đồng bộ `scripts/spoke/sync/coordinator.py` và `ccba_harness.SkillValidator`.
- **Version Anchor (`sync_commit` & `covered_sha256`)**: Neo tại commit trên `main` `6bd71548c72d04e9b7372f37961d5f43d13ddaa9` kèm bảng băm SHA-256 chuẩn hóa LF (`covered_sha256`) bảo vệ toàn bộ `covered_paths` (chống xanh giả trên shallow clone hoặc squash-merge).

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / mock_debugging_patterns.md)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 6 pha Diagnosing Bugs, Redact & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-diagnosing-bugs/SKILL.md`, `.agents/skills/ccba-diagnosing-bugs/references/mock_debugging_patterns.md`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_diagnosing_bugs_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng chẩn đoán lỗi 6 pha:

```mermaid
stateDiagram-v2
    [*] --> Phase1Loop
    Phase1Loop --> PrematureHypothesisError : hypothesised_without_red_loop
    Phase1Loop --> Phase2ReproMinimise : tight_red_capable_command_verified
    Phase2ReproMinimise --> Phase3Hypothesise : minimal_load_bearing_repro
    Phase3Hypothesise --> Phase4Instrument : ranked_3_to_5_falsifiable_hypotheses
    Phase4Instrument --> Phase5RegressionFix : tagged_debug_probes_confirmed
    Phase5RegressionFix --> NoOpMutationFalseRedError : forced_mutation_git_diff_empty
    Phase5RegressionFix --> Phase6CleanupPostMortem : regression_test_and_fix_verified
    Phase6CleanupPostMortem --> [*] : debug_tags_removed_and_retro_linked
    PrematureHypothesisError --> [*]
    NoOpMutationFalseRedError --> [*]
```

- `bug_path`: `[{"from": "Phase1Loop", "to": "PrematureHypothesisError", "when": "hypothesised_without_red_loop"}]` và `[{"from": "Phase4Instrument", "to": "Phase5RegressionFix", "when": "tagged_debug_probes_confirmed"}, {"from": "Phase5RegressionFix", "to": "NoOpMutationFalseRedError", "when": "forced_mutation_git_diff_empty"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_diagnosing_bugs_suite.py::test_feat_bug_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-diagnosing-bugs`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-diagnosing-bugs/harness/run_verify_diagnosing_bugs.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_diagnosing_bugs_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi `<REDACTED>` hoặc quy tắc `git diff` trong `.agents/skills/ccba-diagnosing-bugs/SKILL.md`).
- Chạy lại `run_verify_diagnosing_bugs.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_diagnosing_bugs.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
