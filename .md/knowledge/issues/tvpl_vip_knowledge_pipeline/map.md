# BẢN ĐỒ ĐỊNH HƯỚNG WAYFINDER: TVPL VIP KNOWLEDGE PIPELINE

- **Tên dự án / Kỹ năng:** `tvpl-vip-knowledge-pipeline`
- **Đường dẫn lưu trữ:** `.md/knowledge/issues/tvpl_vip_knowledge_pipeline/map.md`
- **Nguồn tài liệu đầu vào:** [`brainstorm_session_tvpl_vip_knowledge_pipeline.md`](file:///C:/Users/chuvu/.gemini/antigravity/brain/bb6b76dd-7a8d-44e9-85be-6ea70ffabf5f/brainstorm_session_tvpl_vip_knowledge_pipeline.md)

---

## 🎯 1. ĐIỂM ĐÍCH (DESTINATION)

Xây dựng hoàn chỉnh Hệ thống Pipeline Thu thập & Cấu trúc hóa Tri thức Pháp lý Tự động **`tvpl-vip-knowledge-pipeline`** cho CCBA Agent Platform. Hệ thống vận hành 100% tự động ngầm, duy trì an toàn Session VIP `vuvanchu119` qua mô hình Cookie Vault, chống bị khóa IP qua Mutex Lock Queue, bảo toàn 100% định dạng bảng biểu kỹ thuật phức tạp và tự động đóng gói bộ tri thức theo chuẩn **OKF (Open Knowledge Format) Bundle** kèm Đồ thị Mối quan hệ Pháp lý.

---

## 📌 2. GHI CHÚ (NOTES)

- **Bảo mật Session:** Credentials nạp từ `.env` (`TVPL_USERNAME=vuvanchu119`, `TVPL_PASSWORD=ccba@ibst`).
- **Kho Cookie:** Lưu trữ file mã hóa `cookies.json` tại `.md/data/chrome_vip_profile/cookies.json`.
- **Nhật ký:** Mọi sự kiện đăng nhập, gia hạn session và cào văn bản ghi vết tại `.md/data/tvpl_session_audit.log`.

---

## 📑 3. QUYẾT ĐỊNH ĐÃ CHỐT (DECISIONS SO FAR)

1. **[Quyết định P0: VIP Guard Engine](../../brainstorm_session_tvpl_vip_knowledge_pipeline.md#iii-b%E1%BA%A3ng-ph%C3%A2n-nh%C3%B3m--%C6%B0u-ti%C3%AAn-h%C3%A0nh-%C4%91%E1%BB%99ng):** Chốt mô hình Cookie Vault + VIP Health-Check Micro-probe + Auto-Relogin ngầm.
2. **[Quyết định P1: Dual-Parser Table Engine](../../brainstorm_session_tvpl_vip_knowledge_pipeline.md#iii-b%E1%BA%A3ng-ph%C3%A2n-nh%C3%B3m--%C6%B0u-ti%C3%AAn-h%C3%A0nh-%C4%91%E1%BB%99ng):** Kết hợp `python-docx` với `table-reconstructor` và AI Vision rendering snapshot.
3. **[Quyết định P2: Auto-Taxonomy Graph](../../brainstorm_session_tvpl_vip_knowledge_pipeline.md#iii-b%E1%BA%A3ng-ph%C3%A2n-nh%C3%B3m--%C6%B0u-ti%C3%AAn-h%C3%A0nh-%C4%91%E1%BB%99ng):** Tự động bóc tách Lược đồ TVPL để tạo `metadata.yaml` và cập nhật `legal_registry.yaml`.

---

## 🚀 4. BIÊN GIỚI TICKET CẦN GIẢI QUYẾT (FRONTIER TICKETS)

### [Ticket 01: Cookie Vault & VIP Health-Check Engine](ticket_01_cookie_vault.md) `[Research/AFK]`
- **Mục tiêu:** Xây dựng class `CookieVault` và Micro-probe HEAD Request kiểm tra trạng thái session, tự động gọi Chrome CDP ngầm tái tạo `cookies.json` khi hết hạn.
- **Blocked by:** Không.

### [Ticket 02: Single-Point Mutex Lock & Jitter Queue](ticket_02_mutex_queue.md) `[Research/AFK]`
- **Mục tiêu:** Nâng cấp `TVPLSessionMutex` với FIFO Queue và nhịp sinh học Jitter Delay từ 3.5s - 7.2s giữa các lượt tải `.docx`.
- **Blocked by:** Ticket 01.

### [Ticket 03: Dual-Parser Table Engine & AI Vision Snapshot](ticket_03_dual_parser.md) `[Task/HITL]`
- **Mục tiêu:** Tích hợp `python-docx` + `table-reconstructor` xử lý các bảng biểu bị vỡ ô/gộp dòng trong Phụ lục H.
- **Blocked by:** Ticket 01, Ticket 02.

### [Ticket 04: Auto-Taxonomy Graph & OKF Packager Integration](ticket_04_auto_taxonomy.md) `[Task/HITL]`
- **Mục tiêu:** Tự động bóc tách mối quan hệ pháp lý từ trang Lược đồ TVPL và cập nhật `legal_registry.yaml`.
- **Blocked by:** Ticket 01, Ticket 02, Ticket 03.

---

## 🌫️ 5. CHƯA XÁC ĐỊNH RÕ (NOT YET SPECIFIED)

- **Tự động hóa đồng bộ NotebookLM:** Tự động đẩy file `.docx` cào về lên Google Drive chung (`1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2`) để phục vụ NotebookLM RAG.

---

## ⛔ 6. NGOÀI PHẠM VI (OUT OF SCOPE)

- **Cào tự động các website trả phí khác ngoài TVPL:** Chỉ tập trung cho `thuvienphapluat.vn`.
