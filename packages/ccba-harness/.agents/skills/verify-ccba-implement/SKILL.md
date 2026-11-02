---
name: verify-ccba-implement
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng hiện thực hóa mã nguồn và điều phối Task Graph /ccba-implement (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-implement
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-implement, implement-spec.md, prototype_logic.md và prototyping_patterns.md.
category: verification
bundle: _core
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
sync_commit: "0575c8a164c2d4a9502d820307797da393b76329"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-implement/SKILL.md
  - .agents/skills/ccba-implement/references/implement-spec.md
  - .agents/skills/ccba-implement/references/prototype_logic.md
  - .agents/skills/ccba-implement/references/prototyping_patterns.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-implement
  - kiểm định ccba-implement
  - test ccba-implement harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-implement`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-implement` (Hiện thực hóa mã nguồn theo TDD, quản trị Context Budget 3/5 chu kỳ, điều phối Task Graph qua `references/implement-spec.md` với **First-Unit Canary & Single-Writer**, và tạo mẫu thử `prototype_logic.md`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 5 bước triển khai trong `.agents/skills/ccba-implement/SKILL.md`, ngân sách chu kỳ sửa lỗi (Chu kỳ 3 Deep Problem Brief, Chu kỳ 5 `/boost`), quy trình Task Graph `references/implement-spec.md` (`COND-01` First-Unit Canary & Orchestrator Single-Writer), và tạo mẫu thử `references/prototype_logic.md` (`Shareable HTML`, `Guided Walkthroughs`, nhánh `prototype/<slug>`).
- **Version Anchor (`sync_commit`)**: Neo tại commit `0575c8a164c2d4a9502d820307797da393b76329` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / references)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 5 bước Implement, Canary/Single-Writer & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-implement/SKILL.md`, `references/implement-spec.md`, `references/prototype_logic.md`, `references/prototyping_patterns.md`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_implement_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng điều phối Task Graph & Single-Writer:

```mermaid
stateDiagram-v2
    [*] --> SpecBreakdown
    SpecBreakdown --> FirstUnitCanary : task_graph_charted
    FirstUnitCanary --> ParallelFrontier : canary_merged_and_verify_patch_exit_0
    FirstUnitCanary --> SubagentDirectMergeError : subagent_merged_into_integration_branch
    ParallelFrontier --> OrchestratorMergeGate : worktree_subagents_completed
    OrchestratorMergeGate --> HandoverReady : verify_patch_code_preset_exit_0
    OrchestratorMergeGate --> HardLockBlocked : verify_patch_nonzero_exit
    HandoverReady --> [*]
    SubagentDirectMergeError --> [*]
    HardLockBlocked --> [*]
```

- `bug_path`: `[{"from": "SpecBreakdown", "to": "FirstUnitCanary", "when": "task_graph_charted"}, {"from": "FirstUnitCanary", "to": "SubagentDirectMergeError", "when": "subagent_merged_into_integration_branch"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_implement_suite.py::test_feat_imp_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-implement`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python .agents/skills/ccba-implement/harness/run_verify_implement.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_implement_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi quy tắc `Single-Writer` trong `implement-spec.md` hoặc ánh xạ `"implement": "ccba-implement"` trong `coordinator.py`).
- Chạy lại `run_verify_implement.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_implement.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
