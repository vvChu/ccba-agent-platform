# 🎫 Danh Sách Ticket Công Việc: Milestone 2 `ccba-legal-intel`

Tài liệu này quản lý chi tiết danh sách ticket và điều kiện chặn cho dự án Milestone 2 gói [`ccba-legal-intel`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel).

---

## Ticket 1: [Core] AST Parser & Patch Schema Definition

**Bị chặn bởi:** Không có `[DONE]` `[AFK]`

**Giá trị bàn giao:** Triển khai module `ASTParser` trong `ccba_legal` bóc tách Markdown chuẩn thành cấu trúc cây AST Nodes (`#D12-K2-Pa`) và định nghĩa Schema chuẩn Pydantic/YAML cho `delta_patch.yaml`.

**Tiêu chí nghiệm thu:**
- [x] Chuyển đổi tệp Markdown bất kỳ trong `.md/legal_docs/` thành chuỗi AST Nodes chuẩn mực.
- [x] Parse thành công tệp `delta_patch.yaml` mẫu bằng `yaml.safe_load()`.
- [x] Thêm unit test `test_ast_parser.py` (100% pass).

---

## Ticket 2: [AI Gateway] Delta Patch Generator via `ccba-ai`

**Bị chặn bởi:** Ticket 1 (`AST Parser & Patch Schema`) `[DONE]`

**Giá trị bàn giao:** Xây dựng module sinh patch tự động qua `ai.chat()` từ gói `ccba-ai`, áp dụng Article-Scoped Chunking và Double-Pass String Alignment Verification (`apply_patch_dry_run()`).

**Tiêu chí nghiệm thu:**
- [x] Nạp 2 đoạn văn bản (Luật gốc + Điều khoản sửa đổi) và tự động sinh tệp `delta_patch.yaml`.
- [x] Hàm `apply_patch_dry_run()` tự động trả về `[ANCHOR_MISMATCH]` nếu trích đoạn cũ không khớp chính xác với Node AST.
- [x] Thêm unit test `test_ai_patch_generator.py` (100% pass).

---

## Ticket 3: [Engine] Visual Diff Exporter & VBHN Merger Engine

**Bị chặn bởi:** Ticket 2 (`AI Gateway Delta Patch Generator`) `[DONE]`

**Giá trị bàn giao:** Hoàn thiện `VBHNMerger` thực thi 4 lệnh Patch (`REPLACE`, `INSERT_AFTER`, `ABROGATE`, `SUSPEND`) lên cây AST và xuất ra file `VBHN_{slug}.md` với định dạng Visual Diff Markdown (`+` bổ sung, `~~` bãi bỏ).

**Tiêu chí nghiệm thu:**
- [x] Tạo tệp hợp nhất `VBHN_{slug}.md` đầy đủ các chú thích trích dẫn nguồn sửa đổi.
- [x] Định dạng Visual Diff hiển thị rõ nét màu sắc/ký tự phân biệt phần thêm và phần hủy bỏ.
- [x] Thêm unit test `test_vbhn_merger.py` (100% pass).

---

## Ticket 4: [Resilience] Telegram VIP Alert & CAPTCHA Handler

**Bị chặn bởi:** Không có `[DONE]` `[AFK]`

**Giá trị bàn giao:** Tích hợp Webhook cảnh báo khẩn cấp qua Telegram Bot API khi Chrome CDP phát hiện rào chắn CAPTCHA hoặc tài khoản VIP bị hết hạn session.

**Tiêu chí nghiệm thu:**
- [x] Phát hiện các sự kiện VIP expiry / CAPTCHA form qua `crawler.py`.
- [x] Gửi thông báo trực quan (kèm screenshot/URL) đến nhóm Telegram chỉ định.
- [x] Thêm unit test `test_telegram_alert.py` (100% pass với Mock Webhook).

---

## Ticket 5: [Integration] Hybrid RAG Integration & End-to-End Test Suite

**Bị chặn bởi:** Ticket 3 (`VBHN Merger Engine`) & Ticket 4 (`Telegram VIP Alert`) `[DONE]`

**Giá trị bàn giao:** Nạp kho VBPL hợp nhất vào motor [`hybrid-rag-search`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/hybrid-rag-search/SKILL.md) (BM25 + Vector Embedding + RRF Fusion) và chạy bộ test suite toàn trình.

**Tiêu chí nghiệm thu:**
- [x] Chạy truy vấn câu hỏi pháp lý tự nhiên và trả về chính xác Điều/Khoản áp dụng.
- [x] Chạy 100% test suite Scoped Milestone 2 (11/11 passed in 5.45s) với 0 lỗi lặp lại.

---
*Tạo bởi CCBA Ticket Manager*
