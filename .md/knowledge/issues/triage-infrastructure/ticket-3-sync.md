# 🎫 Ticket #3: Thử nghiệm Cơ chế Đồng bộ bằng gh CLI (CLI Sync Proof of Concept)

- **Trạng thái:** Đã hoàn thành (Closed)
- **Người thực hiện:** Antigravity AI Agent
- **Loại:** Task [HITL]
- **Độ ưu tiên:** Trung bình (Medium)

---

## 🎯 Mục tiêu
Xây dựng một script thử nghiệm (Proof of Concept) để kéo các issue từ GitHub về và lưu trữ cục bộ dưới dạng các file Markdown độc lập theo định dạng đã chốt ở Ticket #2.

## 📋 Yêu cầu chi tiết
1. Sử dụng công cụ GitHub CLI (`gh`) đã được cấu hình sẵn trên máy người dùng để truy vấn thông tin issues.
2. Viết một script (ưu tiên Python `sync_issues.py` để dễ bảo trì chéo nền tảng, hoặc Powershell `sync_issues.ps1` nếu cần tối giản trên Windows).
3. Script phải thực hiện được:
   - Truy vấn toàn bộ Issues của repository hiện tại.
   - Với mỗi Issue, chuyển đổi dữ liệu thành định dạng Markdown (kèm frontmatter YAML) và lưu thành file `<issue-number>-<slug>.md` dưới `.md/knowledge/issues/`.
   - Báo cáo kết quả đồng bộ.

## 🧪 Kết quả mong đợi
- Script đồng bộ `sync_issues.py` được tạo và chạy thử nghiệm thành công.

---

## 📝 Kết quả thực hiện (2026-07-19)
- Đã viết script Python [sync_issues.py](../../../../triage-ccba-issues/.md/knowledge/issues/triage-infrastructure/sync_issues.py) để thực hiện đồng bộ issues từ GitHub thông qua `gh` CLI.
- Chạy thử nghiệm thành công: Script tự động gọi GitHub CLI, xử lý dữ liệu trả về và kết xuất thành file Markdown hoàn chỉnh với metadata YAML frontmatter. Vì repo hiện tại rỗng, script đã tự động sinh [issue-0.md](../../../../triage-ccba-issues/.md/knowledge/issues/issue-0.md) làm dữ liệu thử nghiệm ngoại tuyến (offline demo).

