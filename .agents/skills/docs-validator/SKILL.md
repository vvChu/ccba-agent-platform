---
name: docs-validator
description: "Quét kiểm định tài liệu Markdown chống ảo ảnh (hallucinations), broken links và cấu hình thiếu."
user-invocable: true
when_to_use: "Dùng khi cần kiểm tra chất lượng tài liệu Markdown, trước khi commit hoặc tạo Pull Request, hoặc khi người dùng yêu cầu 'validate docs', 'kiểm tra tài liệu'."
category: quality-assurance
keywords: [validate, docs, documentation, hallucination, links]
metadata:
  author: ccba-team
  version: "1.0.0"
---

# Skill: Docs Validator (Kiểm định tài liệu chính quy)

Skill này giúp AI Agent tự động chạy và phân tích báo cáo kiểm định chất lượng tài liệu Markdown để chống lỗi thời và ảo ảnh (hallucinations) so với codebase thực tế.

---

## Cách Kích hoạt & Thực thi

Khi người dùng yêu cầu hoặc trước khi hoàn tất (commit/PR) tài liệu kỹ thuật, bạn **bắt buộc** phải chạy lệnh kiểm định:

```bash
python scripts/validate_docs.py . --src scripts,packages
```

## Các nhóm lỗi cần kiểm tra và xử lý:

### 1. Broken Link Error (Lỗi liên kết hỏng) — [CHẶN CỨNG - EXIT 1]
- **Vấn đề:** Các đường dẫn tương đối (vd: `[config](./setup.md)`) trỏ vào tệp tin không tồn tại.
- **Hành động:** Bạn **phải** kiểm tra lại cấu trúc thư mục thực tế và sửa lại đường dẫn cho đúng. Đây là lỗi nghiêm trọng sẽ chặn đứng commit hoặc build CI.

### 2. Code Ref Warning (Cảnh báo ký hiệu code) — [CẢNH BÁO MỀM]
- **Vấn đề:** Tài liệu nhắc đến các hàm `my_func()` hoặc class PascalCase `MyClass` không được định nghĩa trong codebase (thường do AI tự bịa ra).
- **Hành động:** Xác nhận xem hàm/lớp đó có bị đổi tên hoặc xóa trong đợt refactor không. Sửa lại tên ký hiệu cho đúng với thực tế mã nguồn.

### 3. Env Var Warning (Cảnh báo biến cấu hình) — [CẢNH BÁO MỀM]
- **Vấn đề:** Tài liệu nhắc tới các biến môi trường cấu hình (vd: `API_KEY`) nhưng tệp mẫu `.env.example` ở root dự án không khai báo.
- **Hành động:** Bổ sung khai báo biến mẫu này vào `.env.example` kèm giá trị demo hoặc mô tả.

---

## Nguyên tắc Vận hành (Guidelines)
- **Docs-as-Code:** Coi tài liệu là một phần của code. Luôn giữ tài liệu ngắn gọn (dưới 500 dòng/file) để dễ bảo trì.
- **Tự động hóa:** Tích hợp validator vào Git pre-commit hook (`.pre-commit-config.yaml`) và GitHub Actions CI/CD để tự động kiểm tra trên PR.
- **Bypass:** Trong trường hợp khẩn cấp hoặc tài liệu nghiên cứu cũ có cảnh báo Code Ref nghi vấn (không phải link hỏng), validator sẽ trả về exit code 0 và cho phép bypass tự động.

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
