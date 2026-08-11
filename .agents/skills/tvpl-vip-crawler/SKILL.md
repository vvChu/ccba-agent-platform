---
name: tvpl-vip-crawler
description: Kỹ năng tự động kết nối tài khoản VIP Thư viện Pháp luật, xử lý Cloudflare/Popups, bảo vệ VIP Session (CookieVault), khôi phục bảng biểu và đóng gói OKF Bundle.
---

# Kỹ Năng Cào & Đóng Gói Văn Bản VIP Thư Viện Pháp Luật (`tvpl-vip-crawler`)

Kỹ năng này chịu trách nhiệm tự động hóa toàn bộ quy trình thu thập, đăng nhập tài khoản VIP Thư viện Pháp luật, duy trì session Chrome CDP cố định tại `.md/data/chrome_vip_profile`, vượt các rào chắn kiểm tra Cloudflare Security, tự động gia hạn session cookie qua `CookieVault` và đóng gói văn bản pháp lý thành bộ chuẩn **OKF (Open Knowledge Format) Bundle**.

---

## 🛠️ Hướng Dẫn Sử Dụng & Luồng Thực Thi

### 1. Cấu Hình Tài Khoản VIP (`.env`)
Đảm bảo các biến môi trường sau đã được khai báo tại tệp `.env` của dự án:
```env
TVPL_USERNAME=vuvanchu119
TVPL_PASSWORD=ccba@ibst
DRIVE_FOLDER_ID=1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2
```

### 2. Kích Hoạt Lệnh Cào Văn Bản
Chạy script tự động hóa với đường dẫn URL văn bản cần cào từ TVPL:
```bash
python scripts/tvpl_vip_crawler.py "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Thong-tu-06-2022-TT-BXD-Quy-chuan-QCVN-06-2022-BXD-An-toan-chay-cho-nha-va-cong-trinh-544059.aspx"
```

---

## 📁 Cấu Trúc Kết Xuất OKF Bundle (`.md/legal_docs/<slug>/`)

Mỗi văn bản cào về từ TVPL VIP sẽ được tự động cấu trúc hóa thành một thư mục OKF Bundle độc lập:

```text
.md/legal_docs/<slug>/
├── metadata.yaml        <-- Định danh ID, tên văn bản, ngày hiệu lực & quan hệ pháp lý
├── index.md            <-- Mục lục liên kết tương đối (Relative links)
├── concept.md          <-- Toàn văn nội dung quy chuẩn / văn bản (Markdown)
└── guiding_docs/       <-- Thư mục chứa các văn bản sửa đổi, bổ sung hoặc thông tư hướng dẫn
```

---

## 🔒 Quy Tắc Bảo Mật & Duy Trì Session Chrome CDP

1. **Kho Lưu Trữ Cookie Mã Hóa (`CookieVault`):**
   Lưu trữ file cookie tại `.md/data/chrome_vip_profile/cookies.json` và nạp vào HTTP Session giúp giảm 90% tài nguyên và ẩn danh hoàn toàn.
2. **Khóa Mutex Lock & Nhịp Jitter Queue (`TVPLSessionMutex`):**
   Mọi quá trình kết nối đều được bảo vệ bởi `TVPLSessionMutex` với nhịp sinh học Jitter Delay $3.5\text{s} \rightarrow 7.2\text{s}$ tránh bị khóa IP/tài khoản VIP.
3. **Kiểm Toán Session (`.md/data/tvpl_session_audit.log`):**
   Ghi nhận minh bạch mọi mốc thời gian đăng nhập, vượt Cloudflare và lưu lượng cào tệp.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
