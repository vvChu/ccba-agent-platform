---
name: verify-ccba-grilling
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng phỏng vấn Socrates dồn dập và tạo bảng câu hỏi /ccba-grilling (ADR-0009 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-grilling
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-grilling và tài liệu tham chiếu to-questionnaire.md / workflow_looping.md.
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
sync_commit: "9948fdf18663ae2609edf06ae0cbdbd4c87f8f4a"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-grilling/SKILL.md
  - .agents/skills/ccba-grilling/references/to-questionnaire.md
  - .agents/skills/ccba-grilling/references/workflow_looping.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-grilling
  - kiểm định ccba-grilling
  - test ccba-grilling harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-grilling`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-grilling` (Phỏng vấn Socrates dồn dập qua 3 nhánh A/B/C, Cây thiết kế *Design Tree & Frontier Questions*, và tạo bảng câu hỏi bất đồng bộ `references/to-questionnaire.md`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng Bước 0 (`in-your-own-words` & `sharpen`), 3 nhánh tác nghiệp (Standard Stress-Test, Rule Compliance Stress-Test, Visual Prototype Grilling), cấu trúc Cây thiết kế (`Design Tree`, `Frontier Questions`, `Facts vs. Decisions`), và tài liệu tham chiếu Tier 2A `references/to-questionnaire.md` (*"Grill the send, not the subject"*).
- **Version Anchor (`sync_commit`)**: Neo tại commit `9948fdf18663ae2609edf06ae0cbdbd4c87f8f4a` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / references)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 3 nhánh Grilling, Questionnaire & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-grilling/SKILL.md`, `.agents/skills/ccba-grilling/references/to-questionnaire.md`, `.agents/skills/ccba-grilling/references/workflow_looping.md`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_grilling_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng phỏng vấn Socrates:

```mermaid
stateDiagram-v2
    [*] --> PreFlightSharpen
    PreFlightSharpen --> FrontierQuestion : in_your_own_words_and_outside_check
    FrontierQuestion --> FactAutoLookup : codebase_fact_detected
    FrontierQuestion --> AskedUserFactError : asked_user_discoverable_fact
    FrontierQuestion --> IssueTreeEscalation : major_tradeoff_conflict
    FrontierQuestion --> DecisionRecorded : affirmative_yes_accepts_recommended
    FactAutoLookup --> FrontierQuestion : fact_resolved_from_repo
    DecisionRecorded --> [*] : all_frontier_resolved
    AskedUserFactError --> [*]
    IssueTreeEscalation --> [*]
```

- `bug_path`: `[{"from": "PreFlightSharpen", "to": "FrontierQuestion", "when": "in_your_own_words_and_outside_check"}, {"from": "FrontierQuestion", "to": "AskedUserFactError", "when": "asked_user_discoverable_fact"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_grilling_suite.py::test_feat_grill_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-grilling`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/run_verify_grilling.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_grilling_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi quy tắc 2 vòng trao đổi trong `to-questionnaire.md` hoặc ánh xạ `"grilling": "ccba-grilling"` trong `coordinator.py`).
- Chạy lại `run_verify_grilling.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_grilling.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
