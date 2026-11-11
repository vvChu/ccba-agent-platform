---
name: verify-ccba-create-pr
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng tạo Pull Request và Dual-Gate CI & Copilot Review /ccba-create-pr (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-create-pr
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-create-pr và khuôn mẫu Pull Request chuẩn CCBA.
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
  version: 1.0.1
sync_commit: "c62cc569fe0a70a74dd8b86d339276186f0fde6f"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-create-pr/SKILL.md
  - .github/pull_request_template.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-create-pr
  - kiểm định ccba-create-pr
  - test ccba-create-pr harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-create-pr`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-create-pr` (Main Branch Guard, Shift-Left Gate `verify-patch`, khuôn mẫu Show-Me Visual & Merge Danger `## Summary`/`## Evidence`/`## Merge Danger`, Dual-Gate CI & Copilot Review `audit_pr_comments.py`, và lưu báo cáo tại `.md/knowledge/reports/walkthrough.md`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 5 bước của `.agents/skills/ccba-create-pr/SKILL.md`, khuôn mẫu `.github/pull_request_template.md`, rào chắn Zero-Polling Policy (`RULE-4.8`), quy chuẩn lưu walkthrough (`.md/knowledge/reports/walkthrough.md` — `RULE-4.10`), cùng ánh xạ `scripts/spoke/sync/coordinator.py` và `ccba_harness.SkillValidator`.
- **Version Anchor (`sync_commit`)**: Neo tại commit `c62cc569fe0a70a74dd8b86d339276186f0fde6f` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / pull_request_template.md)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 5 bước Create PR, Show-Me Visual & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-create-pr/SKILL.md`, `.github/pull_request_template.md`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_create_pr_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng tạo PR 5 bước:

```mermaid
stateDiagram-v2
    [*] --> MainBranchGuard
    MainBranchGuard --> RetroactiveBranchSplit : unpushed_commits_on_default_branch
    MainBranchGuard --> ShiftLeftGate : feature_branch_verified
    RetroactiveBranchSplit --> ShiftLeftGate : feature_branch_checked_out
    ShiftLeftGate --> ShiftLeftBlocked : verify_patch_nonzero_exit
    ShiftLeftGate --> PushAndCreatePR : verify_patch_exit_0
    PushAndCreatePR --> DualGateWait : show_me_visual_pr_created
    DualGateWait --> PollingViolationError : manage_task_polling_loop_detected
    DualGateWait --> [*] : ci_green_and_copilot_clean_release_ready
    ShiftLeftBlocked --> [*]
    PollingViolationError --> [*]
```

- `bug_path`: `[{"from": "MainBranchGuard", "to": "ShiftLeftGate", "when": "feature_branch_verified"}, {"from": "ShiftLeftGate", "to": "ShiftLeftBlocked", "when": "verify_patch_nonzero_exit"}]` và `[{"from": "PushAndCreatePR", "to": "DualGateWait", "when": "show_me_visual_pr_created"}, {"from": "DualGateWait", "to": "PollingViolationError", "when": "manage_task_polling_loop_detected"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_create_pr_suite.py::test_feat_pr_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-create-pr`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/run_verify_create_pr.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_create_pr_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi `## Merge Danger` trong `.agents/skills/ccba-create-pr/SKILL.md`).
- Chạy lại `run_verify_create_pr.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_create_pr.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
