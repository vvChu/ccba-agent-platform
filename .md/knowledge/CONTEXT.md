# 📖 Bảng Thuật Ngữ Nghiệp Vụ & Thiết Kế (Domain Context & Glossary)

Tài liệu này lưu trữ các thuật ngữ nghiệp vụ, khái niệm kỹ thuật cốt lõi và các từ khóa định danh duy nhất của CCBA Agent Platform.

---

## 1. Các Thuật Ngữ Kỹ Nghệ AI & Quy Trình (AI Engineering & SDLC)

### 🚀 ccba-prototype (Mẫu thử nhanh)
*   **Định nghĩa:** Mã nguồn thô viết nhanh, chỉ dùng một lần (throwaway code) để giải quyết và trả lời một câu hỏi thiết kế cụ thể (Logic hoặc UI) trước khi triển khai chính thức.
*   **Nguyên tắc:** *Throwaway from day one* (xóa bỏ hoặc hấp thụ sau khi xong), *No persistence* (chạy hoàn toàn trên bộ nhớ tạm).

### 📚 ccba-research (Nghiên cứu chạy ngầm)
*   **Định nghĩa:** Quy trình khởi chạy một subagent nghiên cứu (`research` subagent) chạy song song dưới nền để điều tra các nguồn tài liệu sơ cấp đáng tin cậy (official docs, source code, APIs, VBPL) và xuất báo cáo Markdown.
*   **Mục tiêu:** Giảm thiểu phình to cửa sổ ngữ cảnh (Context Window Bloating) cho phiên làm việc chính.

### ⚙️ SDLC Implementation Loop (Chu kỳ thực thi mã nguồn)
*   **Định nghĩa:** Quy trình thực thi code khép kín bắt buộc được quy định trong Hiến pháp `AGENTS.md` bao gồm 3 bước: (1) Viết test trước (TDD) nếu được thỏa thuận, (2) Kiểm tra kiểu và chạy thử liên tục, (3) Rà soát chất lượng code bằng `/ccba-code-review` trước khi commit/merge.

### 🧠 Facts vs Decisions (Dữ kiện và Quyết định)
*   **Facts (Dữ kiện thực tế):** Các thông tin khách quan đã tồn tại trong codebase hoặc tài liệu mà Agent có thể tự tra cứu mà không cần hỏi người dùng.
*   **Decisions (Quyết định thiết kế):** Các lựa chọn kiến trúc, nghiệp vụ mang tính đánh đổi thuộc thẩm quyền của kỹ sư (con người) — Agent bắt buộc phải hỏi từng câu một và đợi phản hồi.

### 🚫 Negation (Lỗi gợi ý phủ định)
*   **Định nghĩa:** Một lỗi thiết kế prompt (failure mode) khi điều khiển Agent bằng cấm đoán (*không được làm X*). Lỗi này vô tình kéo hành vi bị cấm vào ngữ cảnh khiến Agent dễ phạm phải hơn (hiệu ứng "Don't think of an elephant"). Khắc phục bằng cách mô tả hành vi tích cực cần thực hiện.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
