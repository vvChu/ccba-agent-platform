# 🗺️ Bản Đồ Wayfinder: Milestone 2 `ccba-legal-intel` (Engine VBHN & AI Gateway)

---

## 🎯 1. Điểm Đích (Destination)

Xây dựng thành công gói tính năng **Milestone 2** cho gói dịch vụ [`ccba-legal-intel`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel), bao gồm:
1. **Engine Hợp Nhất Văn Bản Pháp Luật (VBHN Merger Engine):** Phân rã cây AST (`ASTParser`), tự động sinh tệp `delta_patch.yaml` qua AI Gateway (`ccba-ai`), và xuất bản file `VBHN_{slug}.md` kèm Visual Diff Markdown.
2. **Kênh Cảnh Báo Telegram VIP / CAPTCHA:** Tự động phát hiện form Login/CAPTCHA qua Chrome CDP và gửi Webhook Telegram Alert.
3. **Tích Hợp Tra Cứu Hybrid RAG:** Nạp kho dữ liệu VBPL đã cào/hợp nhất vào motor [`hybrid-rag-search`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/hybrid-rag-search/SKILL.md) để tra cứu điều khoản ngữ nghĩa siêu tốc.

---

## 📌 2. Ghi Chú (Notes)

- **Nguyên tắc KISS:** `ASTParser` viết bằng Python thuần (~40-50 dòng), bóc tách từ Markdown chuẩn hóa của CCBA (`# Phần`, `## Chương`, `### Điều`, `- Khoản`, `a) Điểm`).
- **An toàn 0% Áo Giác:** Mọi thao tác Patch đều qua vòng 2 kiểm chứng `old_text_anchor` bằng Python thuần trước khi ghi file.
- **Tài liệu tham chiếu:** [`brainstorm_session_legal_intel_milestone2.md`](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_milestone2.md)

---

## 📝 3. Quyết Định Đã Chốt (Decisions so far)

- [x] **[Thống nhất Kiến trúc Milestone 2]** Chốt 4 nhóm tính năng trong phiên Brainstorming: AST Parser + AI Gateway Delta Generator + Telegram VIP Alert + Hybrid RAG Integration. ([Chi tiết](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/brainstorm_session_legal_intel_milestone2.md))
- [x] **[Triển khai Ticket 1 - Core AST Parser & Patch Schema]** Hoàn thành module `ccba_legal.ast_parser`, hỗ trợ bóc tách cây AST Nodes (`#D12-K2-Pa`) và định nghĩa Schema `delta_patch.yaml`. ([Walkthrough Ticket 1](file:///C:/Users/chuvu/.gemini/antigravity/brain/0c0a9304-cfbb-4fa3-9c81-3e11441ace97/walkthrough.md))
- [x] **[Triển khai Ticket 2 - AI Gateway Delta Patch Generator]** Hoàn thành module `DeltaPatchGenerator`, tích hợp AI Gateway `ccba-ai` và vòng tự đối soát chuỗi `apply_patch_dry_run()`.
- [x] **[Triển khai Ticket 3 - Visual Diff Exporter & VBHN Merger Engine]** Hoàn thành module `VBHNMerger`, thực thi 4 thao tác Patch (`REPLACE`, `INSERT_AFTER`, `ABROGATE`, `SUSPEND`) và xuất tệp `VBHN_{slug}.md` kèm Visual Diff.
- [x] **[Triển khai Ticket 4 - Telegram VIP Alert & CAPTCHA Handler]** Hoàn thành module `TelegramAlertHandler`, tự động phát hiện rào chắn Đăng nhập/CAPTCHA và bắn Webhook khẩn cấp về Telegram.
- [x] **[Triển khai Ticket 5 - Hybrid RAG Integration & End-to-End Test Suite]** Hoàn thành `LegalHybridRAG`, nạp kho dữ liệu VBHN và kiểm chứng 11/11 Scoped unit tests (100% pass in 6.09s).
- [x] **[Giải Quyết Nguyên Nhân "User Cancelled Agent Execution"]** Thống nhất chính sách Scoped Testing cho lượt TDD đồng bộ và Bounded Async Tasks cho Full Suite Verification để triệt hạ 100% rủi ro Command Timeout.

---

## 🚩 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

Chi tiết nội dung nghiệm thu được theo dõi tại [tickets.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md):

* ✅ **[Ticket 1: Core AST Parser & Patch Schema](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md#ticket-1-core-ast-parser--patch-schema-definition)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Triển khai `ASTParser` chuyển Markdown thành cây AST Nodes (`#D12-K2-Pa`) và định nghĩa Schema `delta_patch.yaml`.
* ✅ **[Ticket 2: AI Gateway Delta Patch Generator](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md#ticket-2-ai-gateway-delta-patch-generator)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Xây dựng module sinh patch qua `ai.chat()` với Article-Scoped Chunking và Double-Pass Alignment Verification.
* ✅ **[Ticket 3: Visual Diff Exporter & VBHN Merger Engine](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md#ticket-3-visual-diff-exporter--vbhn-merger-engine)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Áp dụng patch lên cây AST và xuất file `VBHN_{slug}.md` kèm Visual Diff Markdown (`+` bổ sung, `~~` bãi bỏ).
* ✅ **[Ticket 4: Telegram VIP Alert & CAPTCHA Handler](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md#ticket-4-telegram-vip-alert--captcha-handler)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Phát hiện rào chắn CAPTCHA/VIP Expiry và gửi Webhook Telegram khẩn cấp.
* ✅ **[Ticket 5: Hybrid RAG Integration & End-to-End Test Suite](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-milestone2/tickets.md#ticket-5-hybrid-rag-integration--end-to-end-test-suite)** `[DONE]` `[AFK]`
  * *Mục tiêu:* Nạp kho VBPL hợp nhất vào `hybrid-rag-search` và viết unit tests kiểm chứng 100% pass.

---

## 🌫️ 5. Chưa Xác Định Rõ / Sương Mù Chiến Trận (Not yet specified)

- Không còn sương mù chiến trận cho Milestone 2.

---

## ⛔ 6. Ngoài Phạm Vi (Out of scope)

- Thay đổi sơ đồ OKF Bundle tiêu chuẩn.
- Cào tin tức pháp lý ngoài Thư viện Pháp luật (TVPL).

---
*Tạo bởi CCBA Wayfinder System*
