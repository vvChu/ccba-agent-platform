---
name: ccba-tvpl-vip-crawler
description: Kỹ năng tự động cào và đóng gói văn bản pháp luật VIP TVPL qua Deep Seam
  TVPLCrawler (tự động CookieVault & Mutex).
disable-model-invocation: true
bundle: _software
tier: kernel
user-invocable: true
command: /ccba-tvpl-vip-crawler
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- ccba-tvpl-vip-crawler
- tvpl vip crawler
- cào thư viện pháp luật
- tvpl vip
- vip crawler
---

# Kỹ Năng Cào & Đóng Gói Văn Bản VIP Thư Viện Pháp Luật (`tvpl-vip-crawler`)

Kỹ năng này điều phối quy trình thu thập, đăng nhập tài khoản VIP Thư viện Pháp luật, tự động quản lý cookie qua `CookieVault`, bảo vệ phiên làm việc bằng `TVPLSessionMutex`, vượt các rào chắn kiểm tra Cloudflare/Popups và đóng gói văn bản pháp lý thành bộ chuẩn **OKF (Open Knowledge Format) Bundle** thông qua Deep Seam **`TVPLCrawler`** ([`packages/ccba-legal-intel`](../../../packages/ccba-legal-intel)).

---

## 🛠️ Hướng Dẫn Vận Hành & Luồng Thực Thi

1. **Khởi Tạo & Quản Lý Phiên VIP (Persistent Chromium VIP Session - ADR 0031)**:
   - **Hạ tầng Trình duyệt Chuẩn:** Kế thừa trực tiếp hạ tầng CDP và Persistent Profile thống nhất từ kỹ năng [`ccba-chrome-debug`](../ccba-chrome-debug/SKILL.md).
   - **Khởi chạy nhanh (Khuyên dùng):** Mở shortcut Desktop **`Chrome (AI Debug Mode)`** hoặc chạy `Launch-Chrome-Debug.cmd` (cổng `9222`, profile `~/.gemini/antigravity-browser-profile`).
   - **Hoặc khởi chạy qua CLI:**
     ```powershell
     python -m ccba_legal login
     ```
   - Hệ thống tự động mở Chromium trên cổng `9222` với cờ bắt buộc `--remote-allow-origins=*`. Toàn bộ phiên đăng nhập được chia sẻ đồng bộ giữa lệnh CLI và subagent `/browser`.

2. **Kích hoạt Lệnh Thu Thập Văn Bản 3 Tầng (3-Tier Acquisition)**:
   - **Cách 1: Thu thập đơn lẻ tải cả DOCX và VIP Digital Vector PDF:**
     ```powershell
     python -m ccba_legal fetch "https://thuvienphapluat.vn/van-ban/..."
     ```
   - **Cách 2: Nạp tự động 1 lệnh toàn trình (Giao thức "Một Cửa `tab=7`" - ADR 0035, ADR 0036):**
     ```powershell
     python -m ccba_legal ingest "https://thuvienphapluat.vn/van-ban/..." --category 01_vbpl --upload-drive
     ```
   - **Tiêu chí hoàn thành:** Tải trọn vẹn bản Word gốc `.docx` (Gold Source) và PDF Công báo số hóa `.pdf` vào `legal_docs/<category>/<doc_slug>/sources/`.

3. **Cấu trúc Bundle Chuẩn OKF v2.4 Universal Agent-Centric (ADR 0036)**:
   - File tải về và bóc tách được lưu vào cấu trúc chuẩn:
     ```text
     legal_docs/<category>/<doc_slug>/
     ├── <doc_slug>.md          <-- Thân văn bản Markdown nguyên văn 100% (ADR 0037)
     ├── metadata.yaml          <-- RAG Metadata, quan hệ pháp lý & source_assets
     ├── clauses.json           <-- Cây điều khoản AST & severity rating
     ├── index.md               <-- Mục lục điều hướng 2D & anchor links
     ├── sources/               <-- Universal sources invariant: .docx, .pdf gốc
     ├── tables/                <-- Bảng số liệu 2D (CSV, JSON, catalog)
     ├── figures/               <-- Thẻ thị giác tính toán tham số hóa (cards/)
     ├── annexes/               <-- Phụ lục kỹ thuật quy phạm
     └── templates/             <-- Biểu mẫu hành chính nguyên tử (mau_*.md)
     ```

---

## 🔒 Cơ Chế Tự Động Trong Deep Seam (`TVPLCrawler`)

1. **Persistent Session Engine:** Profile Chromium độc lập tại `~/.gemini/antigravity/chrome_vip` bảo vệ phiên VIP Pro lâu dài.
2. **Khóa Mutex An Toàn (`TVPLSessionMutex`):** Tự động khóa và giải phóng lock file kèm nhịp Jitter Delay tránh bị khóa IP/tài khoản VIP.
3. **Multi-tier Fallback:** Tự động chuyển đổi giữa HTTP Crawler tốc độ cao và Chrome CDP Browser khi gặp Cloudflare/Anti-bot.
4. **Tri-Tier Cloud Vault (ADR 0035):** Tích hợp cờ `--upload-drive` tự động đồng bộ tài sản nhị phân lên Google Drive Vault `CCBA_Legal_Vault` và sinh Native Google Docs cho Google NotebookLM.

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế:
  - Nghị định 136/2020/NĐ-CP -> Bắt buộc sử dụng **Nghị định 105/2025/NĐ-CP**.
  - QCVN 06:2020/BXD -> Bắt buộc sử dụng **QCVN 06:2022/BXD & Sửa đổi 1:2023**.
  - Thông tư 149/2020/TT-BCA -> Bắt buộc tra cứu văn bản cập nhật mới nhất.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
