# 🗺️ Bản đồ Định hướng: Hạ tầng Triage & Issue Management

Bản đồ này quản lý tiến trình thiết lập hệ thống sàng lọc và quản lý sự cố (Triage & Issue Tracker) cục bộ tích hợp với GitHub cho dự án `ccba-agent-platform`.

---

## 🎯 Điểm đích (Destination)
Hạ tầng Triage được xây dựng hoàn chỉnh và sẵn sàng vận hành:
- Bộ nhãn chuẩn (Triage Labels) hoạt động trên GitHub.
- Thư mục cục bộ `.md/knowledge/issues/` được cấu trúc hóa để quản lý các sự cố ngoại tuyến.
- Có cơ chế/kịch bản đồng bộ 2 chiều (gh CLI / python script) hỗ trợ kéo và đẩy trạng thái issues giữa Local và GitHub.
- Tài liệu quy trình `/ccba-triage` được cập nhật tương ứng.

---

## 📝 Ghi chú (Notes)
- Dự án hiện tại là **Hub**, do đó mọi giải pháp cần hướng tới tính tổng quát cao, dễ đóng gói thành Skill hoặc script tiện ích để các Spoke khác kế thừa dễ dàng.
- Ưu tiên các giải pháp KISS (Keep It Simple, Stupid), tránh phụ thuộc phức tạp vào các thư viện bên ngoài.

---

## 🤝 Quyết định đã chốt (Decisions so far)
- **Quyết định #1 [labels.yaml](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/labels.yaml):** Thống nhất bộ nhãn chuẩn gồm 7 nhãn phục vụ quy trình sàng lọc và phân vai xử lý sự cố.
- **Quyết định #2 [template_issue.md](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/template_issue.md):** Thiết kế định dạng issue cục bộ dạng Markdown kết hợp Frontmatter YAML giúp lưu trữ metadata và nội dung dễ dàng.
- **Quyết định #3 [sync_issues.py](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/sync_issues.py):** Phát triển script Python đồng bộ hóa issues từ GitHub API thông qua `gh` CLI về lưu trữ cục bộ.

---

## 🌫️ Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- **Xử lý xung đột đồng bộ:** Giải quyết thế nào khi nội dung issue bị sửa đổi đồng thời trên GitHub và file cục bộ?
- **Tự động hóa hoàn toàn:** Kích hoạt đồng bộ qua GitHub Actions hay thông qua lệnh CLI thủ công của Agent/Con người?

---

## 🚫 Ngoài phạm vi (Out of scope)
- Xây dựng giao diện UI/Web độc lập để quản lý issues (chỉ sử dụng file Markdown cục bộ và GitHub Web Interface).

---

## 🎫 Các Ticket ở Biên giới (Frontier Tickets)

### 1. [Ticket #1: Khảo sát & Thống nhất Bộ Nhãn Chuẩn](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/ticket-1-labels.md) [AFK] — **Đã đóng (Closed)**
- **Mục tiêu:** Thống nhất danh sách tên nhãn, màu sắc và mô tả chi tiết cho quy trình Triage của CCBA (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix, v.v.).
- **Đầu ra:** File đặc tả nhãn `labels.yaml` để có thể import tự động bằng `gh label`.

### 2. [Ticket #2: Thiết kế Định dạng File Issue Cục bộ](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/ticket-2-format.md) [AFK] — **Đã đóng (Closed)**
- **Mục tiêu:** Xác định cấu trúc file issue cục bộ trong `.md/knowledge/issues/` (Frontmatter YAML kết hợp nội dung Markdown hay thuần JSON). Đảm bảo Agent dễ dàng đọc hiểu và cập nhật.
- **Đầu ra:** File mẫu `template_issue.md`.

### 3. [Ticket #3: Thử nghiệm Cơ chế Đồng bộ bằng gh CLI](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/ticket-3-sync.md) [HITL] — **Đã đóng (Closed)**
- **Mục tiêu:** Viết script Powershell hoặc Python ngắn gọn để kéo các issue hiện có trên GitHub (nếu có) về thư mục cục bộ dưới định dạng đã thiết kế ở Ticket #2.
- **Đầu ra:** Script `sync_issues.ps1` hoặc `sync_issues.py` chạy thử nghiệm thành công.
