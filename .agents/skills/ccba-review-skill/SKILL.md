---
name: ccba-review-skill
description: Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết
  skill của CCBA.
disable-model-invocation: true
bundle: _core
triggers:
- review-skill
- audit-skill
- ccba-review-skill
- kiểm định skill
---
# Kỹ năng Rà soát và Tối ưu hóa Skill (Review Skill)

Kỹ năng này thực hiện quy trình đánh giá tĩnh (static) và ngữ nghĩa (semantic) của một tệp tin `SKILL.md` để đảm bảo tính khả đoán (predictability), độ súc tích (pruning) và tuân thủ các quy tắc chất lượng của CCBA.

---

## Quy trình Thực hiện (Process)

1.  **Thu thập và phân tích tài liệu đầu vào:**
    - Sử dụng `view_file` để đọc tệp tin `SKILL.md` cần đánh giá.
    - Sử dụng `view_file` để nạp cẩm nang chất lượng kỹ năng tại [writing-great-skills](../ccba-writing-great-skills/SKILL.md). Nếu cần tra cứu định nghĩa chính xác của các failure modes, tham khảo [GLOSSARY.md](../ccba-writing-great-skills/GLOSSARY.md).
    - **Phân loại skill:** Nếu file không chứa tiêu đề `## Quy trình`, `## Process` hoặc các bước đánh số tuần tự rõ ràng, ghi nhận đây là **skill all-reference** (thuần tham chiếu). Bước 2 sẽ bỏ qua kiểm tra Completion Criterion nhưng vẫn thực hiện đầy đủ các kiểm tra linter còn lại. Bước 3 Semantic Audit vẫn áp dụng đầy đủ.
    - **Tiêu chí hoàn thành:** Nội dung của cả tệp tin đích và cẩm nang chuẩn được nạp đầy đủ vào ngữ cảnh Agent, và skill đã được phân loại (có steps / all-reference).

2.  **Đánh giá linter và cấu trúc (Linter & Structure Check):**
    - Kiểm tra độ dài mô tả `description` trong frontmatter (đối với kỹ năng model-invoked, bắt buộc dưới **180 ký tự**).
    - Kiểm tra xem mọi bước hướng dẫn trong các phần quy trình (dưới tiêu đề `Process` hoặc `Quy trình`) có chứa dòng `Tiêu chí hoàn thành:` hoặc `Completion Criterion:` hay chưa. Khi skill có nhiều nhánh (branches), kiểm tra Completion Criterion cho từng nhánh chứa steps.
    - Kiểm tra tính hợp lệ của các liên kết tương đối (relative links), phát hiện các đường dẫn tuyệt đối hoặc link hỏng.
    - Kiểm tra định danh skill trong frontmatter: thuộc tính `name:` phải tuân thủ chuẩn namespace tổ chức bắt đầu bằng tiền tố `ccba-` (hoặc `bigbim-` đối với kỹ năng BIM). Không tạo file wrapper tại `.agents/workflows/` do Antigravity hỗ trợ Slash Command Native trực tiếp từ `SKILL.md`.
    - Kiểm tra skill hoặc nhánh thích ứng từ nguồn bên ngoài phải có blockquote attribution (tên nguồn, tác giả, loại giấy phép).
    - **Tiêu chí hoàn thành:** Lập danh sách cụ thể các điểm vi phạm quy chuẩn linter tĩnh kèm vị trí dòng. Nếu skill là all-reference, ghi rõ đã bỏ qua kiểm tra Completion Criterion.

3.  **Rà soát chất lượng ngữ nghĩa (Semantic Audit Check):**
    - **Premature completion:** Rà soát xem các tiêu chí hoàn thành đã đủ rõ ràng, kiểm chứng được chưa.
    - **Duplication:** Tìm kiếm các đoạn trùng lặp ý hoặc cấu trúc viết lại.
    - **Sprawl:** Đánh giá xem tài liệu có quá phình to không; nếu có, chỉ rõ phần tham chiếu cần tách ra tệp sibling (áp dụng Progressive Disclosure).
    - **No-op:** Phát hiện các câu hướng dẫn sáo rỗng hoặc vô nghĩa mà mô hình mặc định đã biết làm.
    - **Negation:** Phát hiện các câu chỉ dẫn sử dụng cấm đoán mà thiếu hướng dẫn tích cực thay thế.
    - **Sediment:** Phát hiện nội dung cũ, lỗi thời không còn phản ánh đúng hành vi hiện tại của skill.
    - **Tiêu chí hoàn thành:** Đưa ra đánh giá chi tiết cho từng lỗi ngữ nghĩa được phát hiện kèm theo lý do cụ thể. Phải quét đủ 6 failure modes.

4.  **Đề xuất bản vá tối ưu hóa (Optimization Patch):**
    - Chỉ thực hiện bước này nếu Bước 2 hoặc Bước 3 phát hiện lỗi.
    - Sinh ra báo cáo review gồm 2 phần: (1) Bảng tổng hợp lỗi phát hiện (dạng table: STT, Loại lỗi, Vị trí, Mô tả), (2) Đề xuất sửa từng lỗi dưới dạng diff block.
    - Không tự ghi đè tệp tin thật — chờ người dùng phê duyệt từng đề xuất trước khi áp dụng.
    - **Tiêu chí hoàn thành:** Sinh ra báo cáo review với bảng lỗi và diff block hiển thị rõ ràng cho người dùng rà soát.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Hoàn thành Bước 2 (Linter) và Bước 3 (Semantic Audit) đầy đủ — quét đủ 6 failure modes.
*   [x] Nếu phát hiện lỗi: xuất báo cáo review theo format Bước 4 (bảng + diff block) và chờ phê duyệt.
*   [x] Nếu không phát hiện lỗi: kết luận PASS kèm tóm tắt các mục đã kiểm tra.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
