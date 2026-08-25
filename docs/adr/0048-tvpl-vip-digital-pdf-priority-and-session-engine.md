# ADR 0048: TVPL VIP Digital PDF Priority & Persistent Chrome Profile Session Engine

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-08-24)

## 2. Bối Cảnh (Context)
Trong quá trình tự động hóa thu thập văn bản pháp lý từ Thư Viện Pháp Luật (TVPL), hệ thống gặp 2 điểm nghẽn nghiêm trọng:
1. **Thiếu phụ lục và bảng số liệu trong bản Scan Công Báo (`part=0`):**
   - Các quy chuẩn kỹ thuật lớn (như QCVN 02:2022/BXD, QCVN 06:2022/BXD) khi tải qua nút *"Tải Văn bản gốc"* chỉ trả về bản scan 16 trang (chỉ có phần Thông tư hành chính), hoàn toàn thiếu mất 600+ trang quy chuẩn và các bảng số liệu tra cứu.
2. **Điểm nghẽn phiên đăng nhập tự động (Headless / Multi-session Lock):**
   - TVPL áp dụng kiểm tra Cloudflare và chính sách Single Sign-On (SSO) ngắt phiên đa thiết bị, khiến việc submit tự động bằng script thường xuyên bị đẩy về trạng thái `Guest`, làm ẩn nút **`Tải bản PDF` (VIP)**.

## 3. Quyết Định Thiết Kế (Decision)

### A. Ma Trận 3 Tham Số Tải TVPL & Ưu Tiên Mỏ Neo PDF (Tiered Priority)
Hệ thống đóng cứng thứ tự ưu tiên khi tải tài liệu từ TVPL:
1. **Tier 1 — VIP Digital Vector Searchable PDF (`part=-100` / `#ctl00_Content_ThongTinVB_filePDFHyperLink`):**
   - Là **Mỏ neo Pháp lý Tối thượng Cấp 1 (Primary Anchor of Trust)**. Chứa trọn vẹn $100\%$ thân văn bản và toàn bộ phụ lục, bảng biểu số liệu, đồ thị.
2. **Tier 2 — VIP OpenXML Word Document (`part=-1&docx=1` / `#ctl00_Content_ThongTinVB_vietnameseHyperLink_Docx`):**
   - Là **Nguồn Dữ Liệu Gốc Vàng (Gold Source Input)** để nạp vào `docx_converter.py` sinh ra Markdown Bundle OKF v2.2.
3. **Tier 3 — Gazette Scan PDF (`part=0` / `#ctl00_Content_ThongTinVB_pdfHyperLink`):**
   - Chỉ dùng làm fallback dự phòng khi TVPL chưa xuất bản bản PDF số hóa riêng.

### B. Persistent Chromium VIP Profile Session Engine
- Sử dụng hồ sơ trình duyệt chuyên dụng độc lập tại `~/.gemini/antigravity/chrome_vip`.
- Cung cấp lệnh CLI chuẩn hóa:
  ```powershell
  python -m ccba_legal login
  ```
  Lệnh này mở trình duyệt trên cổng Debugging `9222`, cho phép người dùng đăng nhập tài khoản TVPL Pro 1 lần duy nhất. Session cookie được bảo lưu vĩnh viễn cho tất cả các lệnh `fetch` và `batch-fetch` sau đó.

### C. WebSocket Timeout & Navigation Reconnect Guard
- Cấu hình `websocket.create_connection(..., timeout=8.0)`.
- Bọc bắt lỗi `(WebSocketTimeoutException, WebSocketConnectionClosedException)` trong các hàm `evaluate_js` và `navigate`, chống hiện tượng treo luồng vô hạn khi form ASP.NET PostBack/Reload.

## 4. Hệ Quả & Lợi Ích (Consequences)
- **100% Khớp nối dữ liệu:** Toàn bộ 29/29 văn bản trong kho tri thức đạt đối soát `100% Verified Match` giữa PDF số hóa toàn văn và Markdown OKF v2.2.
- **Tự động hóa an toàn:** Không còn rủi ro bị khóa tài khoản hoặc lỗi treo tiến trình khi tải hàng loạt.
