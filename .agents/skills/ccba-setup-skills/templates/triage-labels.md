# Nhãn Phân Loại Sự Cố & Nhiệm Vụ (Triage Labels)

Các công cụ kỹ thuật (như quy trình triage trong `/ccba-issue-to-hub`) hoạt động dựa trên 5 vai trò phân loại tiêu chuẩn. Bảng dưới đây ánh xạ các vai trò tiêu chuẩn đó sang nhãn thực tế được sử dụng trong tracker của dự án này.

| Vai trò tiêu chuẩn | Nhãn thực tế trong Tracker | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| `needs-triage` | `needs-triage` | Sự cố/Yêu cầu mới tiếp nhận, cần đánh giá sơ bộ. |
| `needs-info` | `needs-info` | Đang chờ người báo cáo bổ sung thêm thông tin. |
| `ready-for-agent` | `ready-for-agent` | Đã đặc tả đầy đủ thông tin, sẵn sàng cho Agent tự động xử lý. |
| `ready-for-human` | `ready-for-human` | Yêu cầu lập trình viên (người thật) xử lý trực tiếp. |
| `wontfix` | `wontfix` | Yêu cầu bị từ chối hoặc sẽ không thực hiện. |

Khi một công cụ yêu cầu thao tác nhãn (ví dụ: "áp dụng nhãn sẵn sàng cho Agent"), hãy sử dụng chính xác chuỗi ký tự ở cột **"Nhãn thực tế trong Tracker"** tương ứng.

*Lập trình viên có thể chỉnh sửa cột "Nhãn thực tế trong Tracker" ở bảng này để phù hợp với hệ thống nhãn có sẵn của dự án mà không cần thay đổi code của Agent.*

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
