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
  version: 2.0.0
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

Để tránh ô nhiễm ngữ cảnh (context pollution), hai trục này sẽ được thực thi song song bởi hai sub-agents độc lập trước khi tổng hợp kết quả.

## Quy trình Thực hiện (Process)

### 1. Xác định điểm mốc đối chiếu (Pin the fixed point)
- Xác định điểm mốc đối chiếu do người dùng chỉ định (Commit SHA, branch name, tag, `main`, v.v.). Nếu không chỉ định, yêu cầu người dùng cung cấp.
- Xác nhận mốc đối chiếu tồn tại hợp lệ và truy xuất dữ liệu diff so với `HEAD`.
- **Tiêu chí hoàn thành:** Điểm mốc đối chiếu được xác minh tồn tại và dữ liệu diff so sánh trả về khác rỗng. Nếu mốc đối chiếu không hợp lệ hoặc không có thay đổi nào (diff rỗng), dừng lại và báo lỗi.

### 2. Xác định tài liệu đặc tả nghiệp vụ (Identify the spec source)
- Tìm kiếm tài liệu Spec hoặc danh sách ticket tương ứng với tính năng tại thư mục `.md/knowledge/`.
- Nếu không tìm thấy tệp tin đặc tả nghiệp vụ nào, yêu cầu người dùng cung cấp đường dẫn hoặc xác nhận bỏ qua trục Spec (chỉ review Standards).
- **Tiêu chí hoàn thành:** Xác định chính xác tệp tin Spec (ví dụ: `spec-{slug}.md`) làm nguồn chân lý để đối chiếu hoặc ghi nhận bỏ qua trục Spec.

### 3. Xác định tài liệu quy chuẩn (Identify the standards sources)
- Tìm kiếm các quy định chuẩn viết code của dự án (ví dụ: `.agents/AGENTS.md` hoặc `CODING_STANDARDS.md`).
- Đồng thời, áp dụng 12 Fowler smells cơ bản (Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest) làm quy chuẩn bổ trợ.
- **Tiêu chí hoàn thành:** Xác định đầy đủ các tệp tài liệu tiêu chuẩn hiện hành của repo để nạp vào prompt cho sub-agent.

### 4. Gọi song song hai Sub-agents (Spawn sub-agents in parallel)
- Áp dụng **Rào Chắn Kép (Two-Layer Sub-Agent Guardrail)**:
  - Bắt buộc chèn chỉ dẫn cấm ủy thác vào prompt của cả hai sub-agents: `"CRITICAL CONSTRAINT: You are a dedicated review sub-agent. Do NOT invoke /code-review, do NOT spawn any child sub-agents, and do NOT propose bash execution. Perform this review directly using read-only tools and output your structured report immediately."`
- Spawn đồng thời 2 sub-agents (sử dụng subagent `self` hoặc `research` với công cụ chỉ đọc):
  - **Standards Sub-agent Prompt:** Nhận Git Diff + danh sách tiêu chuẩn + 12 smells + chỉ dẫn cấm ủy thác. Yêu cầu chỉ ra các vi phạm quy chuẩn và smell kèm trích dẫn dòng code.
  - **Spec Sub-agent Prompt:** Nhận Git Diff + nội dung Spec + chỉ dẫn cấm ủy thác. Yêu cầu chỉ ra các điểm thiếu hụt tính năng so với yêu cầu hoặc scope creep dư thừa.
- **Tiêu chí hoàn thành:** Khởi chạy thành công 2 sub-agents chạy song song và nhận lại đầy đủ 2 báo cáo phân tích độc lập (Standards Report và Spec Report) mà không phát sinh đệ quy sub-agent.

### 5. Tổng hợp báo cáo (Aggregate Findings & Deterministic Gate)
- Tổng hợp kết quả từ hai sub-agents dưới dạng báo cáo rõ ràng với hai tiêu đề `## Standards` và `## Spec`.
- Chạy cổng kiểm tra máy tính khách quan đối với codebase hiện tại:
  ```bash
  python -m ccba_harness verify-patch --preset code --target <target_path>
  ```
- Tuyệt đối không tự ý gộp chung hoặc trộn lẫn phát hiện của hai trục để tránh che lấp lỗi của nhau.
- **Tiêu chí hoàn thành:** Xuất báo cáo tổng hợp chi tiết trình lập trình viên đối soát, đính kèm kết quả bảng báo cáo từ `ccba-harness verify-patch`, kèm tóm tắt 1 dòng về số lượng lỗi và lỗi nghiêm trọng nhất trên mỗi trục. Quy tắc Khóa Cứng (HUB-ADR-0058): Đánh dấu trạng thái Review là BLOCKED nếu exit-code gate $\ne 0$.

## Tích hợp hệ thống (System Integration)

- **Trước khi tạo PR:** Chạy `code-review --pending` sau khi hoàn thành code bằng `/ccba-tdd` để rà soát lại toàn bộ diff cục bộ.
- **Trước khi Merge PR:** Chạy `code-review #PR_NUMBER` trong quá trình thực thi `/ccba-release-feature` để kiểm soát chất lượng và rà soát lỗi trước khi merge vào nhánh `main`.

## Vị trí trong Luồng công việc (Workflow Position)

- **Thường chạy sau:** `/ccba-tdd` (Rà soát sau khi code hướng kiểm thử).
- **Thường chạy trước:** `/ccba-contribute-to-hub` (Push và tạo PR), `/ccba-release-feature` (Merge và đóng tính năng).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
