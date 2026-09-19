# Walkthrough: PR #297 — Word COM Single-Pass Form Filler Module & Form Layout Guard

## 1. Tổng Quan PR #297
- **Branch:** `feat/ooxml-form-filler-guard` $\rightarrow$ `main`
- **Tiêu đề:** `feat(ooxml): add Word COM single-pass form filler module with layout guard`
- **PR liên quan:** [PR #297](https://github.com/vvChu/ccba-agent-platform/pull/297)
- **Issue liên quan:** Closes [#296](https://github.com/vvChu/ccba-agent-platform/issues/296)
- **Commit hợp nhất:** `3f2972aa` (Squash and merge)
- **Thể chế & Kiến trúc:** ADR-0058 (Hard Completion Lock), ADR-0057 (Two-Stage Governance), KISS & Architecture Parity

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #297)

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| Review PR #297 | Toàn bộ PR #297 | Rà soát tự động GitHub Copilot | **HOÀN TOÀN SẠCH**: 0 pending review requests, 0 comments. |
| Audit Script | `audit_pr_comments.py` | Kiểm tra tự động các thay đổi và comments | **[OK]**: All Copilot reviews and comments on PR #297 are clean or resolved. |
| Maintainer Gate | PR #297 | Phê duyệt hợp nhất và kích hoạt quy trình release | **ĐÃ PHÊ DUYỆT & MERGE**: Squash merge thành công vào `main` tại commit `3f2972aa`. |

---

## 3. Các Thay Đổi Cốt Lõi (Core Deliverables)

1. **Sub-module Form Filler Mới ([`ccba_ooxml.form_filler`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-ooxml/src/ccba_ooxml/form_filler/)):**
   - **Unified Facade (`WordFormFiller`):** Giao diện thống nhất hỗ trợ auto-detect hệ điều hành (`engine="auto"`), context manager tự thu hồi tiến trình Word an toàn (`with WordFormFiller(...) as filler:`), và fluent chaining API.
   - **Engine A (`WinwordEngine` — Windows Native):**
     - Thao tác trực tiếp trên Word DOM qua COM (`win32com.client`).
     - Điền trực tiếp trên file `.doc` (Word 97-2003 nhị phân) và `.docx` gốc (In-Place Single-Pass) theo `Paragraph.Range` và `Table.Cell`, không qua chuyển đổi trung gian.
     - Tự động đóng tài liệu và tắt tiến trình Word an toàn trong khối `finally`, triệt tiêu nguy cơ rò rỉ tiến trình `WINWORD.EXE`.
   - **Engine B (`SofficeFallbackEngine` — Cross-Platform Linux/Docker):**
     - Sử dụng LibreOffice (`soffice` headless runner trong `ccba_ooxml.soffice`) kết hợp `python-docx` khi chạy trên Linux, container Docker hoặc máy chủ không có Microsoft Word.
     - Thao tác trực tiếp trên cây XML OpenXML (`w:cantSplit`).

2. **Form Layout Guard (`FormLayoutGuard`):**
   - **Anti-Row Split:** Cưỡng chế `Row.AllowBreakAcrossPages = False` (COM) hoặc chèn thẻ `<w:cantSplit/>` (DOCX XML) để bảo vệ toàn vẹn bảng biểu, ngăn hàng bị xé đôi giữa 2 trang in.
   - **Empty Row Pruning:** Tự động cắt tỉa các dòng mẫu trống thừa trong bảng biểu danh sách động.
   - **Page Break Enforcement:** Tự động chèn ngắt trang (`PageBreakBefore`) cho các phần kết luận/chữ ký theo từ khóa nhận diện.

3. **Tài Liệu & Quản Trị Hệ Thống:**
   - Sổ tay kỹ thuật: [`.agents/skills/ccba-xu-ly-van-phong/resources/form-filling.md`](file:///home/vvc/ccba/ccba-agent-platform/.agents/skills/ccba-xu-ly-van-phong/resources/form-filling.md).
   - Đăng ký triggers trong `platform-loader/catalog.yaml` và `ccba-xu-ly-van-phong/SKILL.md` (`điền form word`, `fill form doc`, `form-filler`, `layout guard`).
   - Cập nhật tài liệu kiến trúc `README.md` loại bỏ Architecture Drift.
   - Biên dịch web docs tự động (`docs/`).

4. **Kiểm Thử Tự Động & CI:**
   - Unit tests: [`test_form_filler.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-ooxml/tests/test_form_filler.py) (7/7 tests passed).
   - Package tests: `packages/ccba-ooxml/tests/` (67/67 tests passed).
   - Monorepo isolated tests: 11/11 package suites passed.
   - GitHub Actions CI: 6/6 jobs passed (Markdown lint, Python 3.10, 3.11, 3.12, Security scan, Documentation check).
