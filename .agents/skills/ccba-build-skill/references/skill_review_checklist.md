# ccba-review-skill — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Bảng kiểm định chất lượng và tuân thủ thể chế ADR-0057 cho kỹ năng
> **Mô tả gốc:** Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết skill của CCBA.

---

# Kỹ năng Rà soát và Tối ưu hóa Skill (Review Skill)

Kỹ năng này thực hiện quy trình đánh giá thể chế kiến trúc (ADR-0057 & RES-2026-ARCH-001), đánh giá tĩnh (static linter) và ngữ nghĩa (semantic audit) của một tệp tin `SKILL.md` để đảm bảo tính khả đoán (predictability), độ súc tích (pruning) và tuân thủ các quy tắc chất lượng của CCBA.

---

## Quy trình Thực hiện (Process)

1.  **Thu thập và phân tích tài liệu đầu vào:**
    - Sử dụng `view_file` để đọc tệp tin `SKILL.md` cần đánh giá.
    - Sử dụng `view_file` để nạp cẩm nang chất lượng kỹ năng tại [skill_authoring_guide.md](./skill_authoring_guide.md). Nếu cần tra cứu định nghĩa chính xác của các failure modes, tham khảo [skill_glossary.md](./skill_glossary.md).
    - **Phân loại skill:** Nếu file không chứa tiêu đề `## Quy trình`, `## Process` hoặc các bước đánh số tuần tự rõ ràng, ghi nhận đây là **skill all-reference** (thuần tham chiếu). Bước 2 sẽ bỏ qua kiểm tra Completion Criterion nhưng vẫn thực hiện đầy đủ các kiểm tra linter và thể chế còn lại. Bước 3 Semantic Audit vẫn áp dụng đầy đủ.
    - **Tiêu chí hoàn thành:** Nội dung của cả tệp tin đích và cẩm nang chuẩn được nạp đầy đủ vào ngữ cảnh Agent, và skill đã được phân loại (có steps / all-reference).

2.  **Đánh giá thể chế kiến trúc, linter và cấu trúc (Architecture Gates & Linter Check):**
    - **Cổng 0 (The Determinism Gate):** Kiểm tra xem tác vụ có thể giải quyết 100% bằng thuật toán tất định (regex, AST parsing, logic toán học thuần túy, file I/O không cần LLM) hay không. Nếu có $\rightarrow$ Phân tầng Tier 1 (Package Function trong `packages/*/src/`). **TỪ CHỐI** viết dưới dạng SKILL.md.
    - **Cổng 1 (The Orchestration Gate):** Kiểm tra xem tác vụ có điều phối nhiều tác tử song song, chuyển trạng thái StateGraph checkpoints hoặc cần con người phê duyệt (HITL) hay không. Nếu có $\rightarrow$ Phân tầng Tier 3 (Composite Orchestrator trong `.agents/workflows/`).
    - **Kiểm định Chỉ số Granularity Placement Index (GPI Gate):**
      * Kiểm tra xem frontmatter có khai báo đầy đủ khối `gpi: {s, k, a, p}` hay không.
      * Chạy lệnh CLI kiểm định trực tiếp:
        ```bash
        python -m ccba_harness.cli evaluate-gpi --file <path-to-skill.md>
        ```
      * Tính toán chỉ số GPI theo công thức RES-2026-ARCH-001 v1.2:
        $$GPI = (s \times 2.5) + (k \times 2.0) + (a \times 2.0) - (p \times 1.5)$$
      * **Tiêu chí từ chối (Rejection Criteria):**
        - Nếu $GPI < 12.0 $\rightarrow$ **TỪ CHỐI** cấp phép Standalone Kernel Skill (Tier 2B). Bắt buộc yêu cầu gộp thành tài liệu tham chiếu lũy tiến Tier 2A (`references/*.md`) thuộc Master Skill phù hợp.
        - Nếu thư mục `scripts/` của skill chứa mã nguồn > 100 LOC $\rightarrow$ **TỪ CHỐI** (vi phạm rào chắn Chống Script Bloat - RES-2026-ARCH-001). Bắt buộc chuyển mã nguồn thành Deep Seams trong các gói monorepo `packages/*/src/`.
    - **Kiểm tra Linter & Quy chuẩn:**
      * Kiểm tra độ dài mô tả `description` trong frontmatter (đối với kỹ năng model-invoked, bắt buộc dưới **180 ký tự**).
      * Kiểm tra xem mọi bước hướng dẫn trong các phần quy trình (dưới tiêu đề `Process` hoặc `Quy trình`) có chứa dòng `Tiêu chí hoàn thành:` hoặc `Completion Criterion:` hay chưa. Khi skill có nhiều nhánh (branches), kiểm tra Completion Criterion cho từng nhánh chứa steps.
      * Kiểm tra điểm tự chủ $a$ trong khối `gpi:`: Nếu skill khai báo `disable-model-invocation: true` (User Ritual thuần túy), bắt buộc $a = 1.0$ theo barem định lượng chuẩn.
      * Kiểm tra kỹ năng đa chế độ (Multi-mode Check): Nếu skill hỗ trợ nhiều chế độ chạy qua file sibling (`MODES.md`), kiểm tra xem `Tiêu chí hoàn thành:` ở các pha phân tích và bàn giao đã bao quát hành vi riêng biệt của từng mode hay chưa.
      * Kiểm tra cổng kiểm thử xác thực máy tính (Deterministic Verification Gate per ADR-0058): Kiểm tra xem pha nghiệm thu / hoàn tất có chỉ định lệnh kiểm thử xác định khách quan (`ccba-harness verify-patch` hoặc `verify-doc`) hay chưa. Cảnh báo lỗi nếu pha hoàn tất chỉ có tiêu chí định tính mơ hồ dẫn tới Premature Completion.
      * Kiểm tra tính hợp lệ của các liên kết tương đối (relative links), phát hiện các đường dẫn tuyệt đối hoặc link hỏng.
      * Kiểm tra định danh skill trong frontmatter: thuộc tính `name:` phải tuân thủ chuẩn namespace tổ chức bắt đầu bằng tiền tố `ccba-` (hoặc `bigbim-` đối với kỹ năng BIM). Không tạo file wrapper tại `.agents/workflows/` do Antigravity hỗ trợ Slash Command Native trực tiếp từ `SKILL.md`.
      * Kiểm tra skill hoặc nhánh thích ứng từ nguồn bên ngoài phải có blockquote attribution (tên nguồn, tác giả, loại giấy phép).
    - **Tiêu chí hoàn thành:** Xác nhận vượt qua Cổng 0, Cổng 1, $GPI \ge 12.0$, không chứa script > 100 LOC và lập danh sách chi tiết các vi phạm linter tĩnh kèm vị trí dòng.

3.  **Rà soát chất lượng ngữ nghĩa (Semantic Audit Check):**
    - **Premature completion:** Rà soát xem các tiêu chí hoàn thành đã đủ rõ ràng, kiểm chứng được chưa, đặc biệt kiểm tra việc phân nhánh tiêu chí đối với các cờ rẽ nhánh (flags/modes).
    - **Duplication:** Tìm kiếm các đoạn trùng lặp ý hoặc cấu trúc viết lại, đặc biệt là lỗi lặp lại nhiều lần cùng một quy tắc cấm trong các tệp sibling (`MODES.md`).
    - **Sprawl:** Đánh giá xem tài liệu có quá phình to không; nếu có, chỉ rõ phần tham chiếu cần tách ra tệp sibling (áp dụng Progressive Disclosure).
    - **No-op:** Phát hiện các câu hướng dẫn sáo rỗng hoặc vô nghĩa mà mô hình mặc định đã biết làm.
    - **Negation:** Phát hiện các câu chỉ dẫn sử dụng cấm đoán mà thiếu hướng dẫn tích cực thay thế.
    - **Sediment:** Phát hiện nội dung cũ, lỗi thời không còn phản ánh đúng hành vi hiện tại của skill (bao gồm các file sao lưu rác như `.bak`).
    - **Tiêu chí hoàn thành:** Đưa ra đánh giá chi tiết cho từng lỗi ngữ nghĩa được phát hiện kèm theo lý do cụ thể. Phải quét đủ 6 failure modes.

4.  **Đề xuất bản vá tối ưu hóa (Optimization Patch):**
    - Chỉ thực hiện bước này nếu Bước 2 hoặc Bước 3 phát hiện lỗi.
    - Sinh ra báo cáo review gồm 2 phần: (1) Bảng tổng hợp lỗi phát hiện (dạng table: STT, Loại lỗi, Vị trí, Mô tả), (2) Đề xuất sửa từng lỗi dưới dạng diff block.
    - Không tự ghi đè tệp tin thật — chờ người dùng phê duyệt từng đề xuất trước khi áp dụng.
    - **Tiêu chí hoàn thành:** Sinh ra báo cáo review với bảng lỗi và diff block hiển thị rõ ràng cho người dùng rà soát.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Hoàn thành Bước 2 (Kiểm tra Cổng 0, Cổng 1, GPI $\ge$ 12.0, Script Bloat, Linter) và Bước 3 (Semantic Audit) đầy đủ — quét đủ 6 failure modes.
*   [x] Nếu phát hiện lỗi hoặc vi phạm tiêu chí từ chối ($GPI < 12.0$ hoặc script > 100 LOC): xuất báo cáo review theo format Bước 4 (bảng + diff block / hướng dẫn di dời) và chờ phê duyệt.
*   [x] Nếu không phát hiện lỗi: kết luận PASS kèm tóm tắt các mục đã kiểm tra.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
