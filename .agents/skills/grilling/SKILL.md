---
name: grilling
description: Phỏng vấn dồn dập người dùng về kế hoạch thiết kế (Stress-Test) hoặc chất vấn tuân thủ quy chuẩn (Grill with Docs).
user-invocable: true
keywords: [grill, stress-test, phỏng vấn, chất vấn, đối chiếu]
---

# Grilling (Phỏng Vấn Dồn Dập & Đối Chiếu Quy Chuẩn)

Kỹ năng này bắt buộc Agent phải chạy một vòng lặp phỏng vấn Socrates dồn dập (Grilling Loop) để stress-test kế hoạch thiết kế của người dùng hoặc đối chiếu tính tuân thủ của kế hoạch đó với các quy chuẩn tài liệu được chỉ định.

## Các Chế độ chạy (Branches)

### Nhánh A: Standard Stress-Test (Phỏng vấn Thiết kế)
Sử dụng khi người dùng muốn rà quét điểm mù logic thiết kế, cấu trúc file, sự đánh đổi kỹ thuật.
*   **Quy trình:**
    1. Đọc kỹ kế hoạch/thiết kế hiện tại.
    2. Đưa ra các câu hỏi stress-test xoay quanh: sự đánh đổi (trade-offs), độ phức tạp (complexity), khả năng mở rộng (scalability), và các giả định chưa được kiểm chứng.
    3. Đặt từng câu hỏi một (one-by-one), chờ người dùng trả lời xong mới chuyển sang câu tiếp theo. **Tuyệt đối không in ra danh sách nhiều câu hỏi cùng lúc.**
    4. Đối với mỗi câu hỏi, Agent phải đưa ra phương án đề xuất của mình trước (recommended answer) làm cơ sở tham chiếu.
    5. **Nguyên tắc tra cứu:** Nếu một thông tin thực tế (fact) có thể tìm thấy bằng cách khám phá codebase, Agent phải tự tra cứu thay vì hỏi người dùng. Chỉ đưa ra các câu hỏi thảo luận về các quyết định thiết kế (decisions) và chờ phản hồi của người dùng.

### Nhánh B: Rule Compliance Stress-Test (Grill with Docs)
Sử dụng khi người dùng cung cấp các tài liệu quy chuẩn (rules, specifications, standards, e.g., `AGENTS.md`, `legal_registry.yaml`, các spec nghiệp vụ trong `.md/knowledge/`) và yêu cầu đối soát.
*   **Quy trình:**
    1. Nạp và đọc kỹ các tài liệu quy chuẩn được chỉ định.
    2. Đọc kỹ kế hoạch/thiết kế hiện tại của người dùng.
    3. Tìm kiếm các điểm sai lệch, mâu thuẫn hoặc chưa tuân thủ quy chuẩn trong tài liệu.
    4. Chạy Grilling loop: Chất vấn người dùng từng câu một (one-by-one) về các điểm chưa khớp, yêu cầu giải trình lý do và đưa ra giải pháp sửa đổi cụ thể để tuân thủ spec.
    5. **Nguyên tắc tra cứu:** Tự tra cứu các thông tin thực tế từ codebase thay vì hỏi người dùng. Hãy dành câu hỏi cho các quyết định thiết kế hoặc lý do không tuân thủ quy chuẩn.

---

## Tiêu chí hoàn thành (Completion Criteria)
*   [x] Mọi câu hỏi đặt ra đều phải được thảo luận và có phản hồi phản hồi rõ ràng từ người dùng.
*   [x] Phải xuất ra biên bản tổng hợp quyết định (Decision Log / Resolution Summary) sau khi kết thúc toàn bộ các câu hỏi.
*   [x] Tự động cập nhật lại bản Kế hoạch triển khai (`implementation_plan.md`) nếu cuộc thảo luận dẫn đến thay đổi thiết kế hoặc cách tiếp cận kỹ thuật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
