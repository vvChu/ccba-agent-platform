---
name: grilling
description: Phỏng vấn dồn dập người dùng về kế hoạch thiết kế (Stress-Test), chất vấn tuân thủ quy chuẩn (Grill with Docs), hoặc hội tụ thiết kế UI qua prototype trực quan (Visual Prototype Grilling).
user-invocable: true
keywords: [grill, stress-test, phỏng vấn, chất vấn, đối chiếu, prototype, UI, frontend, visual]
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
    5. **Nguyên tắc tra cứu:** Nếu một dữ kiện thực tế (*fact*) có thể tìm thấy bằng cách khám phá codebase, Agent phải tự tra cứu thay vì hỏi người dùng. Tuy nhiên, các quyết định thiết kế (*decisions*) là của người dùng — hãy đặt từng câu hỏi quyết định cho người dùng và chờ phản hồi.

### Nhánh B: Rule Compliance Stress-Test (Grill with Docs)
Sử dụng khi người dùng cung cấp các tài liệu quy chuẩn (rules, specifications, standards, e.g., `AGENTS.md`, `legal_registry.yaml`, các spec nghiệp vụ trong `.md/knowledge/`) và yêu cầu đối soát.
*   **Quy trình:**
    1. Nạp và đọc kỹ các tài liệu quy chuẩn được chỉ định.
    2. Đọc kỹ kế hoạch/thiết kế hiện tại của người dùng.
    3. Tìm kiếm các điểm sai lệch, mâu thuẫn hoặc chưa tuân thủ quy chuẩn trong tài liệu.
    4. Chạy Grilling loop: Chất vấn người dùng từng câu một (one-by-one) về các điểm chưa khớp, yêu cầu giải trình lý do và đưa ra giải pháp sửa đổi cụ thể để tuân thủ spec.
    5. **Nguyên tắc tra cứu:** Tự tra cứu các dữ kiện thực tế (*facts*) từ codebase thay vì hỏi người dùng. Hãy dành câu hỏi cho các quyết định thiết kế (*decisions*) hoặc lý do không tuân thủ quy chuẩn và chờ phản hồi.

### Nhánh C: Visual Prototype Grilling (Hội tụ Thiết kế UI qua Prototype)
Sử dụng khi người dùng muốn hội tụ về một thiết kế giao diện (frontend/UI) cụ thể thông qua các vòng lặp prototype trực quan, thay vì chỉ thảo luận bằng văn bản. Nhánh này kết hợp kỹ năng `ccba-prototype` (nhánh UI) với Grilling loop.

> Nguồn gốc: Thích ứng từ `grilling-frontend-prototyping` của Matt Pocock (MIT License).

*   **Quy trình:**
    1. Xác định câu hỏi thiết kế UI cần giải quyết (layout, component, interaction pattern).
    2. **Grilling bằng Prototype:** Mỗi vòng, Agent tạo **3-5 prototype UI khác nhau triệt để** (tùy mức độ zoom: 5 cho tổng thể, 3 cho component cụ thể) trong **1 file HTML duy nhất** (standalone artifact), cập nhật tại chỗ mỗi vòng.
    3. File HTML phải chứa một **floating picker** (draggable, góc dưới phải) với tên từng thiết kế và phím ←/→ để chuyển đổi giữa các variant live. Khi thiết kế có nhiều trạng thái có ý nghĩa (ví dụ: inbox đầy vs trống), thêm nút toggle trạng thái vào picker.
    4. **Visual Design Tree:** Grilling đi theo cây thiết kế trực quan, mỗi vòng phán quyết zoom sâu hơn một tầng: **overall design → component groups → individual components**. Agent được phép dừng sớm nếu người dùng đã hài lòng, hoặc zoom thêm tầng nếu component phức tạp — quyết định dừng hay tiếp thuộc về người dùng.
    5. **Fallback:** Nếu người dùng chỉ cần mockup nhanh mà không cần tương tác, có thể sử dụng `generate_image` thay cho standalone HTML.
    6. **Nguyên tắc Grilling:** Áp dụng đầy đủ quy tắc Nhánh A — hỏi từng câu một, đưa ra recommended answer, tự tra cứu facts từ codebase.
*   **Đầu ra & Dọn dẹp:**
    - Chỉ giữ file HTML vòng cuối chứa variant chiến thắng.
    - Bắt buộc ghi **Decision Log** (biên bản quyết định thiết kế) tóm tắt mỗi vòng đã chọn variant nào và lý do, lưu vào `.md/knowledge/issues/[feature_name]/prototypes/NOTES.md`.
    - Sau khi người dùng xác nhận thiết kế cuối, xóa file HTML prototype và chỉ giữ `NOTES.md` — tuân thủ quy trình dọn dẹp của `ccba-prototype`.

---

## Tiêu chí hoàn thành (Completion Criteria)
*   [x] Mọi câu hỏi đặt ra đều phải được thảo luận và có phản hồi phản hồi rõ ràng từ người dùng.
*   [x] Phải xuất ra biên bản tổng hợp quyết định (Decision Log / Resolution Summary) sau khi kết thúc toàn bộ các câu hỏi.
*   [x] Tự động cập nhật lại bản Kế hoạch triển khai (`implementation_plan.md`) nếu cuộc thảo luận dẫn đến thay đổi thiết kế hoặc cách tiếp cận kỹ thuật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
