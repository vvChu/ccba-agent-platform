# ccba-sequential-thinking — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Phương pháp tư duy suy luận tuần tự nhiều bước (Sequential Thinking)
> **Mô tả gốc:** Áp dụng phương pháp phân tích suy nghĩ tuần tự từng bước cho các vấn đề phức tạp. Hỗ trợ rẽ nhánh giả thuyết, cập nhật và chỉnh sửa nhận định cũ.

---

# Sequential Thinking (Suy nghĩ tuần tự)

Phương pháp phân rã và giải quyết vấn đề thông qua chuỗi suy nghĩ có cấu trúc, linh hoạt điều chỉnh và tự kiểm chứng.

## Khi nào cần áp dụng

- Phân rã bài toán/thuật toán phức tạp.
- Lập kế hoạch nhiều bước có khả năng tự sửa lỗi và rẽ nhánh.
- Phân tích chéo các điều khoản văn bản pháp luật xây dựng.
- Kiểm thử giả thuyết và gỡ lỗi (debugging).

## Quy trình Cốt lõi

### 1. Bắt đầu với Ước lượng ban đầu
```
Thought 1/5: [Phân tích sơ bộ ban đầu]
```
Số lượng bước suy nghĩ tổng thể sẽ được điều chỉnh linh hoạt trong quá trình thực hiện.

### 2. Cấu trúc mỗi Bước suy nghĩ
- Liên kết và kế thừa thông tin từ bước trước một cách tường minh.
- Tập trung phân tích duy nhất một khía cạnh trong mỗi bước.
- Nêu rõ các giả định, điểm nghi vấn và các bài học rút ra.
- Định hướng rõ ràng bước suy nghĩ tiếp theo cần giải quyết vấn đề gì.

### 3. Điều chỉnh Động (Dynamic Adjustment)
- **Mở rộng (Expand)**: Phát hiện thêm điểm phức tạp -> Tăng tổng số bước (VD: 5 -> 7).
- **Thu hẹp (Contract)**: Vấn đề đơn giản hơn dự kiến -> Giảm tổng số bước.
- **Sửa đổi (Revise)**: Phát hiện nhận định cũ sai lệch -> Đánh dấu cập nhật.
- **Rẽ nhánh (Branch)**: So sánh nhiều phương án khác nhau.

### 4. Sử dụng tính năng Sửa đổi (Revision)
```
Thought 5/8 [REVISION of Thought 2]: [Cập nhật hiểu biết mới]
- Nhận định cũ: [Nội dung cũ]
- Lý do thay đổi: [Thông tin mới phát hiện]
- Ảnh hưởng: [Các thay đổi trong luồng giải quyết]
```

### 5. Rẽ nhánh phương án (Branching)
```
Thought 4/7 [BRANCH A from Thought 2]: [Phương án A]
Thought 4/7 [BRANCH B from Thought 2]: [Phương án B]
```
So sánh rõ ràng ưu/nhược điểm của từng nhánh để hội tụ về quyết định cuối cùng.

### 6. Tạo & Kiểm chứng giả thuyết
```
Thought 6/9 [HYPOTHESIS]: [Đề xuất giải pháp kiểm chứng]
Thought 7/9 [VERIFICATION]: [Kết quả kiểm thử thực tế]
```

### 7. Hoàn thành
Đánh dấu bước cuối cùng: `Thought N/N [FINAL]`. Chỉ hoàn thành khi tất cả khía cạnh đã được kiểm chứng và không còn nghi vấn.

## Các tệp Hướng dẫn & Công cụ

- `references/core-patterns.md` - Các mẫu rẽ nhánh và sửa đổi suy nghĩ chi tiết.
- `references/advanced-techniques.md` - Kỹ thuật suy nghĩ xoắn ốc (spiral refinement) và hội tụ giả thuyết.
- `scripts/process-thought.js` - Script Node.js để lưu vết và validate lịch sử suy nghĩ.
- `scripts/format-thought.js` - Script Node.js để định dạng hiển thị hộp suy nghĩ trực quan.
