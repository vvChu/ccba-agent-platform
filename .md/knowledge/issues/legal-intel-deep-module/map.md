# 🗺️ Bản Đồ Định Hướng (Wayfinding Map): Legal Intel Deep Module Refactor

> **Tính năng:** Refactor & Nâng cấp Kỹ năng / Gói dịch vụ `ccba-legal-intel`
> **File đối chiếu:** [brainstorm_session_legal_intel_eval.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_eval.md)
> **Đặc tả Kỹ thuật:** [spec-legal-intel-deep-module.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/specs/spec-legal-intel-deep-module.md)

---

## 🎯 1. Điểm Đích (Destination)

Bóc tách và đóng gói toàn bộ quy trình cào, kiểm tra CDP, xử lý chênh lệch (Delta), phân rã phụ lục và đăng ký VBPL từ Thư viện Pháp luật (TVPL) thành một **Deep Module Seam duy nhất**: `LegalIntelPipeline` trong gói `ccba_legal.coordinator`.

**Trạng thái hoàn thành mong muốn:**
1. AI Agent và CLI scripts chỉ cần tương tác qua 1 phương thức duy nhất: `LegalIntelPipeline().process_document(url_or_id) -> LegalProcessResult`.
2. Tự động kiểm tra & khởi động Chrome debug port 9222 nếu chưa chạy, áp dụng cơ chế lắng nghe sự kiện DOM/Network ready triệt tiêu race condition.
3. Tự động ủy quyền tác vụ cào VBPL dung lượng lớn (> 100 trang) cho Subagent `ccba-research` chạy ngầm.
4. `scripts/legal_intelligence.py` và `scripts/legal_sync.py` trở thành Thin CLI Adapters (< 15 dòng code).
5. 100% test suite chạy mượt mà offline với lớp giả lập `MockChromeCDP`.

---

## 📌 2. Ghi Chú & Quy Chuẩn (Notes)

- **Bắt buộc tuân thủ Rào cản Windows MAX_PATH:** `slug` tối đa 60 ký tự (`sanitize_slug`).
- **Khóa phiên đồng thời:** Quản lý khóa `TVPLSessionMutex` bên trong `LegalIntelPipeline` để tránh lỗi đụng độ tài khoản VIP.
- **Quy chuẩn Kiểm thử An toàn (Execution Policy):**
  - Trong lúc dev/TDD: **Chỉ chạy Scoped Test trên 1 tệp tin cụ thể** (`.venv\Scripts\pytest.exe path/to/test.py`) để phản hồi tức thì < 2s và không gây timeout.
  - Khi nghiệm thu full suite: **Bắt buộc chạy ngầm dạng Bounded Async Task** qua `run_command` để không làm đứt kết nối Agent ("User cancelled agent execution").
- **Kiến trúc dữ liệu:** Duy trì chuẩn OKF Bundle lồng nhau (`.md/legal_docs/<law_slug>/guiding_docs/appendices/`).
- **Kỹ năng nạp kèm:** [`ccba-legal-intel`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-legal-intel/SKILL.md), [`code-review`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/code-review/SKILL.md), [`tdd`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/tdd/SKILL.md).

---

## 📝 3. Quyết Định Đã Chốt (Decisions so far)

- [x] **[Phê duyệt Phiên Brainstorming]** Thống nhất thực hiện đồng thời 3 nhóm cải tiến (Chrome CDP Resilience, Async Offloading/Caching, DX/Deep Seam) quy tụ bên trong `LegalIntelPipeline`. ([Chi tiết](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_eval.md))
- [x] **[Triển khai Ticket 1 - MockChromeCDP Adapter]** Đã nâng cấp `MockChromeCDP` hỗ trợ mock metadata, body_text, links, popup & login cho test suite offline 100%. ([Walkthrough Ticket 1](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/walkthrough.md))
- [x] **[Triển khai Ticket 2 - Core Seam LegalIntelPipeline]** Hoàn thành Seam sâu `LegalIntelPipeline`, tích hợp `ensure_chrome_cdp_port(9222)` và `TVPLSessionMutex`, 100% test seam pass.
- [x] **[Triển khai Ticket 3 - Async Offloading & SHA-256 Delta Caching]** Tích hợp `calculate_content_sha256()`, `is_large_legal_document()`, delta caching và ủy quyền Subagent `ccba-research` cho VBPL lớn.
- [x] **[Triển khai Ticket 4 - CLI Adapters Thin Wrappers]** Rút gọn `scripts/legal_intelligence.py` và `scripts/legal_sync.py` thành Thin Adapters ủy quyền trực tiếp cho `LegalIntelPipeline.run_cli()`.
- [x] **[Triển khai Ticket 5 - Verification & CI Gate Integration]** Đã kiểm chứng toàn bộ 13 test cases (100% pass) và đồng bộ số liệu kiến trúc thành công.
- [x] **[Thống nhất Quy chuẩn Kiểm thử Operational Policy]** Thực thi Scoped Testing đồng bộ trong TDD và Async Background Task cho Full Suite Verification.

---

## 🚩 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

Chi tiết nội dung nghiệm thu được theo dõi tại [tickets.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md):

* ✅ **[Ticket 1: Pre-factoring - MockChromeCDP Adapter](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md#ticket-1-pre-factoring-build-mockchromecdp-adapter--mock-fixtures-for-offline-testing)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Xây dựng lớp giả lập CDP và Fixtures để test suite chạy offline hoàn toàn.
* ✅ **[Ticket 2: Core Seam - Auto-Launch CDP & LegalIntelPipeline](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md#ticket-2-core-seam-implement-legalintelpipeline-deep-class-in-ccba_legalcoordinator)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Triển khai Class `LegalIntelPipeline` tích hợp `TVPLSessionMutex` và auto-detect/launch Chrome debug port 9222 + Event-driven DOM ready.
* ✅ **[Ticket 3: Performance - Async Offloading & SHA-256 Caching](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md#ticket-3-performance-integrate-subagent-ccba-research-offloading--sha-256-delta-caching)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Tự động delegate subagent `ccba-research` cho VBPL lớn và chỉ cào Delta khi SHA-256/Lược đồ có biến động.
* ✅ **[Ticket 4: CLI Adapters - Thin Wrappers for Scripts](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md#ticket-4-cli-adapters-refactor-legal_intelligencepy--legal_syncpy-into-thin-invocation-wrappers)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Rút gọn `scripts/legal_intelligence.py` và `scripts/legal_sync.py` thành wrapper mỏng (< 15 dòng).
* ✅ **[Ticket 5: Verification - End-to-End Seam Test & CI Gate](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-deep-module/tickets.md#ticket-5-verification-add-end-to-end-seam-test-suite--ci-gate-integration)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Kiểm thử toàn trình qua test seam `LegalIntelPipeline` và xác nhận 0 lỗi lặp lại.

---

## 🌫️ 5. Đã Làm Sáng Tỏ & Định Hướng Milestone 2 (Fog Clarified & Milestone 2 Backlog)

> Chi tiết kết quả thảo luận định hướng kiến trúc được ghi nhận tại biên bản **[brainstorm_session_legal_intel_milestone2.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_milestone2.md)**.

- **[Đã Giải Quyết 1 Phần] Xử lý CAPTCHA/VIP Expiry:**
  - *Hiện tại:* `MockChromeCDP` và `get_tvpl_metadata()` đã tích hợp cơ chế phát hiện form Login/Popup. Nếu cần đăng nhập thủ công, `TVPLSessionMutex` bảo vệ session và chờ người dùng đăng nhập Chrome trên port 9222.
  - *Milestone 2:* Tích hợp Webhook/Telegram Alert thông báo khi tài khoản VIP hết hạn hoặc bị chặn Cloudflare/CAPTCHA.
- **[Đã Thống Nhất Thiết Kế] Hợp nhất Văn bản Hợp nhất (Engine VBHN & AI Gateway):**
  - *Kiến trúc chốt:* AST Parser (`#D12-K2-Pa`) + Article-Scoped Chunking (`ccba-ai`) + Double-Pass `old_text_anchor` Alignment Verification.
  - *Milestone 2:* Triển khai `ASTParser`, `delta_patch.yaml` generator và `Visual Diff Exporter`.

---

## ⛔ 6. Ngoài Phạm Vi (Out of scope)

- Thay đổi sơ đồ OKF Bundle tiêu chuẩn đã quy định trong Hiến pháp CCBA.
- Cào các trang tin tức pháp lý ngoài hệ thống Thư viện Pháp luật (TVPL).

---
*Tạo bởi CCBA Wayfinder System*
