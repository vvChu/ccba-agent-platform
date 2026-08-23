---
name: tvpl-vip-crawler
description: Kỹ năng tự động cào và đóng gói văn bản pháp luật VIP TVPL qua Deep Seam
  TVPLCrawler (tự động CookieVault & Mutex).
disable-model-invocation: true
bundle: _software
triggers:
- tvpl-vip-crawler
- tvpl vip crawler
- cào thư viện pháp luật
- tvpl vip
- vip crawler
---
# Kỹ Năng Cào & Đóng Gói Văn Bản VIP Thư Viện Pháp Luật (`tvpl-vip-crawler`)

Kỹ năng này điều phối quy trình thu thập, đăng nhập tài khoản VIP Thư viện Pháp luật, tự động quản lý cookie qua `CookieVault`, bảo vệ phiên làm việc bằng `TVPLSessionMutex`, vượt các rào chắn kiểm tra Cloudflare/Popups và đóng gói văn bản pháp lý thành bộ chuẩn **OKF (Open Knowledge Format) Bundle** thông qua Deep Seam **`TVPLCrawler`** ([`packages/ccba-legal-intel`](../../packages/ccba-legal-intel)).

---

## 🛠️ Hướng Dẫn Vận Hành & Luồng Thực Thi

1. **Kiểm tra Cấu hình Môi trường (`.env`)**:
   - Đảm bảo các biến môi trường sau đã được khai báo tại tệp `.env` của dự án:
     ```env
     TVPL_USERNAME=vuvanchu119
     TVPL_PASSWORD=ccba@ibst
     ```
   - **Tiêu chí hoàn thành:** Xác nhận biến môi trường `TVPL_USERNAME` và `TVPL_PASSWORD` đã sẵn sàng.

2. **Kích hoạt Lệnh Cào Văn bản qua Deep Seam**:
   - Sử dụng Python API hoặc Script CLI Facade:
     ```python
     from ccba_legal import TVPLCrawler

     crawler = TVPLCrawler()
     doc = crawler.fetch_document("https://thuvienphapluat.vn/van-ban/...")
     ```
     Hoặc chạy qua CLI:
     ```bash
     python scripts/legal/tvpl_vip_crawler.py "https://thuvienphapluat.vn/van-ban/..."
     ```
   - **Tiêu chí hoàn thành:** Văn bản và tệp đính kèm được tải về đầy đủ mà không bị lỗi xác thực hay xung đột session lock.

3. **Cấu trúc hóa OKF Bundle (`.md/legal_docs/<slug>/`)**:
   - Kiểm tra kết quả đóng gói tại thư mục đích:
     ```text
     .md/legal_docs/<slug>/
     ├── metadata.yaml        <-- Định danh ID, tên văn bản, ngày hiệu lực & quan hệ pháp lý
     ├── index.md            <-- Mục lục liên kết tương đối (Relative links)
     ├── concept.md          <-- Toàn văn nội dung quy chuẩn / văn bản (Markdown)
     └── guiding_docs/       <-- Văn bản sửa đổi, bổ sung hoặc thông tư hướng dẫn
     ```
   - **Tiêu chí hoàn thành:** Thư mục bundle chứa đầy đủ các tệp `metadata.yaml`, `concept.md`, `index.md` hợp lệ.

---

## 🔒 Cơ Chế Tự Động Trong Deep Seam (`TVPLCrawler`)

1. **Kho Lưu Trữ Cookie Tự Động (`CookieVault`):** Lưu trữ cookie tại `.md/data/chrome_vip_profile/cookies.json` và nạp vào HTTP session giúp tăng tốc độ tải và ẩn danh hoàn toàn.
2. **Khóa Mutex An Toàn (`TVPLSessionMutex`):** Tự động khóa và giải phóng lock file `.md/data/tvpl_vip_session.lock` (bọc trong `try...finally`), kèm nhịp Jitter Delay tránh bị khóa IP/tài khoản VIP.
3. **Multi-tier Fallback:** Tự động chuyển đổi giữa HTTP Crawler tốc độ cao và Chrome CDP Browser khi gặp Cloudflare/Anti-bot.
