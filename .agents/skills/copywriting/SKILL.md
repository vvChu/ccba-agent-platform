---
name: copywriting
description: Soạn thảo văn bản hành chính, thầu và hợp đồng từ template chuẩn hóa và áp dụng các công thức viết thuyết phục (AIDA, PAS).
argument-hint: "[loại-văn-bản-theo-mẫu] [ngữ-cảnh]"
license: MIT
metadata:
  author: claudekit
  version: "1.0.0"
---

# Kỹ năng Soạn thảo Văn bản theo Mẫu chuẩn (Copywriting)

Kỹ năng này chịu trách nhiệm tạo văn bản mới (hồ sơ thầu, quyết định, công văn, hợp đồng, tờ trình...) theo biểu mẫu chuẩn lưu tại `templates/` (được sinh tự động bởi quy trình [/ccba-extract-style](../../workflows/ccba-extract-style.md)).

## Khi nào sử dụng

- Soạn thảo hồ sơ đề xuất thầu, hồ sơ năng lực, quyết định hành chính, tờ trình, công văn, hợp đồng từ biểu mẫu chuẩn hóa.
- Tối ưu hóa và làm giàu nội dung thuyết phục cho văn bản bằng các công thức copywriting chuyên nghiệp.

## Luồng dữ liệu (Data Flow)

`[Mẫu hiện trạng thô] -> [/ccba-extract-style] -> [copywriting/templates/] -> [copywriting (điền thông tin)] -> [Tài liệu hoàn thiện]`

## Quy trình Sinh tài liệu (Process)

1. **Nạp biểu mẫu chuẩn**:
   - Đọc thư mục `templates/` để tải tệp template tương ứng với yêu cầu soạn thảo.
   - Tuyệt đối không tự suy đoán cấu trúc hoặc tự tạo khung nếu chưa có tệp template tương ứng.
   - **Tiêu chí hoàn thành:** Xác định đúng đường dẫn tệp template phù hợp trong thư mục `templates/`. Nếu không có tệp khớp, báo cáo lỗi và dừng lại.

2. **Điền thông tin và Viết nội dung**:
   - Phân tích và điền đầy đủ các placeholders `{{placeholder}}` bằng thông tin dự án mới.
   - Áp dụng các công thức viết thuyết phục (xem tại [copy-formulas.md](references/copy-formulas.md)) để phát triển nội dung chi tiết.
   - **Tiêu chí hoàn thành:** Tất cả các placeholders được thay thế bằng dữ liệu chính xác, giữ nguyên cấu trúc khung pháp lý/hành chính của biểu mẫu gốc.

3. **Lựa chọn Định dạng tối ưu (Format Selection)**:
   - Agent tự động phân tích tính chất thông tin và định dạng tối ưu nhất cho từng phần văn bản:
     - *Văn xuôi lập luận (Prose):* Dùng cho các phần giải trình, diễn dịch lý do hoặc lập luận thầu.
     - *Danh sách liệt kê (List):* Dùng cho các điều khoản song song có chung cấu trúc ngữ pháp.
     - *Bảng biểu (Table):* Dùng khi có cấu trúc lặp lại từ 3 lần trở lên (như danh sách nhân sự, bảng giá thiết bị).
   - **Tiêu chí hoàn thành:** Ghi nhận rõ ràng lý do lựa chọn định dạng trong log hoặc ghi chú thô của bản thảo trước khi xuất tài liệu chính thức.

4. **Neo giữ Khái niệm (Concept Grounding)**:
   - Đảm bảo các khái niệm kỹ thuật hoặc định nghĩa thầu phức tạp được giới thiệu rõ ràng (neo giữ) ở các điều khoản đầu trước khi được viện dẫn hoặc tham chiếu ở các điều khoản sau để người đọc không bị mất phương hướng.
   - **Tiêu chí hoàn thành:** Rà soát bản thảo và xác nhận không có thuật ngữ/khái niệm cốt lõi nào được sử dụng mà chưa được định nghĩa hoặc làm rõ trước đó.

## Tiêu chuẩn Thực thi (Best Practices)

- **Tuân thủ khung mẫu:** Tuyệt đối giữ nguyên Quốc hiệu, tiêu ngữ, căn lề cấu trúc của template chuẩn.
- **Kế thừa văn phong:** Sử dụng đặc tả văn phong tại [writing-styles.md](references/writing-styles.md).
- **Đa dạng biến thể:** Đề xuất tối thiểu 2 phương án viết cho các phân đoạn thuyết phục quan trọng để người dùng lựa chọn.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
