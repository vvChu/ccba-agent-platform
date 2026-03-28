---
description: Tổng hợp kiến thức cuối phiên làm việc - Session Knowledge Retrospective
---

# Session Knowledge Retrospective Workflow

Workflow này được chạy trước khi kết thúc phiên làm việc để tổng hợp, đánh giá và lưu trữ các kiến thức có giá trị nhất đã được phát hiện trong quá trình làm việc.

## Các bước thực hiện

### 1. Thu thập thông tin phiên làm việc

Phân tích conversation hiện tại để xác định:

- **Vấn đề gốc**: Mục tiêu ban đầu của người dùng là gì?
- **Các thử nghiệm đã thực hiện**: Những phương pháp nào đã được thử?
- **Giải pháp thành công**: Giải pháp cuối cùng là gì và tại sao nó hoạt động?
- **Thất bại/Backtracking**: Những gì không hoạt động và bài học rút ra là gì?

### 2. Phân loại kiến thức theo danh mục

Phân loại kiến thức đã phát hiện thành các danh mục:

| Danh mục | Mô tả | Ví dụ |
| ---------- | ------- | ------- |
| **Patterns (Mẫu)** | Các kỹ thuật/approach có thể tái sử dụng | "Sử dụng LlamaParse cho PDF scan thay vì Gemini OCR" |
| **Anti-patterns (Phản mẫu)** | Các cách tiếp cận cần tránh | "Không dùng regex phức tạp cho markdown parsing" |
| **Conventions (Quy ước)** | Quy tắc/tiêu chuẩn được thiết lập | "Tên file lowercase với underscore" |
| **Solutions (Giải pháp)** | Cách giải quyết vấn đề cụ thể | "Fix lỗi Milvus max_length bằng truncation" |
| **Configurations (Cấu hình)** | Thiết lập tối ưu | "ENABLE_RERANKER=False cho tốc độ" |
| **Integrations (Tích hợp)** | Cách kết nối các thành phần | "DeepSeek fallback to Groq khi lỗi 402" |

### 3. Đánh giá và xếp hạng kiến thức

Với mỗi kiến thức, đánh giá:

- **Mức độ quan trọng** (1-5): Ảnh hưởng đến toàn bộ hệ thống?
- **Khả năng tái sử dụng** (1-5): Có áp dụng được cho nhiều ngữ cảnh?
- **Độ tin cậy** (1-5): Đã được xác minh và test chưa?

Chỉ lưu lại kiến thức có tổng điểm >= 10/15.

### 4. Tạo/Cập nhật file kiến thức

Tạo hoặc cập nhật file `knowledge/session_learnings.md` với format sau:

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
```code
...
```text

- **Nguồn**: Session [conversation-id], [date]

---

## Anti-patterns (Cách tránh)

### [Tên Anti-pattern]

- **Vấn đề**: Tại sao không nên làm
- **Thay thế bằng**: Pattern thay thế
- **Nguồn**: Session [conversation-id], [date]

---

## Solutions (Giải pháp tham chiếu)

### [Tên Solution]

- **Vấn đề**: Mô tả lỗi/issue
- **Giải pháp**: Các bước fix
- **Liên kết**: File/function liên quan
- **Nguồn**: Session [conversation-id], [date]

---

## Configurations (Cấu hình tối ưu)

| Setting | Value | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| ENABLE_RERANKER | False | Tốc độ | CPU-only |

```text

### 5. Đề xuất cập nhật user_global memory

Nếu kiến thức quan trọng (điểm >= 12/15), đề xuất thêm vào `user_global` memory với format:
```text

- [Mô tả ngắn gọn kiến thức - tối đa 100 ký tự]

```text

### 6. Đề xuất cập nhật workflows (nếu cần)

Nếu phát hiện quy trình làm việc mới có giá trị:

- Tạo workflow mới trong `.agent/workflows/`
- Cập nhật workflow hiện có nếu có cải tiến

### 7. Tạo báo cáo tóm tắt

Kết thúc bằng báo cáo ngắn gọn:

```markdown
## 📋 Session Retrospective Summary

### Phiên làm việc

- **Ngày**: [date]
- **Mục tiêu**: [objective]
- **Kết quả**: ✅ Thành công / ⚠️ Một phần / ❌ Chưa hoàn thành

### Kiến thức mới

- [x] N patterns mới
- [x] N anti-patterns mới  
- [x] N solutions mới

### Đề xuất cập nhật

- [ ] Cập nhật user_global: [Có/Không] - [Nội dung]
- [ ] Tạo workflow mới: [Có/Không] - [Tên workflow]
- [ ] Cập nhật workflow: [Có/Không] - [Tên workflow]

### Ghi chú cho phiên tiếp theo

[Các việc cần làm tiếp]
```text

---

## Cách kích hoạt workflow

Người dùng có thể gọi workflow này bằng cách:

```text
/session-retrospective
```text

hoặc nói:

```text
"Hãy chạy session retrospective trước khi kết thúc"
"Tổng hợp lại kiến thức phiên làm việc"
"Lưu lại những gì đã học được hôm nay"
```text

---

## Lợi ích

1. **Compounding Knowledge**: Kiến thức tích lũy theo thời gian, AI trở nên "thông minh" hơn với codebase cụ thể

2. **Tránh lặp lỗi**: Anti-patterns được ghi nhận giúp tránh các sai lầm tương tự

3. **Onboarding nhanh**: Context recovery dễ dàng cho session mới

4. **Continuous Improvement**: Workflows được cải tiến liên tục

5. **Tribal Knowledge Capture**: Bắt giữ kiến thức ngầm không có trong docs chính thức
