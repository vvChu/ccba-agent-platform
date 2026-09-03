# 🧠 CCBA Platform Knowledge Base: Session Learnings & Architectural Invariants

> **Scope:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Standard:** OKF v2.2, ADR 0016, ADR 0021, ADR 0031, ADR 0032.

---

## 1. TVPL VIP 3-Tier Download Priority & Parameter Discovery (ADR 0031)

- **Tier 1 — VIP Digital Vector Searchable PDF (`part=-100` / `#ctl00_Content_ThongTinVB_filePDFHyperLink`):**
  - **Mỏ neo Pháp lý Tối thượng Cấp 1 (Primary Anchor of Trust)**: Bản PDF số hóa toàn văn (ví dụ QCVN 02 619 trang, QCVN 06 182 trang, TT 38 1,893 trang). Chứa trọn vẹn 100% thân văn bản, toàn bộ phụ lục, bảng biểu và đồ thị.
- **Tier 2 — VIP OpenXML Word Document (`part=-1&docx=1` / `#ctl00_Content_ThongTinVB_vietnameseHyperLink_Docx`):**
  - **Nguồn Dữ Liệu Gốc Vàng (Gold Source Input)**: Nạp trực tiếp vào `docx_converter.py` để sinh ra OKF v2.2 Markdown Bundle (phân rã biểu mẫu `templates/` và bảng tra cứu `tables/`).
- **Tier 3 — Gazette Scan PDF (`part=0` / `#ctl00_Content_ThongTinVB_pdfHyperLink`):**
  - Dự phòng khi TVPL chưa xuất bản bản PDF số hóa riêng.

---

## 2. Persistent Chromium VIP Session Engine & CLI (`python -m ccba_legal login`)

- **Profile Độc Lập:** Sử dụng `~/.gemini/antigravity/chrome_vip` để lưu Cookie phiên VIP Pro lâu dài.
- **Khởi chạy 1-Click:** Lệnh `python -m ccba_legal login` tự động mở Chrome/Edge trên cổng `9222`, cho phép đăng nhập 1 lần duy nhất, tránh bị Windows DPAPI chặn khi copy file cookie.
- **WebSocket Timeout Guard:** Bổ sung `timeout=8.0s` và bắt lỗi `(WebSocketTimeoutException, WebSocketConnectionClosedException)` trong `evaluate_js` và `navigate`, chống đơ luồng khi form ASP.NET PostBack/Reload.

---

## 3. Automated Contract Tests: CLI & Documentation Parity

- **`test_cli_doc_parity.py`:** Kiểm tra tự động tính khớp nối $100\%$ giữa các lệnh trong `cli.py` (`login`, `fetch`, `batch-fetch`, `convert`, `consolidate`, `process`) và hướng dẫn trong `SKILL.md`. Ngăn ngừa triệt để lỗi lệch pha tài liệu (Documentation Drift).

---

## 4. Spoke CI Gates Verification Pipeline

Mọi văn bản trước khi nghiệm thu vào kho tri thức bắt buộc phải vượt qua tuần tự 5 cổng kiểm định không dung thứ (Zero-Tolerance):
1. `python scripts/lint_visual_parity.py` (0 lỗi layout/thoát ký tự `\- ` và `&nbsp;&nbsp;\+ `)
2. `python scripts/validate_legal_spoke.py` (0 lỗi schema, AST, bảng biểu)
3. `python scripts/test_converter_regression.py` (100% gói vượt qua kiểm thử hồi quy)
4. `python scripts/verify_all_docs_against_pdf.py` (100% PDF Verified & SHA-256 Valid)
5. `python scripts/verify_cross_links.py` (100% liên kết điều khoản và phụ lục hợp lệ)

---

## 5. Spoke `.md` Directory Hygiene & Archiving Structure (ADR 0033)

- **Cấp gốc `.\.md\`**: Chỉ chứa các file cấu hình và mỏ neo tri thức tối thượng (`workspace_context.yaml`, `codebase_architecture_analysis.md`).
- **Thư mục con chuyên biệt**:
  - `.\.md\extracted_docs\`: Lưu trữ toàn bộ file Word (`.docx`) và PDF Công báo gốc đã nạp.
  - `.\.md\knowledge\`: Lưu trữ tri thức cốt lõi (`session_learnings.md`, architectural patterns).
  - `.\.md\archive\`: Nơi lưu trữ tất cả các script thử nghiệm, kiểm toán lịch sử và khảo sát (`audits/`, `inspections/`, `legacy_harvesters/`).
  - `.\.md\backups\`: Lưu trữ các bản sao lưu config (`.bak_*`).
  - `.\.md\data\`: Lưu trữ session locks, caches và audit logs.

---

## 6. Workflow Routing: `/ccba-new-feature` là Entry Point Duy Nhất Khi Có Issue ID

- **Quy tắc:** Khi đã xác định được Issue ID cần triển khai (ví dụ từ `/ccba-ask`, `/ccba-triage`, hoặc backlog review), **luôn đề xuất** `/ccba-new-feature #<id>` làm hành động tiếp theo.
- **KHÔNG BAO GIỜ** đề xuất `/ccba-implement`, `/ccba-to-spec`, hay `/ccba-to-tickets` làm entry point — đây là các bước con bên trong luồng `/ccba-new-feature`.
- **Lý do:** `/ccba-new-feature` bao trọn 8 bước lifecycle chuẩn (Factory Model):
  1. Pre-flight check & `git pull`
  2. Dọn branch cũ đã merge
  3. Bóc tách Issue (GitHub CLI hoặc Offline Fallback)
  4. Tạo branch chuẩn `feat/issue-<id>-*`
  5. Planning Mode (Triage Fast-Path + Reuse Assessment)
  6. Factory Model hand-off (route sang `/ccba-implement`, `/boost`, hoặc `/ccba-teamwork`)
  7. Coding & Verification (Quality Gates)
  8. Walkthrough & PR

  Nhảy thẳng vào `/ccba-implement` = bỏ qua 7 bước chuẩn bị.

---

## 7. Strict Legal Currency & Real-Time Validity Guardrail (Bảo Đảm Tính Hiện Hành Tuyệt Đối)

- **Nguyên tắc cốt lõi:** Mọi thông tin trao đổi, viện dẫn văn bản quy phạm pháp luật (VBPL), số hiệu luật, nghị định, thông tư và kịch bản thuyết trình (kể cả tệp dữ liệu mẫu, mock fixtures, demo slides) **BẮT BUỘC PHẢI LÀ VĂN BẢN ĐANG CÓ HIỆU LỰC (CURRENT / IN-FORCE)**.
- **Không dung thứ dữ liệu lỗi thời:** Tuyệt đối không sử dụng văn bản đã hết hiệu lực (như NĐ 175/2024, NĐ 15/2021, NĐ 06/2021) làm căn cứ quy chuẩn áp dụng hiện tại, trừ trường hợp so sánh đối chiếu lịch sử văn bản.
- **Nguồn đối chiếu:** Luôn tra cứu và đồng bộ với Registry Pháp lý CCBA (`legal_registry.yaml`) — Cụ thể từ 01/07/2026:
  - **Luật Xây dựng 2025** (Luật số `135/2025/QH15`).
  - **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng — Thay thế NĐ 175/2024 và NĐ 15/2021).
  - **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì — Thay thế NĐ 06/2021).

---

## 39. Browser Target WebSocket CDP, Centralized TVPL DOM Selectors & Ingest Slug Standardization

- **Vấn đề Phát Hiện:**
  1. **Chromium Scope Bug khi Cấu Hình Tải File (`Browser.setDownloadBehavior`):** Lệnh `Browser.setDownloadBehavior` bị gọi trên Page Target WebSocket (`ws://127.0.0.1:9222/devtools/page/...`) thay vì Browser Target WebSocket (`/json/version`). Các phiên bản Chromium mới từ chối lệnh này ở cấp Tab khiến việc tải tệp tự động về thư mục Bundle bị vô hiệu hóa.
  2. **Trùng Lặp DOM Selectors & Lệch Pha Đăng Nhập TVPL:** TVPL cập nhật form đăng nhập sang `#usernameTextBox`, `#passwordTextBox`, `#loginButton`. Selector cũ hardcoded rải rác ở `cdp.py`, `providers.py`, `tier_downloader.py` dẫn đến rớt phiên VIP về Guest và tải nhầm link tiện ích (`/bieumau`) thành tệp rác `.dat`.
  3. **Thiếu Tùy Chọn Định Danh Slug Bundle (`--slug`) Trên CLI `ingest`:** Lệnh `ingest` tự động lấy số hiệu thông tư (ví dụ `15_2017_tt_bxd`) làm tên thư mục, trong khi đối với Quy chuẩn kỹ thuật quốc gia (`02_qcvn`) định danh chuẩn mực phải là `qcvn_09_2017_bxd`.
  4. **ASP.NET Query Filtering đối với Ký tự `/`:** Query tìm kiếm có chứa `/` (`15/2017/TT-BXD`) bị IIS chặn mã hóa `%2F`, khiến kết quả trả về rỗng và fallback fuzzy-redirect sang sai văn bản (`Nghị quyết 15/2017/NQ-HĐND`).

- **Giải Pháp Khái Quát Hóa Toàn Hệ Thống (System-Wide Generalization):**
  1. **Browser Target WebSocket CDP Client (`cdp.py`):**
     - Kết nối trực tiếp đến `http://127.0.0.1:{port}/json/version` lấy `webSocketDebuggerUrl` để gửi `Browser.setDownloadBehavior` cấp Browser, đảm bảo 100% tệp nhị phân tải về đúng thư mục chỉ định.
  2. **Centralized DOM Selectors Single Source of Truth (`selectors.py`):**
     - Đóng gói toàn bộ selectors đăng nhập, popup xác nhận đa phiên, nhãn VIP, và mẫu link tiện ích loại trừ vào `TVPLSelectors`.
     - Đồng bộ hóa toàn bộ các module `cdp.py`, `providers.py`, `session.py`, `tier_downloader.py` kế thừa từ `TVPLSelectors`.
  3. **Universal `--slug` CLI Flag & Asset Normalization (`cli.py`):**
     - Bổ sung `-s / --slug` vào `ingest_parser`. Khi có cờ `--slug`, CLI tự động đồng bộ tên thư mục bundle, tên file DOCX và PDF nguồn sang `<slug>.docx` và `<slug>.pdf`.
  4. **Query Sanitization & Turnstile Bypass (`providers.py`):**
     - Chuẩn hóa query thay thế `/`, `:`, `-` bằng dấu cách (`quote_plus`), tự động gọi `cdp.handle_cloudflare()` chờ và giải phóng Turnstile challenge.
