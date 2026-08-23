# BẢN ĐỒ ĐỊNH HƯỚNG WAYFINDER: XÂY DỰNG SKILL `tvpl-vip-crawler`

- **Tên dự án / Kỹ năng:** `tvpl-vip-crawler`
- **Đường dẫn lưu trữ:** `.md/knowledge/issues/tvpl_vip_crawler_skill/map.md`
- **Mã Slash Command dự kiến:** `/ccba-tvpl-vip-crawler`

---

## 🎯 1. ĐIỂM ĐÍCH (DESTINATION)

Xây dựng Kỹ năng chính thức **`tvpl-vip-crawler`** và Workflow Slash Command `/ccba-tvpl-vip-crawler` đạt tiêu chuẩn CCBA Agent Platform. Kỹ năng này cho phép AI Agent tự động kết nối trình duyệt Chrome CDP, duy trì session đăng nhập VIP Thư viện Pháp luật (`vuvanchu119` / `ccba@ibst`), vượt rào chắn Cloudflare & popup cảnh báo session, tải tệp `.docx` / `.pdf` toàn văn 100% và tự động phân tách phụ lục lồng nhau theo chuẩn **OKF (Open Knowledge Format) Bundle**.

---

## 📌 2. GHI CHÚ (NOTES)

- **Môi trường:** Python 3.11, Chrome CDP (Port 9222), Chrome User Data Dir chuyên biệt tại `.md/data/chrome_vip_profile`.
- **Rào cản chính:** Cloudflare Security Challenge, Popup cảnh báo đăng nhập đa thiết bị ("Đồng ý"), Redirect URL sai ID.
- **Tài khoản VIP:** Username `vuvanchu119`, Password `ccba@ibst` (định cấu hình qua `.env`).
- **Quy chuẩn đóng gói:** Tuân thủ `/ccba-build-skill` và QC Gate `validate_docs.py`.

---

## 📑 3. QUYẾT ĐỊNH ĐÃ CHỐT (DECISIONS SO FAR)

1. **[Quyết định Kiến trúc Chrome Profile](../../../../packages/ccba-legal-intel/ccba_legal/crawler.py):** Sử dụng profile Chrome cố định tại `.md/data/chrome_vip_profile` để lưu trữ Session Cookie VIP vĩnh viễn, tránh việc đăng nhập lại nhiều lần gây cảnh báo đa thiết bị.
2. **[Quyết định Đóng gói OKF Bundle](../../../../.agents/skills/ccba-legal-intel/SKILL.md):** Văn bản tải về từ TVPL phải được tách tự động thành `metadata.yaml`, `concept.md` (toàn văn), `guiding_docs/` (văn bản sửa đổi/hướng dẫn) và `index.md`.

---

## 🚀 4. BIÊN GIỚI TICKET CẦN GIẢI QUYẾT (FRONTIER TICKETS)

### [Ticket 01: CDP Session & Anti-Cloudflare Lock Architecture](ticket_01_cdp_session.md) `[Research/AFK]`
- **Mục tiêu:** Thiết kế module `scripts/tvpl_session_manager.py` quản lý khởi động Chrome CDP ẩn danh với `--user-data-dir=.md/data/chrome_vip_profile`, tự động bypass Cloudflare challenge và kiểm tra trạng thái cookie VIP.
- **Blocked by:** Không.

### [Ticket 02: TVPL Download DOM Selector Engine & Fallback Parser](ticket_02_dom_selector.md) `[Research/AFK]`
- **Mục tiêu:** Xây dựng thuật toán định vị link tải về `.docx` chính xác 100% cho mọi loại VBPL trên TVPL (Luật, Nghị định, Thông tư, Quy chuẩn QCVN), loại bỏ hoàn toàn đứt đoạn link hoặc redirect nhầm ID.
- **Blocked by:** Ticket 01.

### [Ticket 03: Đóng gói Skill `tvpl-vip-crawler` bằng `/ccba-build-skill`](ticket_03_build_skill.md) `[Task/HITL]`
- **Mục tiêu:** Đóng gói toàn bộ logic vào `.agents/skills/tvpl-vip-crawler/SKILL.md`, script `scripts/tvpl_vip_crawler.py`, workflow `.agents/workflows/ccba-tvpl-vip-crawler.md` và kiểm định qua `validate_docs.py`.
- **Blocked by:** Ticket 01, Ticket 02.

---

## 🌫️ 5. CHƯA XÁC ĐỊNH RÕ (NOT YET SPECIFIED)

- **Cơ chế nạp tự động vào NotebookLM:** Tự động đẩy tệp `.docx` cào về lên Google Drive chung và đồng bộ NotebookLM ID qua `notebooklm-connector`.
- **Xử lý tài liệu có bảng biểu phức tạp (Complex Tables):** Chuyển đổi các bảng biểu dạng hình ảnh hoặc layout vỡ cột bằng `table-reconstructor`.

---

## ⛔ 6. NGOÀI PHẠM VI (OUT OF SCOPE)

- **Cào tự động các trang web trả phí khác ngoài TVPL:** Giới hạn phạm vi phiên bản v1 này chỉ dành riêng cho `thuvienphapluat.vn`.
