---
name: docs-validator
description: Quét kiểm định tài liệu Markdown chống ảo ảnh (hallucinations), broken links và cấu hình thiếu.
disable-model-invocation: true
category: quality-assurance
keywords: [validate, docs, documentation, hallucination, links]
metadata:
  author: ccba-team
  version: "1.0.0"
---

# Skill: Docs Validator (Kiểm định tài liệu chính quy)

Skill này giúp AI Agent tự động chạy và phân tích báo cáo kiểm định chất lượng tài liệu Markdown để chống lỗi thời và ảo ảnh (hallucinations) so với codebase thực tế. Do là kỹ năng chạy theo yêu cầu trực tiếp từ người dùng, nó được thiết lập ở trạng thái `disable-model-invocation: true` để tránh hao phí tokens trong context window mỗi lượt hội thoại.

---

## Cách Kích hoạt & Thực thi

Khi cần kiểm tra chất lượng tài liệu hoặc trước khi commit/PR tài liệu kỹ thuật, Agent thực thi lệnh kiểm định (xác định `hub_path` để gọi đúng vị trí script):

```bash
python [hub_path]/scripts/validate_docs.py . --src scripts,packages
```

---

## Quy tắc xử lý lỗi phát hiện

### 1. Lỗi liên kết hỏng (Broken Link Error) — [CHẶN CỨNG - EXIT 1]
- **Vấn đề:** Các liên kết tương đối trỏ vào tệp tin không tồn tại.
- **Hành động:** Bắt buộc kiểm tra cấu trúc thư mục và sửa lại đường dẫn liên kết cho đúng. Đây là lỗi nghiêm trọng sẽ chặn build CI/CD.

### 2. Cảnh báo ký hiệu code (Code Ref Warning) — [CẢNH BÁO MỀM]
- **Vấn đề:** Tài liệu nhắc đến các hàm hoặc class không được định nghĩa trong codebase thực tế (do AI ảo tưởng hoặc ký hiệu đã bị xóa/đổi tên).
- **Hành động:** Đối chiếu codebase, sửa lại ký hiệu cho đúng với thực tế mã nguồn.

### 3. Cảnh báo biến cấu hình (Env Var Warning) — [CẢNH BÁO MỀM]
- **Vấn đề:** Tài liệu nhắc tới các biến cấu hình môi trường nhưng `.env.example` ở root dự án chưa khai báo.
- **Hành động:** Bổ sung ngay khai báo biến mẫu này vào `.env.example`.
