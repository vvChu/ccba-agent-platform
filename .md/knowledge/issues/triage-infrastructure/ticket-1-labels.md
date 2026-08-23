# 🎫 Ticket #1: Khảo sát & Thống nhất Bộ Nhãn Chuẩn (Triage Labels)

- **Trạng thái:** Đã hoàn thành (Closed)
- **Người thực hiện:** Antigravity AI Agent
- **Loại:** Research [AFK]
- **Độ ưu tiên:** Cao (High)

---

## 🎯 Mục tiêu
Định nghĩa và thống nhất bộ nhãn (labels) trên GitHub để phục vụ quy trình sàng lọc và phân vai xử lý sự cố.

## 📋 Yêu cầu chi tiết
1. Khảo sát các nhãn mặc định của GitHub hiện tại (đã làm sơ bộ, có 9 nhãn mặc định).
2. Thiết kế danh sách nhãn chuyên biệt cho quy trình Triage của CCBA:
   - `needs-triage` (Màu sắc đề xuất: `#fbca04`, Mô tả: "Sự cố mới tiếp nhận, cần đánh giá sơ bộ")
   - `needs-info` (Màu sắc đề xuất: `#fef2c0`, Mô tả: "Cần người báo cáo bổ sung thông tin")
   - `ready-for-agent` (Màu sắc đề xuất: `#0e8a16`, Mô tả: "Đã có Agent Brief, sẵn sàng cho Agent tự động xử lý")
   - `ready-for-human` (Màu sắc đề xuất: `#b60205`, Mô tả: "Yêu cầu lập trình viên con người xử lý")
3. Tạo file cấu hình `labels.yaml` chứa thông tin chi tiết (tên, màu, mô tả) của tất cả nhãn trên để phục vụ việc tạo tự động qua CLI.

## 🧪 Kết quả mong đợi
- File `labels.yaml` được tạo thành công tại thư mục `.md/knowledge/issues/triage-infrastructure/`.

---

## 📝 Kết quả thực hiện (2026-07-19)
- Đã khảo sát và thống nhất bộ nhãn chuẩn bao gồm: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, `bug`, và `enhancement`.
- Đã xuất đặc tả nhãn hoàn chỉnh ra tệp tin [labels.yaml](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/labels.yaml).

