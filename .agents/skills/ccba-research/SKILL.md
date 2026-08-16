---
name: ccba-research
description: Nghiên cứu chuyên sâu một vấn đề kỹ thuật hoặc pháp lý đối chiếu với
  các nguồn tài liệu gốc đáng tin cậy bằng cách khởi chạy subagent chạy ngầm.
keywords:
- research
- nghiên cứu
- tìm hiểu
- tra cứu
- citations
disable-model-invocation: true
bundle: _software
---
# 📚 Kỹ năng: ccba-research (Nghiên Cứu Chạy Ngầm)

Kỹ năng này hướng dẫn Agent cách khởi chạy một **background subagent** (`research` subagent) để thực hiện các cuộc điều tra tài liệu, thu thập thông tin facts từ các API, mã nguồn hoặc Văn bản Pháp luật (VBPL) song song dưới nền. Điều này giúp Agent chính tiếp tục làm việc mà không bị block và giảm thiểu token bloating cho cuộc hội thoại chính.

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)

Kỹ năng chỉ được coi là hoàn thành khi đáp ứng các điều kiện sau:
1. Khởi chạy thành công subagent `research` chạy ngầm qua `invoke_subagent`.
2. Subagent tuân thủ **Rào chắn Ngân sách Tìm kiếm (Search Budget Cap)**: Tối đa 5 lượt tra cứu/tìm kiếm (max 5 tool calls) trong 1 phiên.
3. Subagent thu thập thông tin trực tiếp từ **các nguồn sơ cấp đáng tin cậy** (tài liệu chính thức, source code dự án, API gốc, VBPL hiện hành) và áp dụng **Kiểm chứng Nguồn tin Chéo (Cross-Reference Validation)** với tài liệu trong vòng 12 tháng gần nhất hoặc văn bản quy phạm hiện hành.
4. Kết quả nghiên cứu được xuất ra tệp Markdown theo **Mẫu Báo cáo Kỹ thuật 5 phần chuẩn hóa**, có trích dẫn nguồn (citations) rõ ràng.
5. Tệp báo cáo được lưu trữ linh hoạt tại:
   - Mặc định: `.md/knowledge/research_and_studies/research-[slug].md`
   - Trong ngữ cảnh Wayfinder/Issue: `.md/knowledge/issues/[feature_name]/research-[slug].md`

---

## 🛠️ Quy trình thực hiện (3 Bước)

### Bước 1: Xác định câu hỏi nghiên cứu & Nguồn sơ cấp
Xác định rõ câu hỏi nghiên cứu của người dùng và các nguồn tài liệu gốc cần đọc (ví dụ: file luật trong `.md/legal_docs/`, API docs của bên thứ ba, codebase hiện tại).
*Tiêu chí hoàn thành:* Agent đã ghi nhận danh sách các câu hỏi nghiên cứu cốt lõi cùng đường dẫn các tệp nguồn sơ cấp tương ứng.

### Bước 2: Khởi chạy Subagent chạy ngầm kèm Prompt Chuẩn hóa
Sử dụng công cụ `invoke_subagent` để spawn một subagent thuộc loại `research` với prompt mô tả chi tiết:
- **Role**: `Codebase Researcher` hoặc `Legal Analyst` tùy thuộc vào nội dung nghiên cứu.
- **Prompt bắt buộc bao gồm các rào chắn**:
  1. **Search Budget Cap**: Giới hạn tối đa **5 tool calls** tra cứu/tìm kiếm. Suy nghĩ kỹ trước mỗi lượt gọi tool để đi thẳng vào trọng tâm.
  2. **Cross-Reference Validation**: Đánh giá tính thời sự (recency), đối chiếu chéo nhiều nguồn độc lập, nêu rõ điểm đồng thuận vs mâu thuẫn.
  3. **Đường dẫn lưu trữ (Dynamic Path)**:
     - Tổng quát: `.md/knowledge/research_and_studies/research-[slug].md`
     - Trong ngữ cảnh Issue: `.md/knowledge/issues/[feature_name]/research-[slug].md`
  4. **Áp dụng Mẫu Báo cáo Kỹ thuật 5 phần**:

```markdown
# Báo cáo Nghiên cứu: [Tên Chủ Đề]

## 1. Tóm tắt Thực thi (Executive Summary)
[Tóm tắt 2-3 đoạn về phát hiện cốt lõi và các đề xuất hành động chính]

## 2. Kết quả Nghiên cứu Chi tiết (Key Findings)
- **Tổng quan & Xu hướng**: [Mô tả chi tiết kỹ thuật/pháp lý, phiên bản, độ chín]
- **Quy chuẩn Tốt nhất (Best Practices)**: [Các khuyến nghị kỹ thuật/quy trình tốt nhất]
- **Bẫy thường gặp (Common Pitfalls)**: [Các rủi ro, bẫy thiết kế và phương án khắc phục]
- **Bảo mật & Hiệu năng**: [Nếu áp dụng]

## 3. Khuyến nghị Triển khai (Implementation Recommendations)
- [Các bước hành động ngắn gọn, khả thi để áp dụng vào hệ thống CCBA]

## 4. Tài liệu Tham chiếu & Citations (References & Citations)
- [Bảng hoặc danh sách chứa liên kết/nguồn trích dẫn sơ cấp rõ ràng]

## 5. Câu hỏi chưa làm rõ (Unresolved Questions)
- [Nêu rõ các câu hỏi, giả định mầm hoặc điểm mù chưa thể xác nhận, nếu có]
```

*Tiêu chí hoàn thành:* Agent chính nhận được ID phiên làm việc (Conversation ID) của subagent và ghi nhận trạng thái khởi chạy thành công dưới nền.

### Bước 3: Tiếp tục công việc chính & Hấp thụ kết quả
Trong khi subagent chạy ngầm đang đọc tài liệu và viết báo cáo, Agent chính tiếp tục trao đổi hoặc thực hiện các task khác với người dùng.
Khi nhận được thông báo subagent đã hoàn thành:
- Đọc file báo cáo Markdown mà subagent vừa tạo ra.
- Trình bày tóm tắt kết quả nghiên cứu và trỏ người dùng tới liên kết file báo cáo click được.
*Tiêu chí hoàn thành:* Báo cáo Markdown từ subagent được Agent chính nạp vào ngữ cảnh, trích xuất tóm tắt và hiển thị liên kết truy cập trực tiếp cho người dùng.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
