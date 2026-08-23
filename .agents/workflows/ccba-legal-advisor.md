---
description: "Tư vấn & Giải đáp Pháp lý Xây dựng: Tự động phân tích câu hỏi mơ hồ, phỏng vấn làm rõ thích ứng, truy xuất tri thức OKF v2.2 và xuất Phiếu Ý kiến Pháp lý (Legal Opinion) chuẩn mực. Kích hoạt khi người dùng hỏi các câu hỏi về cấp phép xây dựng, PCCC, nghiệm thu, đấu thầu, hoặc xin tư vấn pháp lý công trình."
disable-model-invocation: true
---

# Workflow: Tư Vấn & Giải Đáp Pháp Lý Xây Dựng (/ccba-legal-advisor)

Khi người dùng kích hoạt lệnh này hoặc đặt các câu hỏi liên quan đến tư vấn quy chuẩn, cấp phép, nghiệm thu hay thẩm tra pháp lý công trình, Agent hãy nạp và thực thi kỹ năng `legal-advisor` tại [SKILL.md](../skills/legal-advisor/SKILL.md) để:
1. Tiếp nhận câu hỏi và phân loại độ phức tạp (Fast-track hoặc Phỏng vấn thích ứng).
2. Lồng ghép linh hoạt 4 Khung Mẫu Tương Tác Động (Diagnostic, Time-Travel, Matrix Checklist, Atomic Template).
3. Truy xuất chính xác cây điều khoản AST và bảng số liệu 2D từ kho tri thức OKF v2.2.
4. Trình bày câu trả lời theo đúng Form Phiếu Giải Đáp Pháp Lý CCBA 4 phần.
