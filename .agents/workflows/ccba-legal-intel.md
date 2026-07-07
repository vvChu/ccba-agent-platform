---
description: Khởi động quy trình tự động cào, đóng gói và tích hợp văn bản pháp luật mới từ Thư viện Pháp luật (TVPL)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_consulting"
---

# Workflow: Legal Intelligence Crawler (/ccba-legal-intel)

Sử dụng lệnh này để tự động cào, đóng gói và tích hợp văn bản pháp luật mới từ Thư viện Pháp luật (TVPL) vào hệ thống tri thức.

## Hành vi mặc định khi không có tham số (Default Behavior)
Khi người dùng gọi lệnh `/ccba-legal-intel` không kèm tham số, Agent **bắt buộc** phải:
1. Đọc tệp tin [legal_registry.yaml](../../.md/data/legal_registry.yaml) để lấy danh sách các Luật gốc (Parent Laws) đang có trong hệ thống.
2. Sinh động danh sách các ví dụ mẫu (clickable/copyable commands) tương ứng với các Luật gốc đó để người dùng dễ dàng sao chép và thực thi ngay lập tức.

## Cách ra lệnh (Command Usage)

Người dùng có thể gọi lệnh theo 3 cách tương ứng với 3 kịch bản:

### 1. Cào mới Luật gốc (New Parent Law)
*   **Cú pháp**: `/ccba-legal-intel <URL_Luat_goc>`
*   **Ví dụ**: `/ccba-legal-intel https://thuvienphapluat.vn/van-ban/Luat-Xay-dung-2025`
*   **Mô tả**: Tạo một OKF Bundle độc lập cấp cao nhất tại `.md/legal_docs/<slug>/` và tự động tải đệ quy các văn bản hướng dẫn ban hành kèm.

### 2. Cào bổ sung văn bản hướng dẫn vào Luật cha hiện có (Add Guiding Doc)
*   **Cú pháp**: `/ccba-legal-intel <URL_Nghi_dinh_Thong_tu> parent=<ID_Luat_cha>`
*   **Ví dụ**: `/ccba-legal-intel https://thuvienphapluat.vn/van-ban/...Thong-tu-36-2026 parent=LXD-2025`
*   **Mô tả**: Tải và đóng gói văn bản hướng dẫn, tự động tích hợp phẳng vào thư mục con `guiding_docs/` và `guiding_docs/appendices/` của Luật cha tương ứng.

### 3. Cập nhật chênh lệch lược đồ (Delta Update)
*   **Cú pháp**: `/ccba-legal-intel delta=<ID_Luat>`
*   **Ví dụ**: `/ccba-legal-intel delta=LXD-2025`
*   **Mô tả**: Quét lược đồ trực tuyến trên TVPL của Luật tương ứng và chỉ tải bổ sung các văn bản hướng dẫn mới ban hành chưa tồn tại trong registry cục bộ.

---

Agent tiếp nhận bắt buộc phải nạp và thực thi kỹ năng `ccba-legal-intel` tại [SKILL.md](../skills/ccba-legal-intel/SKILL.md) để bắt đầu quy trình kiểm tra cổng Chrome CDP, thực thi cào dữ liệu, phân tách phụ lục, sửa liên kết tương đối và đăng ký văn bản mới vào Registry hệ thống.
