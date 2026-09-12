---
name: ccba-skill-repair
description: Phục hồi và sửa chữa kỹ năng AI theo thể chế ADR-0057 và bộ kiểm định ccba-harness.
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
disable-model-invocation: true
user-invocable: true
command: /ccba-skill-repair
bundle: _core
tier: kernel
gpi: {s: 3.0, k: 2.0, a: 1.0, p: 1.0}
triggers:
- skill-repair
- ccba-skill-repair
- sửa chữa skill
- phục hồi skill
- repair-skill
---
# Kỹ năng Phục Hồi và Sửa Chữa Kỹ Năng (CCBA Skill Repair)

Kỹ năng này tự động hóa quy trình khảo sát, chẩn đoán và sửa chữa các lỗi linter, cấu trúc, liên kết và vi phạm thể chế kiến trúc 3 tầng (ADR-0057 & RES-2026-ARCH-001 v1.2) cho các tệp `SKILL.md` trong hệ thống CCBA Agent Services Platform.

---

## Quy trình Thực hiện (Process)

### 1. Khảo sát hư hỏng & Linter Failure (Triage & Failure Diagnosis)

Quét và phân tích lỗi tĩnh của tệp tin `SKILL.md` cần sửa chữa:
- Chạy lệnh chẩn đoán linter tĩnh có cưỡng chế chỉ số GPI:
  ```bash
  python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi
  ```
- Chạy lệnh đánh giá chỉ số Granularity & Placement Index (GPI):
  ```bash
  python -m ccba_harness.cli evaluate-gpi --file <path-to-skill>
  ```
- Phân loại danh sách lỗi phát hiện:
  * Lỗi cú pháp YAML (`YAML_PARSE_ERROR`): Thiếu ngoặc, lỗi thụt lề tab/space, hoặc metadata không đóng khiến parser thất bại trước khi đọc thuộc tính.
  * Thiếu hoặc sai định dạng khối `gpi: {s, k, a, p}` trong YAML frontmatter.
  * Thiếu tiêu chí hoàn thành (`**Tiêu chí hoàn thành:**` hoặc `**Completion Criterion:**`) ở các bước quy trình.
  * Liên kết hỏng hoặc sử dụng đường dẫn tuyệt đối thay vì tương đối.
  * Độ dài `description` vượt quá 180 ký tự đối với kỹ năng model-invoked.
  * Tên kỹ năng không tuân thủ namespace tiền tố `ccba-` hoặc `bigbim-`.
  * Vi phạm rào chắn Chống Script Bloat: thư mục `scripts/` chứa tệp > 100 LOC.
- **Tiêu chí hoàn thành:** Xác định chính xác danh sách các lỗi linter, cấu trúc hoặc thể chế cần khắc phục của skill đích.

### 2. Phân tích cấu trúc & Vá khối `gpi:` (Structural Analysis & GPI Patching)

Đánh giá thể chế 3 tầng theo Khung Quyết Định Hai Giai Đoạn (ADR-0057 & RES-2026-ARCH-001 v1.2):
- **Khôi phục cú pháp YAML hợp lệ:** Nếu tệp tin gặp lỗi `YAML_PARSE_ERROR`, chuẩn hóa cú pháp frontmatter: thụt lề chuẩn 2 spaces, đóng kín cặp ngoặc kép/ngoặc vuông, ngăn cách khối metadata bằng cặp thẻ `---` hợp lệ trước khi phân tích nội dung.
- **Cổng 0 (The Determinism Gate):** Nếu tác vụ có thể giải quyết 100% bằng thuật toán tất định thuần túy (regex, AST parse, logic toán học, file I/O không cần LLM) $\rightarrow$ Cảnh báo vi phạm thể chế và hướng dẫn chuyển thành Deep Seam trong `packages/*/src/` (Tier 1: Package Function). Tuyệt đối không cấp phép tạo Standalone Skill.
- **Cổng 1 (The Orchestration Gate):** Nếu tác vụ điều phối đa tác tử song song, chuyển trạng thái StateGraph checkpoints hoặc cần con người phê duyệt (HITL) $\rightarrow$ Hướng dẫn chuyển sang Composite Orchestrator trong `.agents/workflows/` (Tier 3).
- **Đo lường Chỉ số Granularity & Placement Index (GPI):**
  Định lượng 4 chiều metric cốt lõi:
  * $s$ (Reasoning Steps): 1.0 - 5.0 (số bước suy luận nhận thức).
  * $k$ (Interface / Schema Complexity): 1.0 - 5.0 (độ phức tạp tham số/schema).
  * $a$ (Autonomous Model Invocation): 1.0 - 5.0 (mức độ cần LLM tự chủ kích hoạt).
  * $p$ (Parent Domain Coupling): 1.0 - 5.0 (mức độ gắn kết với Master Skill sở hữu).
  Tính toán theo công thức:
  $$GPI = (s \times 2.5) + (k \times 2.0) + (a \times 2.0) - (p \times 1.5)$$
- **Định tuyến thể chế:**
  * Nếu $GPI \ge 12.0$: Hợp thức hóa **Tier 2B (Standalone Kernel Skill)**, chèn hoặc vá khối `gpi: {s: ..., k: ..., a: ..., p: ...}` vào frontmatter của `SKILL.md`.
  * Nếu $GPI < 12.0$: Cảnh báo không đủ điều kiện Standalone Kernel Skill, đề xuất đóng gói thành **Tier 2A (Progressive Reference)** trong `references/*.md` thuộc Master Skill phù hợp.
- Chuẩn hóa frontmatter: Bảo đảm có `name: ccba-...` hoặc `bigbim-...`, `user-invocable: true` đi kèm `command: /ccba-...`, `bundle:` hợp lệ và mô tả súc tích.
- **Tiêu chí hoàn thành:** Khối `gpi:` và YAML frontmatter của skill được cập nhật đầy đủ, chuẩn xác theo thể chế ADR-0057.

### 3. Khôi phục liên kết, Tiêu chí hoàn thành & Xử lý Scripts (Remediation & De-bloat)

Sửa chữa nội dung chi tiết trong thân văn bản `SKILL.md`:
- Bổ sung dòng `Tiêu chí hoàn thành:` (hoặc `Completion Criterion:`) cho mọi bước quy trình còn thiếu.
- Chuẩn hóa các liên kết Markdown: chuyển toàn bộ liên kết tuyệt đối thành đường dẫn tương đối hợp lệ, loại bỏ liên kết gãy.
- Xử lý rào chắn Chống Script Bloat: Nếu thư mục `scripts/` của skill chứa mã nguồn > 100 LOC, trích xuất logic nghiệp vụ thành Deep Seam trong `packages/*/src/` và chuyển script thành wrapper ngắn gọn (< 100 LOC).
- **Tiêu chí hoàn thành:** Toàn bộ liên kết tương đối hợp lệ, mọi bước quy trình có Tiêu chí hoàn thành rõ ràng và thư mục `scripts/` không chứa tệp > 100 LOC.

### 4. Kiểm định bắt buộc & Xác nhận tuân thủ (Mandatory Verification & Compliance)

Thực hiện chu trình kiểm định khép kín bảo đảm chất lượng:
- Chạy lệnh kiểm định kép bắt buộc:
  ```bash
  python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi
  ```
  và
  ```bash
  python -m ccba_harness.cli evaluate-gpi --file <path-to-skill>
  ```
- Nếu sửa đổi namespace, bundle hoặc tạo mới: chạy biên dịch catalog:
  ```bash
  python scripts/governance/compile_catalog.py
  ```
- Báo cáo kết quả phục hồi cho người dùng kèm bảng tóm tắt các điểm đã khắc phục và xác nhận trạng thái CI pass.
- **Tiêu chí hoàn thành:** Cả hai công cụ kiểm định trả về mã thoát thành công (code 0, 100% PASS).

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Bước 1: Khảo sát và chẩn đoán toàn diện lỗi linter / GPI.
*   [x] Bước 2: Vá thành công khối `gpi:` và chuẩn hóa YAML frontmatter đạt chuẩn ADR-0057 ($GPI \ge 12.0$).
*   [x] Bước 3: Khôi phục liên kết tương đối, completion criteria và xử lý rào chắn Script Bloat.
*   [x] Bước 4: Lệnh `python scripts/validate_skills.py --file <path> --enforce-gpi` và `python -m ccba_harness.cli evaluate-gpi --file <path>` đều chạy thành công 100% không còn lỗi.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
