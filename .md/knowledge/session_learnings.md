## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-04-23

---

## Patterns (Mẫu tốt)

### Semantic Map-Reduce Audit cho Hồ sơ Kỹ thuật lớn

- **Ngữ cảnh**: Khi cần Audit một bộ hồ sơ thiết kế (Thuyết minh, Bản vẽ MEP/Kiến trúc) có số lượng token vượt quá ngưỡng context window của LLM cục bộ (e.g., >32k tokens), dẫn đến timeout hoặc giảm chất lượng reasoning.
- **Vấn đề giải quyết**: Khắc phục giới hạn Timeout của API Gateway proxy và hiện tượng mất focus (hallucination) của LLM khi đọc tài liệu kỹ thuật dài.
- **Giải pháp**: 
  1. Trích xuất văn bản/vector từ PDF thay vì Pure Vision (tiết kiệm token).
  2. Băm nhỏ hồ sơ thành các "Package" chuyên đề (Ví dụ: Package 1 - Legal & Specs, Package 2 - MEP Water, Package 3 - MEP Alarm).
  3. Dùng vòng lặp `AsyncOpenAI` để quét từng Package (Map phase).
  4. Gom toàn bộ lỗi (findings) và dùng 1 prompt cuối cùng để tổng hợp, chấm điểm (Reduce phase).
- **Nguồn**: Session 8eacf34e-8e53-4d27-a860-de8ea455c177, 2026-04-23

applies_to:
  - "Thẩm tra thiết kế"
  - "Quản lý chất lượng"
bundle: "_qc"
---

## Conventions (Quy ước)

### Phân định Thẩm quyền PCCC (Split Jurisdiction - Luật 55/2024 & NĐ 105/2025)

- **Ngữ cảnh**: Xây dựng Workflow nộp hồ sơ thẩm duyệt PCCC.
- **Vấn đề giải quyết**: Tránh hiểu nhầm rằng Cơ quan chuyên môn về xây dựng (CQCMVXD) hoặc Cảnh sát PCCC (PC07) "bao thầu" toàn bộ việc thẩm định cho một dự án.
- **Giải pháp / Quy ước**: Áp dụng triệt để nguyên tắc phân quyền theo điểm a,b,c,d,đ và e,g Khoản 1 Điều 16 Luật 55/2024:
  - CQCMVXD (Thẩm định Kiến trúc & Thụ động): Khoảng cách an toàn, giao thông, lối thoát nạn, bậc chịu lửa, giải pháp chống khói.
  - Cảnh sát PCCC (Thẩm định Cơ điện & Chủ động): Hệ thống điện PCCC, hệ thống báo/chữa cháy tự động.
- **Nguồn**: Session 8eacf34e-8e53-4d27-a860-de8ea455c177, 2026-04-23

applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
bundle: "_qc"
---

## Solutions (Giải pháp tham chiếu)

### JSON Regex Extraction từ LLM Text Stream

- **Vấn đề**: LLM (đặc biệt là Qwen) thường trả về `<think>` blocks và text lẫn lộn ngoài JSON markup, gây lỗi `JSONDecodeError`.
- **Giải pháp**: Sử dụng regex loại bỏ `<think>`, sau đó tìm kiếm chuỗi nằm giữa ```json ... ```, hoặc dự phòng bằng phương thức `string.find('{')` đến `string.rfind('}')`.
- **Nguồn**: Session 8eacf34e-8e53-4d27-a860-de8ea455c177, 2026-04-23

applies_to:
  - "Phần mềm"
bundle: "_core"
