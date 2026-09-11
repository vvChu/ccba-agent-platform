---
name: ccba-copywriting
description: Soạn thảo văn bản hành chính, thầu và hợp đồng từ template chuẩn hóa
  và áp dụng các công thức viết thuyết phục (AIDA, PAS).
role: master_skill
sub_skills:
- form-template-cleaner
- ccba-viet-chuyen-nghiep
argument-hint: '[loại-văn-bản-theo-mẫu] [ngữ-cảnh]'
license: MIT
metadata:
  author: claudekit
  version: 1.0.0
disable-model-invocation: true
bundle: _software
user-invocable: true
command: /ccba-copywriting
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- ccba-copywriting
- viết thầu
- soạn thầu
- hồ sơ đề xuất
- văn phong thầu
- viết thuyết phục
- marketing admin
- ccba-viet-chuyen-nghiep
- viet-chuyen-nghiep
---

# Kỹ năng Soạn thảo Văn bản theo Mẫu chuẩn (Copywriting)

Kỹ năng này chịu trách nhiệm tạo văn bản mới (hồ sơ thầu, quyết định, công văn, hợp đồng, tờ trình...) theo biểu mẫu chuẩn lưu tại kỹ năng `xu-ly-van-phong` (thư mục `/.agents/skills/ccba-xu-ly-van-phong/templates/`).

## Khi nào sử dụng

- Soạn thảo hồ sơ đề xuất thầu, hồ sơ năng lực, quyết định hành chính, tờ trình, công văn, hợp đồng từ biểu mẫu chuẩn hóa.
- Tối ưu hóa và làm giàu nội dung thuyết phục cho văn bản bằng các công thức copywriting chuyên nghiệp.

## Luồng dữ liệu (Data Flow)

`[Mẫu hiện trạng thô] -> [/ccba-copywriting] -> [/.agents/skills/ccba-xu-ly-van-phong/templates/] -> [copywriting (điền thông tin)] -> [Tài liệu hoàn thiện]`

## Quy trình Sinh tài liệu (Process)

1. **Nạp biểu mẫu chuẩn**:
   - Đọc thư mục `/.agents/skills/ccba-xu-ly-van-phong/templates/` để tải tệp template tương ứng với yêu cầu soạn thảo (áp dụng cho văn bản hành chính, thầu, hợp đồng).
   - Đối với các yêu cầu thuộc lĩnh vực văn bản hành chính/thầu: Tuyệt đối không tự suy đoán cấu trúc hoặc tự tạo khung nếu chưa có tệp template tương ứng. Nếu không có tệp khớp, báo cáo lỗi và dừng lại.
   - **NGOẠI LỆ QUAN TRỌNG (Xử lý yêu cầu ngoài luồng):** Nếu yêu cầu của người dùng rõ ràng không thuộc phạm vi văn bản hành chính/thầu/hợp đồng (ví dụ: yêu cầu viết mã code lập trình như Python `def quicksort`, giải toán, hoặc trả lời câu hỏi chung), Agent **tuyệt đối không được báo lỗi thiếu biểu mẫu**. Thay vào đó, Agent phải bỏ qua quy tắc tìm kiếm template và **trực tiếp thực hiện yêu cầu đó** (ví dụ: xuất trực tiếp đoạn code được yêu cầu).
   - **Tiêu chí hoàn thành:** Xác định đúng đường dẫn tệp template phù hợp đối với văn bản hành chính. Hoặc, trả về trực tiếp kết quả (code, câu trả lời) đối với các yêu cầu ngoài luồng mà không bị chặn bởi quy tắc template.

2. **Điền thông tin và Viết nội dung**:
   - Phân tích và điền đầy đủ các placeholders `{{placeholder}}` bằng thông tin dự án mới.
   - **QUY TẮC ĐỊNH DẠNG NGHIÊM NGẶT:** Tuyệt đối không sử dụng hoặc để lại bất kỳ dấu ngoặc vuông nào (ví dụ: `[...]`) trong toàn bộ văn bản hoàn thiện cuối cùng, dù là placeholder trống hay dùng để đánh dấu tiêu đề, phân loại phương án. Không để lại dấu chấm lửng `...`. 
   - Nếu thông tin đầu vào thiếu (như số hiệu, ngày tháng, tên người ký), Agent bắt buộc phải tự giả định (mock) các thông tin thực tế phù hợp để điền đầy đủ và làm sạch văn bản.
   - Áp dụng các công thức viết thuyết phục (xem tại `/references/copy-formulas.md`) để phát triển nội dung chi tiết.
   - **Tiêu chí hoàn thành:** Tất cả các placeholders (kể cả dấu chấm lửng `...`) được thay thế bằng dữ liệu cụ thể và chính xác. Không tồn tại bất kỳ ký tự ngoặc vuông `[` hoặc `]` nào trong kết quả trả về. Giữ nguyên cấu trúc khung pháp lý/hành chính của biểu mẫu gốc.

3. **Lựa chọn Định dạng tối ưu (Format Selection)**:
   - Agent tự động phân tích tính chất thông tin và định dạng tối ưu nhất cho từng phần văn bản:
     - *Văn xuôi lập luận (Prose):* Dùng cho các phần giải trình, diễn dịch lý do hoặc lập luận thầu.
     - *Danh sách liệt kê (List):* Dùng cho các điều khoản song song có chung cấu trúc ngữ pháp.
     - *Bảng biểu (Table):* Dùng khi có cấu trúc lặp lại từ 3 lần trở lên (như danh sách nhân sự, bảng giá thiết bị).
   - **Tiêu chí hoàn thành:** Ghi nhận rõ ràng lý do lựa chọn định dạng vào một khối "Ghi chú thiết kế" tạm thời ở cuối bản thảo. Khối ghi chú này bắt buộc phải được loại bỏ trước khi xuất bản bản chính thức cuối cùng.

4. **Neo giữ Khái niệm (Concept Grounding)**:
   - Đảm bảo các khái niệm kỹ thuật hoặc định nghĩa thầu phức tạp được giới thiệu rõ ràng (neo giữ) ở các điều khoản đầu trước khi được viện dẫn hoặc tham chiếu ở các điều khoản sau để người đọc không bị mất phương hướng.
   - **Tiêu chí hoàn thành:** Rà soát bản thảo và xác nhận không có thuật ngữ/khái niệm cốt lõi nào được sử dụng mà chưa được định nghĩa hoặc làm rõ trước đó.

## Tiêu chuẩn Thực thi (Best Practices)

- **Tuân thủ khung mẫu:** Tuyệt đối giữ nguyên Quốc hiệu, tiêu ngữ, căn lề cấu trúc của template chuẩn.
- **Kế thừa văn phong:** Sử dụng đặc tả văn phong tại `/references/writing-styles.md`.
- **Đa dạng biến thể:** Đề xuất tối thiểu 2 phương án viết cho các phân đoạn thuyết phục quan trọng để người dùng lựa chọn. **Lưu ý:** Khi trình bày các phương án, chỉ sử dụng chữ in đậm thông thường, tuyệt đối không bọc tên phương án trong dấu ngoặc vuông. 
  - *Sai:* `[PHƯƠNG ÁN 1 - Viết theo công thức PAS]`
  - *Đúng:* **PHƯƠNG ÁN 1 - Viết theo công thức PAS:**

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/viet_chuyen_nghiep_rules.md` | Cẩm nang quy tắc ngữ pháp, văn phong chuyên nghiệp và kiểm tra chất lượng bài viết |

