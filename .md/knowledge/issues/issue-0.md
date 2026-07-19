---
id: 0
title: "Offline Demo Issue - Triage Setup Check"
state: "ready-for-agent"
labels:
  - "needs-triage"
  - "documentation"
  - "ready-for-agent"
assignee: "Antigravity AI Agent"
created_at: "2026-07-19T12:00:00Z"
updated_at: "2026-07-19T19:15:00Z"
---

# 📖 Mô tả (Description)
Đây là issue mẫu được tạo tự động bởi script đồng bộ khi repo GitHub chưa có issue nào. Nhằm kiểm tra cấu trúc lưu trữ và hoạt động của Agent Triage.

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent** (2026-07-19T19:15:00Z):
> Đã xác nhận hạ tầng triage hoạt động ổn định. Nhãn `ready-for-agent` được gán kèm Agent Brief thử nghiệm dưới đây.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Mở rộng script `sync_issues.py` để tự động dọn dẹp các tệp issue cục bộ cũ không còn tồn tại trên GitHub.

### Hành vi hiện tại (Current behavior)
- Script `sync_issues.py` hiện tại chỉ thực hiện kéo (pull) và ghi đè/tạo mới các file issue cục bộ.
- Nếu một issue bị xóa trên GitHub hoặc đóng lại và không nằm trong danh sách kéo về, file cục bộ cũ vẫn tồn tại trong thư mục `.md/knowledge/issues/` gây rác dữ liệu.

### Hành vi mong muốn (Desired behavior)
- Script `sync_issues.py` sẽ so sánh danh sách issue IDs kéo về từ GitHub và danh sách file issue cục bộ hiện có trong thư mục `.md/knowledge/issues/`.
- Nếu có file issue cục bộ (dạng `issue-<id>.md` với id > 0) không nằm trong danh sách issue kéo về từ GitHub, script sẽ tự động xóa file đó đi để đảm bảo tính đồng bộ sạch.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- Script Python sử dụng thư viện `os` để quét thư mục và xóa tệp tin thừa.

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] Quét thư mục và lấy danh sách các file `issue-*.md`.
- [ ] So sánh ID của file với danh sách ID kéo về từ API.
- [ ] Thực hiện xóa file nếu không khớp và ghi log thông báo.
- [ ] File demo `issue-0.md` được bỏ qua khỏi quy trình xóa này (giữ lại làm template/offline check).

### Phạm vi loại trừ (Out of scope)
- Chưa cần xử lý đồng bộ đẩy ngược (push) nội dung thay đổi cục bộ lên GitHub trong scope này.
