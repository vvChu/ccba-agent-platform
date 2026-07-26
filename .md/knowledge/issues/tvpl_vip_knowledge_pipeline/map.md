# BẢN ĐỒ ĐỊNH HƯỚNG WAYFINDER: TVPL VIP KNOWLEDGE PIPELINE

- **Tên dự án / Kỹ năng:** `tvpl-vip-knowledge-pipeline`
- **Đường dẫn lưu trữ:** `.md/knowledge/issues/tvpl_vip_knowledge_pipeline/map.md`
- **Nguồn tài liệu đầu vào:** `brainstorm_session_tvpl_vip_knowledge_pipeline.md` (local brainstorm artifact; do not commit machine-absolute `file:///` paths)

---

## 🎯 1. ĐIỂM ĐÍCH (DESTINATION)

Xây dựng hoàn chỉnh Hệ thống Pipeline Thu thập & Cấu trúc hóa Tri thức Pháp lý Tự động **`tvpl-vip-knowledge-pipeline`** cho CCBA Agent Platform. Hệ thống vận hành 100% tự động ngầm, duy trì an toàn Session VIP qua mô hình Cookie Vault (username từ env), chống bị khóa IP qua Mutex Lock Queue, bảo toàn 100% định dạng bảng biểu kỹ thuật phức tạp và tự động đóng gói bộ tri thức theo chuẩn **OKF (Open Knowledge Format) Bundle** kèm Đồ thị Mối quan hệ Pháp lý.

---

## 📌 2. GHI CHÚ (NOTES)

- **Bảo mật Session:** Credentials **chỉ** nạp từ môi trường / vault — never commit real values. Required env vars (values never in git): `TVPL_USERNAME`, `TVPL_PASSWORD`.
- **Kho Cookie:** Local-only encrypted/session store at `.md/data/chrome_vip_profile/cookies.json` (gitignored; do not commit Chrome profiles).
- **Nhật ký:** Mọi sự kiện đăng nhập, gia hạn session và cào văn bản ghi vết tại `.md/data/tvpl_session_audit.log` (gitignored via `*.log`).

---

## 📑 3. QUYẾT ĐỊNH ĐÃ CHỐT (DECISIONS SO FAR)

1. **[Quyết định P0: VIP Guard Engine]:** Chốt mô hình Cookie Vault + VIP Health-Check Micro-probe + Auto-Relogin ngầm.
2. **[Quyết định P1: Dual-Parser Table Engine]:** Kết hợp `python-docx` với `table-reconstructor` và AI Vision rendering snapshot.
3. **[Quyết định P2: Auto-Taxonomy Graph]:** Tự động bóc tách Lược đồ TVPL để tạo `metadata.yaml` và cập nhật `legal_registry.yaml`.

---

## 🚀 4. BIÊN GIỚI TICKET CẦN GIẢI QUYẾT (FRONTIER TICKETS)

### Ticket 01: Cookie Vault & VIP Health-Check Engine `[Research/AFK]`
- **Mục tiêu:** Xây dựng class `CookieVault` và Micro-probe HEAD Request kiểm tra trạng thái session, tự động gọi Chrome CDP ngầm tái tạo `cookies.json` khi hết hạn.
- **Blocked by:** Không.

### Ticket 02: Single-Point Mutex Lock & Jitter Queue `[Research/AFK]`
- **Mục tiêu:** Nâng cấp `TVPLSessionMutex` với FIFO Queue và nhịp sinh học Jitter Delay từ 3.5s - 7.2s giữa các lượt tải `.docx`.
- **Blocked by:** Ticket 01.

### Ticket 03: Dual-Parser Table Engine & AI Vision Snapshot `[Task/HITL]`
- **Mục tiêu:** Tích hợp `python-docx` + `table-reconstructor` xử lý các bảng biểu bị vỡ ô/gộp dòng trong Phụ lục H.
- **Blocked by:** Ticket 01, Ticket 02.

### Ticket 04: Auto-Taxonomy Graph & OKF Packager Integration `[Task/HITL]`
- **Mục tiêu:** Tự động bóc tách mối quan hệ pháp lý từ trang Lược đồ TVPL và cập nhật `legal_registry.yaml`.
- **Blocked by:** Ticket 01, Ticket 02, Ticket 03.

---

## 🌫️ 5. CHƯA XÁC ĐỊNH RÕ (NOT YET SPECIFIED)

- **Tự động hóa đồng bộ NotebookLM:** Tự động đẩy file `.docx` cào về lên Google Drive chung (`<DRIVE_FOLDER_ID>`) để phục vụ NotebookLM RAG. Configure the folder id via env / secrets — do not hardcode Drive IDs in docs.

---

## ⛔ 6. NGOÀI PHẠM VI (OUT OF SCOPE)

- **Cào tự động các website trả phí khác ngoài TVPL:** Chỉ tập trung cho `thuvienphapluat.vn`.
