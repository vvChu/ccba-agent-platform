---
name: verify-ccba-tdd
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng phát triển hướng kiểm thử /ccba-tdd (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-tdd
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-tdd cùng references/tests.md và references/mocking.md.
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
  version: 1.0.0
sync_commit: "8c731731931966faaba6cc2571fedde11301c6c8"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-tdd/SKILL.md
  - .agents/skills/ccba-tdd/references/tests.md
  - .agents/skills/ccba-tdd/references/mocking.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-tdd
  - kiểm định ccba-tdd
  - test ccba-tdd harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-tdd`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-tdd` (Phát triển hướng kiểm thử Red $\to$ Green $\to$ Refactor, chỉ kiểm thử tại giao diện công khai *Seams* kèm ghi chú `what it catches` / `what it misses`, ngân sách 5 chu kỳ và khóa cứng `verify-patch --preset code`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 3 pha Red-Green-Refactor của `.agents/skills/ccba-tdd/SKILL.md`, quy tắc đánh đổi Seam (`what it catches` / `what it misses` — `v1.3.2 #1192`), ngân sách 5 vòng lặp với `scripts/safe_pytest.py`, tài liệu tham chiếu `references/tests.md` và `references/mocking.md`, cùng ánh xạ đồng bộ `scripts/spoke/sync/coordinator.py` và `ccba_harness.SkillValidator`.
- **Version Anchor (`sync_commit`)**: Neo tại commit `8c731731931966faaba6cc2571fedde11301c6c8` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / tests.md / mocking.md)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng Red-Green-Refactor, Seam Tradeoffs & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-tdd/SKILL.md`, `.agents/skills/ccba-tdd/references/tests.md`, `.agents/skills/ccba-tdd/references/mocking.md`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_tdd_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho chu kỳ Red $\to$ Green $\to$ Refactor:

```mermaid
stateDiagram-v2
    [*] --> SeamSelection
    SeamSelection --> PrivateInternalTestError : tested_private_internals_or_missing_tradeoff
    SeamSelection --> RedPhase : public_seam_with_catches_and_misses
    RedPhase --> GreenPhase : minimal_test_fails_for_expected_reason
    GreenPhase --> LoopBudgetExhausted : cycle_count_exceeded_5
    GreenPhase --> RefactorPhase : minimal_code_passes_100pct
    RefactorPhase --> HardLockBlocked : verify_patch_code_nonzero
    RefactorPhase --> [*] : verify_patch_code_exit_0
    PrivateInternalTestError --> [*]
    LoopBudgetExhausted --> [*]
    HardLockBlocked --> [*]
```

- `bug_path`: `[{"from": "SeamSelection", "to": "PrivateInternalTestError", "when": "tested_private_internals_or_missing_tradeoff"}]` và `[{"from": "RedPhase", "to": "GreenPhase", "when": "minimal_test_fails_for_expected_reason"}, {"from": "GreenPhase", "to": "LoopBudgetExhausted", "when": "cycle_count_exceeded_5"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_tdd_suite.py::test_feat_tdd_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-tdd`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/run_verify_tdd.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_tdd_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi `what it catches` trong `.agents/skills/ccba-tdd/SKILL.md`).
- Chạy lại `run_verify_tdd.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_tdd.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
