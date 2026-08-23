---
description: Quy trình thực thi cào dữ liệu văn bản pháp luật VIP từ Thư viện Pháp
  luật (TVPL) qua Deep Seam TVPLCrawler
disable-model-invocation: true
bundle: _consulting
command: /ccba-tvpl-vip-crawler
triggers:
- tvpl-vip-crawler
- tvpl vip crawler
- cào thư viện pháp luật
- tvpl vip
- vip crawler
---
# Quy trình thực thi Slash Command `/ccba-tvpl-vip-crawler`

Khi người dùng kích hoạt lệnh Slash Command này dưới dạng:
`/ccba-tvpl-vip-crawler <đường-dẫn-url-hoặc-tên-văn-bản-tvpl>`

Agent tiếp nhận lệnh bắt buộc phải thực thi theo các bước sau:

1. **Kiểm tra Cấu hình & Nạp Kỹ năng**:
   - Đọc hướng dẫn tại [SKILL.md](../skills/tvpl-vip-crawler/SKILL.md).
   - Xác nhận tài khoản VIP `TVPL_USERNAME` và `TVPL_PASSWORD` sẵn sàng tại `.env`.

2. **Kích hoạt Deep Seam TVPLCrawler Trực tiếp**:
   - Thực thi lệnh cào tự động qua Facade:
     ```bash
     python scripts/legal/tvpl_vip_crawler.py "<đường-dẫn-url-hoặc-tên-văn-bản-tvpl>"
     ```

3. **Cấu trúc hóa OKF Bundle & Kiểm tra Kết quả**:
   - Kiểm tra kết quả đóng gói tại `.md/legal_docs/<slug>/`.
   - Báo cáo kết quả đóng gói thành công bao gồm các tệp `metadata.yaml`, `concept.md`, `index.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
