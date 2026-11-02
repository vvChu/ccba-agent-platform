---
name: verify-ccba-wayfinder
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng lập bản đồ định hướng giải quyết bài toán mơ hồ /ccba-wayfinder (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-wayfinder
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-wayfinder, cấu trúc Wayfinding Map và bộ đồng bộ Spoke.
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
  - .agents/skills/ccba-wayfinder/SKILL.md
  - packages/ccba-harness/src/ccba_harness/evals/simulators/platform_tooling.py
  - packages/ccba-harness/src/ccba_harness/evals/archetypes_catalog.yaml
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-wayfinder
  - kiểm định ccba-wayfinder
  - test ccba-wayfinder harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-wayfinder`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-wayfinder` (Lập bản đồ định hướng *Wayfinding Map* giải quyết bài toán mơ hồ theo cơ chế *Sương mù chiến trận — Fog of War*), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng cấu trúc của `.agents/skills/ccba-wayfinder/SKILL.md` (5 mục bản đồ chuẩn, 4 phân loại Ticket `Research`/`Prototype`/`Grilling`/`Task`, quy tắc `Fog vs. Ticket Test`, `Parallel Research Dispatch`, và khóa nhận việc `Claiming`), kết hợp kiểm định `ccba_harness.SkillValidator`, `GitRatchetOptimizer`, `PlatformToolingDomainSimulator` và ánh xạ đồng bộ `scripts/spoke/sync/coordinator.py`.
- **Version Anchor (`sync_commit`)**: Neo tại commit `0575c8a164c2d4a9502d820307797da393b76329` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / covered_paths)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng Wayfinder Map, Ticket & Statechart Bug-Path)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-wayfinder/SKILL.md`, `packages/ccba-harness/src/ccba_harness/evals/simulators/platform_tooling.py`, `packages/ccba-harness/src/ccba_harness/evals/archetypes_catalog.yaml`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_wayfinder_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng vận hành của `/ccba-wayfinder`:

```mermaid
stateDiagram-v2
    [*] --> ChartMap
    ChartMap --> DirectExecutionHandoff : zero_fog_detected
    ChartMap --> FrontierReady : fog_and_unblocked_tickets_charted
    FrontierReady --> ClaimedTicket : assignee_claimed_first
    FrontierReady --> RaceConditionCollision : worked_without_assignee_claim
    ClaimedTicket --> TicketResolved : single_ticket_answered_and_closed
    TicketResolved --> MapUpdated : decisions_and_new_frontier_synced
    MapUpdated --> [*] : destination_reached
    DirectExecutionHandoff --> [*]
    RaceConditionCollision --> [*]
```

- `bug_path`: `[{"from": "FrontierReady", "to": "RaceConditionCollision", "when": "worked_without_assignee_claim"}]` và `[{"from": "ChartMap", "to": "DirectExecutionHandoff", "when": "zero_fog_detected"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_wayfinder_suite.py::test_feat_wf_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-wayfinder`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-wayfinder/harness/run_verify_wayfinder.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_wayfinder_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths` (`.agents/skills/ccba-wayfinder/SKILL.md`, `packages/ccba-harness/src/ccba_harness/evals/simulators/platform_tooling.py`, `packages/ccba-harness/src/ccba_harness/evals/archetypes_catalog.yaml`, `scripts/spoke/sync/coordinator.py`).
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi ánh xạ `"wayfinder": "ccba-wayfinder"` trong `scripts/spoke/sync/coordinator.py` hoặc điểm GPI trong `.agents/skills/ccba-wayfinder/SKILL.md`).
- Chạy lại `run_verify_wayfinder.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$) và lưu nhật ký phản chứng (*counterexample failure log*).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_wayfinder.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
