---
description: Tổng hợp kiến thức cuối phiên làm việc - Session Knowledge Retrospective
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Session Knowledge Retrospective Workflow

Workflow này được chạy trước khi kết thúc phiên làm việc để tổng hợp, đánh giá và lưu trữ các kiến thức có giá trị nhất đã được phát hiện trong quá trình làm việc.

## Các bước thực hiện

### 1. Thu thập thông tin phiên làm việc
Phân tích cuộc trò chuyện hiện tại để xác định:
- **Vấn đề gốc**: Mục tiêu ban đầu của người dùng là gì?
- **Các thử nghiệm đã thực hiện**: Những phương pháp nào đã được thử?
- **Giải pháp thành công**: Giải pháp cuối cùng là gì và tại sao nó hoạt động?
- **Thất bại/Backtracking**: Những gì không hoạt động và bài học rút ra là gì?

### 2. Phân loại kiến thức theo danh mục
Phân loại kiến thức đã phát hiện thành các danh mục:
- **Patterns (Mẫu)**: Các kỹ thuật/cách tiếp cận tốt có thể tái sử dụng.
- **Anti-patterns (Phản mẫu)**: Các cách tiếp cận cần tránh.
- **Conventions (Quy ước)**: Quy tắc/tiêu chuẩn được thiết lập.
- **Solutions (Giải pháp)**: Cách giải quyết vấn đề cụ thể.
- **Configurations (Cấu hình)**: Thiết lập tối ưu.
- **Integrations (Tích hợp)**: Cách kết nối các thành phần.

### 3. Đánh giá và xếp hạng kiến thức
Với mỗi kiến thức, đánh giá trên thang điểm từ 1-5:
- Mức độ quan trọng (Ảnh hưởng đến toàn bộ hệ thống?)
- Khả năng tái sử dụng (Có áp dụng được cho nhiều ngữ cảnh?)
- Độ tin cậy (Đã được xác minh và test chưa?)

*Chỉ lưu lại kiến thức có tổng điểm >= 10/15.*

### 4. Tạo/Cập nhật file kiến thức
Tạo hoặc cập nhật file `.md/knowledge/session_learnings.md` (hoặc vị trí tương tự) theo định dạng chuẩn:

```markdown
## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: [YYYY-MM-DD]

---

## Patterns (Mẫu tốt)

### [Tên Pattern]
- **Ngữ cảnh**: Khi nào áp dụng
- **Vấn đề giải quyết**: Mô tả vấn đề
- **Giải pháp**: Các bước thực hiện
- **Ví dụ code** (nếu có):
  ```python
  # Code ví dụ
  ```
- **Nguồn**: Session [conversation-id], [date]

---

## Anti-patterns (Cách tránh)

### [Tên Anti-pattern]
- **Vấn đề**: Tại sao không nên làm
- **Thay thế bằng**: Pattern thay thế
- **Nguồn**: Session [conversation-id], [date]
```

### 5. Đề xuất cập nhật user_global memory
Nếu kiến thức đặc biệt quan trọng (điểm >= 12/15), đề xuất thêm vào quy tắc toàn cục `user_global` dưới dạng các dòng tóm tắt ngắn gọn (tối đa 100 ký tự).

### 6. Đề xuất tiến hóa Kỹ năng (Skill Discovery & Evolution)
Đây là bước quan trọng để làm giàu Platform. Agent chủ động rà soát toàn bộ phiên làm việc để tìm kiếm các cơ hội tạo Skill mới.
- **Tiêu chí đánh giá (đạt cả 3):**
  - *Modularity (Tính độc lập):* Logic có thể đóng gói thành script/workflow riêng.
  - *Reusability (Tính tái sử dụng):* Có thể áp dụng cho các dự án CCBA khác.
  - *Complexity (Độ phức tạp):* Việc thực hiện thủ công tốn nhiều thời gian/công sức.
- **Hành động:**
  Hỏi người dùng ngay để đề xuất đóng góp:
  > *"Tôi phát hiện logic `[tên logic]` có thể đóng gói thành skill/workflow tái sử dụng. Bạn có muốn tôi ghi đề xuất này lên Hub ngay bây giờ không? Lệnh: `/ccba-propose-to-hub`"*

### 7. Tự động Phân loại và Dọn dẹp tài liệu đầu vào (Retrospective & Cleanup)
Trước khi đóng phiên làm việc, Agent quét thư mục đầu vào tạm thời `input_documents/` ở gốc dự án để phân phối tri thức đã sử dụng:
1. **Phân tích phân loại:** Tự động đề xuất phân loại các tệp tin trong `input_documents/`:
   - Tài liệu pháp lý, quy định $\rightarrow$ `.md/legal_docs/` hoặc `.md/extracted_docs/`.
   - Báo cáo phân tích kỹ thuật, hướng dẫn $\rightarrow$ `.md/knowledge/`.
   - Biên bản, ghi chú họp $\rightarrow$ `.md/seminars/`.
   - Tệp log, test script tạm $\rightarrow$ `.md/scratch/`.
2. **In bảng đề xuất di chuyển:** Trình bày bảng đề xuất để người dùng xác nhận.
3. **Thực thi di chuyển & Làm sạch:** Sau khi người dùng xác nhận, Agent di chuyển vật lý các tệp đã chốt vào đúng vị trí và xóa sạch các file rác còn lại trong `input_documents/`.

### 8. Tạo báo cáo tóm tắt
Kết thúc phiên bằng báo cáo ngắn gọn bao gồm: ngày làm việc, mục tiêu, kết quả, danh sách tài liệu đã dọn dẹp, kiến thức mới được ghi nhận, đề xuất cập nhật workflows/skills mới, và các công việc cần làm tiếp theo cho phiên sau.
