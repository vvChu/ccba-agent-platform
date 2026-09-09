---
name: ccba-ask
description: Tư vấn và định hướng lựa chọn kỹ năng hoặc workflow phù hợp với nhu cầu
  phát triển.
disable-model-invocation: true
bundle: _core
triggers:
- ccba-ask
- tư vấn
- định hướng
- luồng công việc
- bản đồ kỹ năng
- ccba-wait-what
- wait-what
- ccba-brainstorm
- brainstorm
---

# Bản đồ Định hướng Kỹ năng Nền tảng (CCBA Ask Guide)

Kỹ năng này giúp định tuyến, định hướng cho cả AI Agent và Nhà phát triển để lựa chọn đúng Slash Command hoặc Kỹ năng (Skill) phù hợp nhất với trạng thái công việc hiện tại.

> [!IMPORTANT]
> **Nguồn tin cậy (Source of Truth):**
> Tất cả các Slash Command trong tài liệu này đều được định tuyến dựa trên danh mục dịch vụ tại [catalog.yaml](../platform-loader/catalog.yaml). Vui lòng kiểm tra danh mục này trước khi thực thi để đảm bảo lệnh đã được đăng ký thành công trong phân vùng (spoke) hiện tại.

---

## Luồng công việc chính: Từ Ý tưởng đến Phát hành (Idea → Ship)

Đây là lộ trình chuẩn nhất của mọi yêu cầu phát triển tính năng mới trong Platform:

1. **Làm sắc nét ý tưởng:** Gọi `/ccba-grilling` để phỏng vấn sâu rộng và ghi nhận tri thức dự án vào `CONTEXT.md` và các bản ghi quyết định kiến trúc (ADRs).
2. **Rẽ nhánh — prototype hay spec:**
   - Nếu cần kiểm chứng giao diện/hành vi trực quan: Chạy `/ccba-handoff` ➔ mở phiên `/ccba-prototype` ➔ `/ccba-handoff` kết quả trở lại.
   - Nếu là build nhiều phiên: Chạy `/ccba-to-spec` để tổng hợp thành Đặc tả Kỹ thuật.
3. **Phân rã tác vụ công việc:** Gọi `/ccba-to-tickets` để bẻ nhỏ Spec thành các ticket độc lập dạng lát cắt dọc (Tracer-bullet vertical slices).
4. **Triển khai lập trình (TDD):** Mở cửa sổ Agent sạch và chạy `/ccba-implement` (hoặc `/ccba-tdd`) để hiện thực hóa từng ticket độc lập.
5. **Kiểm soát chất lượng (QC):** Chạy `/ccba-ai-qc` để quét chất lượng và rà soát lỗi đa bộ môn.
6. **Bàn giao cuối phiên làm việc:** Chạy `/ccba-session-retrospective` (hoặc `/ccba-handoff`) để dọn dẹp môi trường và tổng hợp tri thức bàn giao.

> [!TIP]
> **Context Hygiene (Vệ sinh Context):** Giữ Bước 1–3 trong cùng một cửa sổ context liên tục trước khi bẻ ticket. Mỗi ticket triển khai ở Bước 4 nên chạy trên một phiên làm việc/agent sạch riêng biệt để tránh cạn kiệt Context Budget.

---

## Các luồng bổ trợ (On-ramps & Upkeep)

*   **Tiếp nhận yêu cầu thô / Báo lỗi từ bên ngoài:** Chạy `/ccba-triage` để phân loại trạng thái, lọc trùng lặp với `.out-of-scope/` và soạn thảo Agent Brief.
*   **Xử lý lỗi hóc búa / Regression:** Sử dụng kỹ năng `ccba-diagnosing-bugs` để xây dựng vòng phản hồi nhanh và viết test hồi quy trước khi vá lỗi.
*   **Upkeep kiến trúc hệ thống:** Chạy `/ccba-improve-codebase-architecture` để phát hiện các module nông và deepening cấu trúc code.
*   **Không gian học tập:** Chạy `/ccba-teach` để khởi động không gian bài giảng/nghiên cứu trong thư mục ẩn `.md/teach/`.

---

## Quy trình tư vấn định hướng (Process)

1. **Phân tích yêu cầu và trạng thái hiện tại:**
   - Đọc kỹ mô tả nhu cầu của người dùng (Ví dụ: "Tôi muốn bắt đầu một dự án mới", "Có bug lỗi kết nối", "Tôi muốn dọn dẹp code").
   - Xác định xem công việc thuộc luồng chính (Ý tưởng -> Ship) hay luồng bổ trợ (Triage/Diagnose/Upkeep).
   - **Tiêu chí hoàn thành:** Xác định đúng nhóm tính năng và trạng thái hiện tại của workspace để đưa ra gợi ý chuẩn xác.

2. **Khuyến nghị Slash Command phù hợp:**
   - Trình bày rõ ràng Slash Command nên chạy tiếp theo (nhúng link file workflow tương ứng) kèm theo tóm tắt 1 dòng lý do lựa chọn.
   - Trình bày sơ đồ luồng công việc tiếp theo để người dùng hình dung các bước kế tiếp.
   - **Tiêu chí hoàn thành:** Đưa ra được ít nhất một đề xuất Slash Command cụ thể phù hợp với ngữ cảnh người dùng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/clarification_patterns.md` | Mẫu câu và kỹ thuật phỏng vấn làm rõ ngữ cảnh khi gặp yêu cầu mơ hồ |
| `references/brainstorm_templates.md` | Khung mẫu câu hỏi định hướng tư duy và giải pháp sáng tạo |

