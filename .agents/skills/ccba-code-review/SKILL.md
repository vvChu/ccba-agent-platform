---
name: ccba-code-review
description: Rà soát chất lượng code song song trên hai trục Standards (Coding style/Smells)
  và Spec (Spec/Requirements).
user-invocable: true
command: /ccba-code-review
when_to_use: Dùng khi người dùng muốn đánh giá chất lượng của một PR, một commit,
  hoặc các thay đổi chưa commit (--pending).
category: utilities
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- review
- quality
- verification
- reliability
argument-hint: '[#PR | COMMIT | --pending | codebase [parallel]]'
metadata:
  author: CCBA
  version: 1.4.0
disable-model-invocation: true
bundle: _software
tier: kernel
triggers:
- review
- quality
- verification
- reliability
- ccba-code-review
- rà soát code
- check code
- review commit
- review pr
---
# Quy trình Rà soát Chất lượng Code (Code Review)

Kỹ năng này thực hiện quy trình đánh giá chất lượng mã nguồn đối chiếu giữa `HEAD` hiện tại và một điểm mốc (fixed point) được chỉ định trên hai trục độc lập: **Standards** (Quy chuẩn code) và **Spec** (Đặc tả nghiệp vụ). 

Để tránh ô nhiễm ngữ cảnh (context pollution), hai trục này sẽ được thực thi song song bởi hai sub-agents độc lập trước khi tổng hợp kết quả theo **Single-Writer Protocol**.

## Quy trình Thực hiện (Process)

### 1. Xác định điểm mốc đối chiếu & Rào chắn Độ phức tạp Diff (Pin fixed point & Simplify Gate)
- Xác định điểm mốc đối chiếu do người dùng chỉ định (Commit SHA, branch name, tag, `main`, v.v.). Nếu không chỉ định, yêu cầu người dùng cung cấp hoặc hỗ trợ qua `ask_question`.
- Xác nhận mốc đối chiếu tồn tại hợp lệ và truy xuất dữ liệu diff so với `HEAD`.
- **Rào chắn Độ phức tạp Diff (Simplify Gate - RULE-2.10):** Kiểm tra ngưỡng dung lượng diff (`scripts/hooks/simplify.py`):
  * Ngưỡng: tối đa **400 LOC** tổng cộng / **8 tệp** / **200 LOC** mỗi tệp đơn lẻ.
  * Nếu vượt ngưỡng mà không có chú thích `# APPROVED: <lý_do>`, cảnh báo yêu cầu chia nhỏ diff hoặc bổ sung lý do phê duyệt ngoại lệ trước khi tiếp tục.
- **Tiêu chí hoàn thành:** Điểm mốc đối chiếu được xác minh tồn tại và dữ liệu diff so sánh trả về khác rỗng. Nếu mốc đối chiếu không hợp lệ hoặc không có thay đổi nào (diff rỗng), dừng lại và báo lỗi.

### 2. Xác định tài liệu đặc tả & Copilot Review Gating (Identify spec & Copilot gate)
- Tìm kiếm tài liệu Spec hoặc danh sách ticket tương ứng với tính năng tại thư mục `.md/knowledge/`.
- Nếu không tìm thấy tệp tin đặc tả nghiệp vụ nào, yêu cầu người dùng cung cấp đường dẫn hoặc xác nhận bỏ qua trục Spec (chỉ review Standards).
- **Rào chắn Copilot Review (Khi Review PR):** Nếu đối tượng rà soát là Pull Request, bắt buộc kiểm toán trạng thái đánh giá tự động từ GitHub Copilot:
  ```bash
  python scripts/validation/audit_pr_comments.py --pr <pr_id>
  ```
  Nếu Copilot còn ý kiến đề xuất thay đổi chưa xử lý (`Changes recommended`), đánh dấu trạng thái PR là BLOCKED cho đến khi các thread được giải quyết dứt điểm.
- **Tiêu chí hoàn thành:** Xác định chính xác tệp tin Spec (ví dụ: `spec-{slug}.md`) làm nguồn chân lý để đối chiếu (hoặc ghi nhận bỏ qua trục Spec), đồng thời xác nhận không còn unresolved Copilot review comments.

### 3. Xác định tài liệu quy chuẩn (Identify the standards sources)
- Tìm kiếm các quy định chuẩn viết code của dự án (ví dụ: `.agents/AGENTS.md` hoặc `CODING_STANDARDS.md`).
- Đồng thời, áp dụng 12 Fowler smells cơ bản (Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest) làm quy chuẩn bổ trợ.
- **Python Monorepo Overlay:** Nếu phát hiện tệp `pyproject.toml`, tự động nạp thêm checklist chuyên biệt `references/checklists/python.md` (ADR-0035 private module isolation, mypy strict, Windows UTF-8 encoding, KISS function limit).
- **Tiêu chí hoàn thành:** Xác định đầy đủ các tệp tài liệu tiêu chuẩn hiện hành của repo để nạp vào prompt cho sub-agent.

### 4. Gọi song song hai Sub-agents (Spawn sub-agents in parallel)
- Áp dụng **Rào Chắn Kép (Two-Layer Sub-Agent Guardrail)**:
  - Bắt buộc chèn chỉ dẫn cấm ủy thác vào prompt của cả hai sub-agents: `"CRITICAL CONSTRAINT: You are a dedicated review sub-agent. Do NOT invoke /ccba-code-review, do NOT spawn any child sub-agents, and do NOT propose bash execution. Perform this review directly using read-only tools and output your structured report immediately."`
- Spawn đồng thời tối đa 2 sub-agents (sử dụng subagent `research` với công cụ chỉ đọc):
  - **Standards Sub-agent Prompt:** Nhận Git Diff + danh sách tiêu chuẩn + 12 smells + Python checklist (nếu có) + chỉ dẫn cấm ủy thác. Yêu cầu chỉ ra các vi phạm quy chuẩn và smell kèm trích dẫn dòng code. Lưu bản thảo vào `.system_generated/scratch/standards_report.md`.
  - **Spec Sub-agent Prompt:** Nhận Git Diff + nội dung Spec + chỉ dẫn cấm ủy thác. Yêu cầu chỉ ra các điểm thiếu hụt tính năng so với yêu cầu hoặc scope creep dư thừa. Lưu bản thảo vào `.system_generated/scratch/spec_report.md`.
- **Tiêu chí hoàn thành:** Khởi chạy thành công 2 sub-agents chạy song song và nhận lại đầy đủ 2 báo cáo phân tích độc lập (Standards Report và Spec Report) theo Single-Writer Protocol mà không phát sinh đệ quy sub-agent.

### 5. Tổng hợp báo cáo & Phân giải Kiểm tra Khách quan (Aggregate Findings & Deterministic Gate)
- **Đánh giá Merge Danger (Reversibility & Blast Radius):** Ngay đầu báo cáo tổng hợp, Agent bắt buộc phải xuất mục `## Merge Danger` gồm 2 chỉ số cốt lõi để người duyệt ra quyết định nhanh:
  * **Door:** `Two-way` (Trivial to revert, thay đổi cô lập/nội bộ) hoặc `One-way` (Khó đảo ngược, breaking change, thay đổi schema/contract hoặc migration phức tạp).
  * **Blast Radius:** `Localized` (1 file/hàm nội bộ), `Package-wide` (trong 1 package), `Monorepo-wide` (ảnh hưởng tooling/scripts/CI), hoặc `Spoke-affecting` (thay đổi contract/interface mà Spoke phụ thuộc).
  * *Tóm tắt lý do và tác động rủi ro (1-2 câu).*
- Tổng hợp kết quả từ hai sub-agents dưới dạng báo cáo rõ ràng với hai tiêu đề `## Standards` và `## Spec`.
- Chạy cổng kiểm tra máy tính khách quan đối với codebase hiện tại:
  * **Phân giải target package:** Nếu diff chỉ giới hạn trong một gói cụ thể thuộc monorepo (`packages/<pkg_name>`), chạy scoped test:
    ```bash
    python -m ccba_harness verify-patch --preset code --target packages/<pkg_name>
    ```
  * **Fallback đa gói / Root scripts:** Nếu diff trải rộng trên nhiều package hoặc chạm vào tooling gốc (`scripts/`, governance files), fallback về kiểm tra toàn diện CI:
    ```bash
    python -m ccba_harness verify-patch --preset ci
    ```
- Tuyệt đối không tự ý gộp chung hoặc trộn lẫn phát hiện của hai trục để tránh che lấp lỗi của nhau.
- **Tiêu chí hoàn thành:** Xuất báo cáo tổng hợp chi tiết trình lập trình viên đối soát, đính kèm kết quả bảng báo cáo từ `ccba-harness verify-patch`, kèm tóm tắt 1 dòng về số lượng lỗi và lỗi nghiêm trọng nhất trên mỗi trục. Quy tắc Khóa Cứng (HUB-ADR-0058): Đánh dấu trạng thái Review là BLOCKED nếu exit-code gate $\ne 0$.

## Tích hợp hệ thống (System Integration)

- **Trước khi tạo PR:** Chạy `/ccba-code-review --pending` sau khi hoàn thành code bằng `/ccba-tdd` để rà soát lại toàn bộ diff cục bộ.
- **Trước khi Merge PR:** Chạy `/ccba-code-review #PR_NUMBER` trong quá trình thực thi `/ccba-release-feature` để kiểm soát chất lượng và rà soát lỗi trước khi merge vào nhánh `main`.

## Vị trí trong Luồng công việc (Workflow Position)

- **Thường chạy sau:** `/ccba-tdd` (Rà soát sau khi code hướng kiểm thử).
- **Thường chạy trước:** `/ccba-contribute-to-hub` (Push và tạo PR), `/ccba-release-feature` (Merge và đóng tính năng).

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/input-mode-resolution.md` | Phân giải tham số đầu vào (PR, commit hash, `--pending`, `codebase`) thành diff kiểm thử |
| `references/requesting-code-review.md` | Quy trình yêu cầu rà soát code, tích hợp Copilot Review Gating và Simplify Gate |
| `references/checklist-workflow.md` | Hướng dẫn áp dụng checklist có cấu trúc theo từng loại dự án (Python, Web, API) |
| `references/checklists/base.md` | Checklist rà soát nền tảng phổ quát (Bảo mật, Injection, Race conditions, Auth) |
| `references/checklists/python.md` | Checklist chuyên biệt cho Python Monorepo (ADR-0035, mypy strict, Windows UTF-8, KISS) |
| `references/checklists/api.md` | Checklist chuyên biệt cho REST / RPC APIs (Idempotency, Pagination, Status codes) |
| `references/checklists/web-app.md` | Checklist chuyên biệt cho ứng dụng Web / UI (XSS, State management, Accessibility) |
| `references/spec-compliance-review.md` | Rà soát đối chiếu đặc tả chức năng (Pass/Missing/Extra requirements) |
| `references/edge-case-scouting.md` | Thám thính biên và phát hiện hiệu ứng phụ tiềm ẩn trước khi review |
| `references/parallel-review-workflow.md` | Điều phối 2 subagents song song (Standards & Spec) theo Single-Writer Protocol |
| `references/codebase-scan-workflow.md` | Quy trình quét toàn diện kiến trúc codebase với 2 subagents hỗ trợ |
| `references/code-review-reception.md` | Kỷ luật tiếp nhận phản hồi review: kiểm chứng kỹ thuật trước khi chỉnh sửa |
| `references/verification-before-completion.md` | Khóa cứng kỷ luật nghiệm thu: bằng chứng chạy thực tế trước khi tuyên bố hoàn thành |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
