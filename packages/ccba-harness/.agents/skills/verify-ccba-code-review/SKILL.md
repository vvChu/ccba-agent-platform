---
name: verify-ccba-code-review
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng rà soát mã nguồn hai trục /ccba-code-review (ADR-0009 / ADR-0035 / ADR-0044 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-code-review
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-code-review và 14 tài liệu tham chiếu Level 3.
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
  .agents/skills/ccba-code-review/SKILL.md: "7fc474beba66df5b473a07f1780445504cb52dc2d2c16698223b2af593f7d150"
  .agents/skills/ccba-code-review/references/parallel-review-workflow.md: "e8cde906bac988b39eb232d08db83ec306bb3bd9dd07f18e92046e8257d57be5"
  .agents/skills/ccba-code-review/references/unslop_checklist.md: "2a2499376921b379d61a5cfc2bc9531ca823c484a5ffb714ef311a987df66084"
  scripts/spoke/sync/coordinator.py: "5ed1d0785a30a5505b630786ef7450cee2e5127ed864aa5e80e381cdfb64988f"
verification_mode:
  - scaffold
  - sync
  - verify
covered_paths:
  - .agents/skills/ccba-code-review/SKILL.md
  - .agents/skills/ccba-code-review/references/parallel-review-workflow.md
  - .agents/skills/ccba-code-review/references/unslop_checklist.md
  - scripts/spoke/sync/coordinator.py
triggers:
  - verify-ccba-code-review
  - kiểm định ccba-code-review
  - test ccba-code-review harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-code-review`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-code-review` (Rà soát chất lượng mã nguồn song song trên 2 trục `Standards` và `Spec`, Simplify Gate `400 LOC`/`8 tệp`/`200 LOC`, Copilot Review Gate `audit_pr_comments.py`, `fresh context window` foreground subagents, bộ lọc `Execution-Proven Findings Filter`, và đánh giá `## Merge Danger`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0035, ADR-0044, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 5 bước của `.agents/skills/ccba-code-review/SKILL.md`, chuyển giao tường minh các tệp tiêu chuẩn (`docs/rules/code_quality_standards.md` — `v1.3.2 #1208`), khởi tạo subagents với `fresh context window` (`v1.3.2 #1341`), phân loại `candidate` + `repro_command` $\to$ `Verified Findings` vs `Dropped / Unverified Notes`, cùng 14 tài liệu tham chiếu Level 3 và `ccba_harness.SkillValidator`.
- **Version Anchor (`sync_commit` & `covered_sha256`)**: Neo tại commit trên `main` `6bd71548c72d04e9b7372f37961d5f43d13ddaa9` kèm bảng băm SHA-256 chuẩn hóa LF (`covered_sha256`) bảo vệ toàn bộ `covered_paths` (chống xanh giả trên shallow clone hoặc squash-merge).

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / Level 3 references)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 2 trục Code Review, Execution-Proven Filter & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-code-review/SKILL.md`, 14 tệp tham chiếu trong `.agents/skills/ccba-code-review/references/`, và `scripts/spoke/sync/coordinator.py`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_code_review_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng rà soát mã nguồn 2 trục:

```mermaid
stateDiagram-v2
    [*] --> PinFixedPoint
    PinFixedPoint --> SimplifyAndCopilotGate : diff_non_empty
    SimplifyAndCopilotGate --> CopilotBlocked : unresolved_copilot_recommendations
    SimplifyAndCopilotGate --> ParallelSubagents : simplify_and_copilot_clear
    ParallelSubagents --> ContextForkedViolation : subagent_forked_caller_context_or_spawned_child
    ParallelSubagents --> OrchestratorReproFilter : fresh_context_candidates_emitted
    OrchestratorReproFilter --> ReviewBlocked : verified_finding_or_verify_patch_nonzero
    OrchestratorReproFilter --> [*] : merge_danger_and_verify_patch_exit_0
    CopilotBlocked --> [*]
    ContextForkedViolation --> [*]
    ReviewBlocked --> [*]
```

- `bug_path`: `[{"from": "SimplifyAndCopilotGate", "to": "ParallelSubagents", "when": "simplify_and_copilot_clear"}, {"from": "ParallelSubagents", "to": "ContextForkedViolation", "when": "subagent_forked_caller_context_or_spawned_child"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_code_review_suite.py::test_feat_rev_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-code-review`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python packages/ccba-harness/.agents/skills/verify-ccba-code-review/harness/run_verify_code_review.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_code_review_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi `fresh context window` trong `.agents/skills/ccba-code-review/SKILL.md`).
- Chạy lại `run_verify_code_review.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_code_review.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
