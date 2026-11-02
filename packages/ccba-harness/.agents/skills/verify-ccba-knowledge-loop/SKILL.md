---
name: verify-ccba-knowledge-loop
description: Bộ kỹ năng kiểm định tự động 5 khối cho kỹ năng điều phối vòng lặp tri thức /ccba-knowledge-loop và llm-wiki.md (ADR-0009 / ADR-0044 / ADR-0053 / ADR-0057 / ADR-0058).
user-invocable: true
command: /verify-ccba-knowledge-loop
when_to_use: Dùng khi cần chạy kiểm định tự động 5 khối hoặc bảo trì sai lệch (drift) cho kỹ năng /ccba-knowledge-loop và tài liệu tham chiếu llm-wiki.md.
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
  - .agents/skills/ccba-knowledge-loop/SKILL.md
  - .agents/skills/ccba-knowledge-loop/references/llm-wiki.md
  - packages/ccba-harness/src/ccba_harness/evals/simulators/platform_tooling.py
  - packages/ccba-harness/src/ccba_harness/evals/archetypes_catalog.yaml
triggers:
  - verify-ccba-knowledge-loop
  - kiểm định ccba-knowledge-loop
  - test ccba-knowledge-loop harness
---

# Kỹ Năng Kiểm Định Tự Động `verify-ccba-knowledge-loop`

Bộ kỹ năng kiểm định tự động chuyên biệt cho kỹ năng `/ccba-knowledge-loop` (Điều phối vòng lặp tri thức toàn trình qua 4 pha: `Recon` $\to$ `Brainstorm` $\to$ `Wayfinder` $\to$ `Exec`, tuân thủ **Single-Writer Protocol — ADR-0053** và tài liệu tham chiếu Tier 2A `references/llm-wiki.md` tại `.md/knowledge/wiki/`), tuân thủ chuẩn **Pstack Upstream Disciplines (ADR-0009, ADR-0044, ADR-0053, ADR-0057, ADR-0058)**.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `package-bound`. Kỹ năng kiểm định hợp đồng 4 pha điều phối của `.agents/skills/ccba-knowledge-loop/SKILL.md`, rào chắn Single-Writer Protocol (Orchestrator ghi chính thức, Subagent Read-Only Sandbox), và tài liệu tham chiếu `references/llm-wiki.md` (`COND-02` cô lập không gian tên `.md/knowledge/wiki/index.md`, chu trình `Ingest`/`Query`/`Lint`, quy tắc *"Write history, not the present"* gắn mốc `YYYY-MM-DD` + `ccba-agent-platform@<commit_sha>`).
- **Version Anchor (`sync_commit`)**: Neo tại commit `0575c8a164c2d4a9502d820307797da393b76329` bảo vệ danh mục `covered_paths` khai báo tại frontmatter.

---

## Kiến Trúc 5 Khối Chức Năng Cốt Lõi

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port & nạp SKILL.md / llm-wiki.md)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe polling & SkillValidator ping)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Pytest hợp đồng 4 pha Knowledge Loop, LLM Wiki & Statechart)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch Process Group)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra cổng TCP cục bộ trước khi khởi chạy readiness probe server.
- Kiểm tra sự tồn tại nguyên vẹn của `.agents/skills/ccba-knowledge-loop/SKILL.md`, `.agents/skills/ccba-knowledge-loop/references/llm-wiki.md`, `packages/ccba-harness/src/ccba_harness/evals/simulators/platform_tooling.py`, và `packages/ccba-harness/src/ccba_harness/evals/archetypes_catalog.yaml`.

### 2. Dual-Mode Server Lifecycle (Quản Trị Tiến Trình Đa Nền Tảng)
- Khởi chạy tiến trình probe trong Process Group cô lập:
  - **Windows (`sys.platform == "win32"`)**: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  - **POSIX (`Linux / macOS`)**: `preexec_fn=os.setsid`

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- CẤM dùng `time.sleep(N)` tùy tiện để chờ tiến trình khởi động.
- BẮT BUỘC dùng vòng lặp thăm dò HTTP readiness endpoint (`/healthz`) với timeout xác định (`10.0s`, chu kỳ `50ms`).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Thực thi bộ kiểm thử hợp đồng `test_knowledge_loop_suite.py` đối chiếu toàn bộ 7 tính năng trong `features/INDEX.md`.
- Đối chứng đường lỗi Statechart (`Statechart Bug-Path Replay`) cho luồng Single-Writer & LLM Wiki:

```mermaid
stateDiagram-v2
    [*] --> ReconPhase
    ReconPhase --> BrainstormPhase : video_and_research_notes_ready
    BrainstormPhase --> WayfinderPhase : hybrid_rhythm_and_action_items_ranked
    WayfinderPhase --> ParallelExecPhase : map_and_frontier_tickets_created
    ParallelExecPhase --> SubagentWriteViolation : subagent_wrote_directly_to_map_or_kb
    ParallelExecPhase --> WikiIngestSync : orchestrator_absorbed_verified_report
    WikiIngestSync --> RootIndexOverwriteError : overwrote_root_knowledge_index
    WikiIngestSync --> [*] : wiki_isolated_and_decisions_closed
    SubagentWriteViolation --> [*]
    RootIndexOverwriteError --> [*]
```

- `bug_path`: `[{"from": "WayfinderPhase", "to": "ParallelExecPhase", "when": "map_and_frontier_tickets_created"}, {"from": "ParallelExecPhase", "to": "SubagentWriteViolation", "when": "subagent_wrote_directly_to_map_or_kb"}]` và `[{"from": "ParallelExecPhase", "to": "WikiIngestSync", "when": "orchestrator_absorbed_verified_report"}, {"from": "WikiIngestSync", "to": "RootIndexOverwriteError", "when": "overwrote_root_knowledge_index"}]` — được replay trực tiếp trên hàm kiểm chứng thực tại `test_knowledge_loop_suite.py::test_feat_kl_006_statechart_bug_path_and_drift_provenance`.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Luôn giải phóng nhóm tiến trình con trong khối `finally:` (`taskkill /F /T /PID` trên Windows hoặc `os.killpg(pgid, signal.SIGTERM)` trên POSIX) và xác nhận cổng TCP đã được giải phóng hoàn toàn.

---

## Quy Trình Vận Hành & Bảo Trì

### Bước 1: Thực Thi Bộ Kiểm Định 5 Khối Cho `/ccba-knowledge-loop`
- Chạy kịch bản điều phối kiểm định tự động từ thư mục gốc của dự án:
  ```bash
  .venv/bin/python .agents/skills/ccba-knowledge-loop/harness/run_verify_knowledge_loop.py
  ```
- **Tiêu chí hoàn thành:** Kịch bản thực thi trọn vẹn cả 5 khối, toàn bộ 7 bài kiểm thử trong `test_knowledge_loop_suite.py` vượt qua 100%, tiến trình con được dọn sạch và lệnh thoát với `exit code 0`.

### Bước 2: Kiểm Tra Nguồn Gốc Thay Đổi Khi Phát Sinh Lỗi (`Pre-Remediation Provenance Check`)
- Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`.
- Phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`).
- **Tiêu chí hoàn thành:** Xác định rõ trạng thái thuộc 1 trong 4 phân loại (`in_sync`, `updated`, `bug`, `blocked`) trước khi can thiệp mã; tuyệt đối cấm sửa `harness/` nếu phát hiện lỗi hồi quy (`bug`).

### Bước 3: Phép Thử Đột Biến Ngữ Nghĩa (`Semantic Mutation Proof`)
- Xác nhận cây làm việc sạch (`git diff --quiet && git diff --cached --quiet`).
- Thực hiện 1 đột biến ngữ nghĩa tạm thời trên `covered_paths` (ví dụ: đổi đường dẫn `.md/knowledge/wiki/index.md` trong `references/llm-wiki.md`).
- Chạy lại `run_verify_knowledge_loop.py` để xác nhận bộ kiểm định bắt trúng lỗi (exit code $\ne 0$).
- Hoàn nguyên tức thì (`git checkout -- <mutated_files>`), xác nhận `git diff` sạch và chạy lại `run_verify_knowledge_loop.py` đạt `exit code 0`.
- **Tiêu chí hoàn thành:** Phép thử đột biến ngữ nghĩa bắt được lỗi, mã nguồn được hoàn nguyên 100% và lượt chạy nghiệm thu thoát sạch với `exit code 0`.
