# 🎫 Ticket #2: Thiết kế Định dạng File Issue Cục bộ (Local Issue Format)

- **Trạng thái:** Đã hoàn thành (Closed)
- **Người thực hiện:** Antigravity AI Agent
- **Loại:** Research [AFK]
- **Độ ưu tiên:** Trung bình (Medium)

---

## 🎯 Mục tiêu
Thiết lập khuôn mẫu (template) và định dạng lưu trữ cho các issue cục bộ dưới `.md/knowledge/issues/` để đảm bảo Agent và Con người đều có thể dễ dàng đọc, viết và theo dõi.

## 📋 Yêu cầu chi tiết
1. Quyết định định dạng lưu trữ:
   - File Markdown `.md` kèm Frontmatter YAML để lưu metadata (như trạng thái, nhãn, người thực hiện, thời gian tạo, v.v.).
   - Hay file JSON/YAML riêng biệt?
2. Thiết kế cấu trúc file issue Markdown mẫu bao gồm các phần:
   - Metadata (YAML frontmatter): ID, Title, State, Labels, Assignee, CreatedAt, UpdatedAt.
   - Nội dung mô tả sự cố (Description).
   - Nhật ký thảo luận (Comments/Discussion).
   - Phần Agent Brief (nếu trạng thái chuyển sang `ready-for-agent`).
3. Tạo file mẫu `template_issue.md` làm tài liệu tham khảo.

## 🧪 Kết quả mong đợi
- Bản thiết kế định dạng issue cục bộ được ghi nhận.
- File `template_issue.md` được tạo thành công tại thư mục `.md/knowledge/issues/triage-infrastructure/`.

---

## 📝 Kết quả thực hiện (2026-07-19)
- Đã lựa chọn định dạng **Markdown kết hợp Frontmatter YAML** để lưu trữ issues ngoại tuyến. Định dạng này giúp con người dễ dàng tương tác qua git/IDE, đồng thời Agent có thể parse metadata bằng thư viện YAML tiêu chuẩn và đọc mô tả/brief trực tiếp bằng định dạng Markdown.
- Đã xuất bản mẫu issue chuẩn tại [template_issue.md](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/template_issue.md).

