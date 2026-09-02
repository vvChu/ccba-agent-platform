---
proposal_id: "2026-09-02_legal-intel-table-figure-schematic-hardening"
type: "tool"
name: "legal-intel-table-figure-schematic-hardening"
status: "merged"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-02"
merged_commit: "7f8d8618b7e3825e26a81ba8eeecea8fa3c6d88d"
merged_date: "2026-09-02"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp điển"
---

# Proposal: Technical Table & Figure Hardening, In-Cell Schematics, and KaTeX Normalization

## 1. Tóm Tắt & Bối Cảnh Thực Tế (Context & Pain Points)
Trong quá trình số hóa các tiêu chuẩn kỹ thuật phức tạp (TCVN 2737:2023, TCVN 5574:2018, QCVN 02:2022/BXD, QCVN 06:2022/BXD) tại Spoke `ccba-legal-knowledge`:
1. **Sơ đồ nhúng trong ô bảng (In-Cell Schematics):** Các bảng quy chuẩn (như Bảng F.12, F.14, F.15 TCVN 2737) chứa sơ đồ hình học, tiết diện thanh tháp/giàn nhúng trực tiếp trong ô bảng không có text, dẫn đến hiện tượng ô trống hoặc mất dữ liệu trực quan khi chuyển sang Markdown.
2. **Co cụm ô gộp đa tầng (Hierarchical Merged Headers):** Các bảng có tiêu đề gộp ngang (như Bảng F.8, G.3, G.5) bị cơ chế khử trùng lặp cũ ép thành ít cột hơn, gây rơi rụng các cột dữ liệu quan trọng cuối bảng.
3. **Rơi rụng chú dẫn và chú thích kẹp giữa (Sandwiched Notes & Legends):** Các đoạn `CHÚ DẪN 1, 2` và `CHÚ THÍCH` nằm giữa hình ảnh và tiêu đề hình bị rơi rụng hoặc sai lệch trật tự hiển thị.
4. **Thoái hóa danh sách sau dấu hai chấm (Parser State Machine Regression):** Các mục quy phạm phân nhánh sau câu dẫn kết thúc bằng `:` bị bộ phân tích rơi state về đoạn văn phẳng, làm mất dấu gạch đầu dòng `\- ` và KaTeX notation.

---

## 2. Giải Pháp Triển Khai Trên Hub (Implementation Details)
Đã hoàn thiện và tôi luyện các module cốt lõi trong package [`packages/ccba-legal-intel`](../../packages/ccba-legal-intel):
1. **Bộ Phân Giải Tiêu Đề Đa Tầng (`resolve_hierarchical_headers`):**
   - Tích hợp trong [`table_handler.py`](../../packages/ccba-legal-intel/src/ccba_legal/converters/standard/handlers/table_handler.py) và [`table_extractor.py`](../../packages/ccba-legal-intel/src/ccba_legal/converters/table_extractor.py).
   - Bảo toàn $100\%$ số cột lưới vật lý và tự động ghép nối tiêu đề cha - con (`Parent — Child`).
2. **Quét và Bảo Tồn Hình Ảnh Nhúng Ô (`scan_and_prune_orphan_figures`):**
   - Bổ sung nhận diện thẻ HTML `<img src="...">` trong các bảng biểu Markdown để tránh quét nhầm thành ảnh mồ côi (Zero Orphaned Figures Policy).
3. **Chuẩn Hóa KaTeX Tiêu Đề Hình & Bảng (`normalize_katex_in_title`):**
   - Tự động chuyển đổi các thẻ HTML `<sub>` sang cú pháp KaTeX toán học chuẩn mực (`$c_e$`, `$c_x$`, `$c_\beta$`, `$k_\lambda$`, `$z_0$`).
4. **Bảo Tồn Thứ Tự Chuẩn Tắc Cho Khối Hình (ADR 0039):**
   - Cưỡng chế trật tự chuẩn: `Anchor -> Image Block -> CHÚ DẪN -> CHÚ THÍCH -> Figure Title`.
5. **Khôi Phục State Machine Danh Sách Quy Phạm:**
   - Bảo toàn $100\%$ các gạch đầu dòng `\- ` cho các đoạn phân nhánh sau dấu hai chấm.

---

## 3. Kiểm Thử & Nghiệm Thu (Verification & QA)
- **Unit Tests Hub:** Bổ sung [`tests/test_table_figure_hardening.py`](../../packages/ccba-legal-intel/tests/test_table_figure_hardening.py) với 5/5 unit tests pass $100\%$.
- **Toàn Bộ Test Suite Hub:** 187/187 tests pass $100\%$.
- **Spoke Master CI Gate:** Vượt qua $11/11$ Master CI Gates trên toàn bộ $37$ văn bản tại `ccba-legal-knowledge` ($0$ Errors, $0$ Critical Warnings).
- **Linter & Code Hygiene:** Đạt tiêu chuẩn ruff format & check.
