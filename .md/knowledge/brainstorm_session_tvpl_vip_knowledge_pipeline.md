# BIÊN BẢN PHIÊN BRAINSTORMING: XÂY DỰNG PIPELINE CÀO & CẤU TRÚC HÓA TRI THỨC PHÁP LÝ TVPL VIP

- **Chủ đề:** Nghiên cứu cấu trúc dữ liệu & Đề xuất giải pháp cào tri thức từ Thư viện Pháp luật (TVPL VIP).
- **Ngày thực hiện:** 26/07/2026
- **Tài khoản VIP áp dụng:** `vuvanchu119` (dấu chân bảo mật qua `.env`).
- **Mã hệ thống:** `TVPL_VIP_KNOWLEDGE_PIPELINE`

---

## 🎯 I. INTAKE & RÀO CẢN ĐẶT RA

1. **Mục tiêu:** Xây dựng Pipeline cào dữ liệu tự động, bảo đảm an toàn session VIP, giữ nguyên vẹn bảng biểu kỹ thuật phức tạp (khoang cháy, PCCC) và tự động xây dựng Đồ thị Mối quan hệ Pháp lý theo chuẩn **OKF (Open Knowledge Format) Bundle**.
2. **Thách thức cốt lõi (3 Trụ cột):**
   - Rào cản chống cào / Khóa tài khoản VIP & IP do cào hàng loạt.
   - Vỡ bảng biểu, mất định dạng dòng/cột khi chuyển đổi Markdown.
   - Phân loại và kết nối đồ thị mối quan hệ giữa các VBPL (Căn cứ, Sửa đổi, Thay thế, Hợp nhất).

---

## 💡 II. NHẬT KÝ Ý TƯỞNG PHÁT TÁN (VERBATIM LOG)

### Vòng 1: Nhận diện thách thức toàn diện
- `(user)` tất cả các thách thức trên.
- `(AI)` **Thẻ Bài Token Bucket & Rotary IP Proxy:** Kết hợp `TVPLSessionMutex` với nhịp sinh học ngẫu nhiên (jitter 3s-8s) giữa các lượt tải `.docx`. Tích hợp `api-circuit-breaker` tự động tạm ngắt 15 phút nếu gặp cảnh báo đa thiết bị để bảo vệ tuyệt đối tài khoản VIP `vuvanchu119`.
- `(AI)` **Song Luồng Parse Bảng Biểu (Dual-Parser Engine):** Khi tải tệp `.docx` gốc từ TVPL VIP, chạy `python-docx` kết hợp Kỹ năng `table-reconstructor` và AI Vision rendering snapshot để tái dựng chính xác 100% cột/dòng bị gộp.
- `(AI)` **Cây Phân Cấp Tri Thức Tự Động (Auto-Graph Taxonomy):** Tự động bóc tách các thẻ liên kết pháp lý trên TVPL (Văn bản căn cứ, Văn bản sửa đổi, Văn bản bị thay thế, Văn bản hợp nhất) để tự xây dựng `metadata.yaml` và cập nhật cây phân cấp trong `legal_registry.yaml`.

### Vòng 2: Đào sâu trụ cột Bảo vệ VIP Session
- `(user)` Bảo vệ VIP Session.
- `(AI)` **Kho Lưu Trữ Session Cookie & HTTP Injection (Cookie Vault Pattern):** Trích xuất và mã hóa `cookies.json` từ Chrome Profile (`.md/data/chrome_vip_profile`). Nạp trực tiếp bộ cookie này vào HTTP Session để tải `.docx` trực tiếp, giảm 90% tài nguyên CPU/RAM và ẩn danh hoàn toàn.
- `(AI)` **Cơ Chế Hàng Đợi Mutex Lock Đơn Điểm (`TVPLSessionMutex` FIFO Queue):** Cưỡng chế các Sub-agent cào dữ liệu xếp hàng lần lượt (FIFO Queue), ngăn chặn tuyệt đối việc gửi request song song kích hoạt ngắt session VIP.
- `(AI)` **Tự Động Nhận Diện & Xử Lý Popup "Đồng Ý" Đa Thiết Bị:** Script tự động bắt sự kiện DOM nút "Đồng ý", ghi log an toàn vào `.md/data/tvpl_session_audit.log` và tự động chờ 5 giây trước khi tiếp tục.

### Vòng 3: Cảnh báo & Tự động Gia hạn Session
- `(user)` đồng ý.
- `(AI)` **Tự Động Kiểm Tra Sức Khỏe Session (VIP Health-Check Micro-Probe):** Thực hiện truy vấn kiểm tra siêu nhẹ (HEAD Request) tới TVPL trước mỗi lượt cào để phân loại trạng thái `ACTIVE` hoặc `EXPIRED`.
- `(AI)` **Tự Động Đăng Nhập & Tái Tạo Cookie Khép Kín (Auto-Relogin Flow):** Khi phát hiện `EXPIRED`, crawler tự động mở Chrome CDP ngầm với credentials từ `.env`, tự động điền form, cập nhật file `cookies.json` mới và in cảnh báo `[VIP Guard] Session renewed successfully!`.
- `(AI)` **Nhật Ký Kiểm Toán Session VIP (`tvpl_session_audit.log`):** Ghi nhận minh bạch mọi mốc thời gian đăng nhập, vượt Cloudflare và lưu lượng cào tệp.

---

## 📊 III. BẢNG PHÂN NHÓM & ƯU TIÊN HÀNH ĐỘNG

| Trụ Cột Giải Pháp | Mô Tả Kỹ Thuật | Mức Độ Ưu Tiên |
| :--- | :--- | :--- |
| 🛡️ **VIP Guard Engine** | Cookie Vault + Mutex Lock FIFO Queue + Auto-Relogin + Audit Log | 🔴 **P0 (Bắt buộc - Ưu tiên hàng đầu)** |
| 📊 **Dual-Parser Table** | `python-docx` + `table-reconstructor` + AI Vision Snapshot | 🟡 **P1 (Quan trọng - Độ chính xác cao)** |
| 🕸️ **Auto-Taxonomy Graph**| Parse Lược đồ TVPL + Auto-generate `metadata.yaml` & `legal_registry.yaml` | 🟢 **P2 (Nâng cao - Tự động hóa trọn gói)** |

---

## 🚀 IV. KẾ HOẠCH HÀNH ĐỘNG (ACTION ITEMS)

1. **Action 1 (Nâng cấp `scripts/tvpl_vip_crawler.py`):**
   - Tích hợp module `CookieVault` và `VIPHealthCheck` vào `tvpl_vip_crawler.py`.
   - Bổ sung cơ chế ghi nhật ký tự động vào `.md/data/tvpl_session_audit.log`.

2. **Action 2 (Nâng cấp Kỹ năng `tvpl-vip-crawler`):**
   - Đơn giản hóa quy trình gọi lệnh cào: `/ccba-tvpl-vip-crawler <URL_hoặc_Tên_Văn_Bản>`.

3. **Action 3 (Thử nghiệm toàn trình trên bộ Quy chuẩn PCCC & Xây dựng):**
   - Tiến hành thử nghiệm cào tự động 100% cho bộ Thông tư 09/2023/TT-BXD (Sửa đổi 1:2023 QCVN 06:2022) và Nghị định 217/2026/NĐ-CP.
