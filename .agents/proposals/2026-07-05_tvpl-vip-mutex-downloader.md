---
proposal_id: "2026-07-05_tvpl-vip-mutex-downloader"
type: "skill"
name: "tvpl-vip-mutex-downloader"
status: "open"
priority: "High"
proposed_by_project: "ccba-agent-platform"
proposed_date: "2026-07-05"
applies_to:
  - "crawler"
  - "legal-intel"
---

## Mô tả
Cơ chế tải tài liệu pháp lý 3 cấp (Cache-First) kết hợp khóa Mutex chống kích đăng nhập phiên VIP dành cho các tác nhân và luồng cào dữ liệu pháp lý.

## Vấn đề giải quyết
- **Xung đột phiên đăng nhập**: Khi có nhiều tác nhân hoặc luồng cào chạy song song cùng sử dụng một tài khoản VIP Thư viện Pháp luật (TVPL), việc đăng nhập đồng thời sẽ gây kích đăng nhập lẫn nhau (kick-out), dẫn đến lỗi cào dữ liệu và khóa tài khoản.
- **Tốc độ và Chi phí**: Việc tải tệp tin văn bản pháp luật trực tiếp từ TVPL lặp đi lặp lại tiêu tốn tài nguyên mạng và dễ bị chặn IP (rate limit).

## Giải pháp / Cấu trúc đề xuất
- **VIP Session Mutex Lock**: Sử dụng một tệp khóa nguyên tử (`.lock`) chứa PID và thời gian để đồng bộ hóa quyền đăng nhập giữa các tiến trình chạy song song, tự động chờ (retry loop) và giải phóng khóa an toàn trong block `try...finally`.
- **Three-Tier Cache-First Downloader**:
  1. Kiểm tra sự tồn tại của tệp đệm cục bộ (Local Cache).
  2. Nếu không có, đối soát với Shared Cache (Google Drive hoặc S3).
  3. Chỉ tải trực tuyến từ TVPL nếu cả 2 nguồn đệm trên đều không có.
