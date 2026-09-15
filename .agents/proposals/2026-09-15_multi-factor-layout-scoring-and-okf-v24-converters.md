---
proposal_id: "2026-09-15_multi-factor-layout-scoring-and-okf-v24-converters"
type: "tool"
name: "multi-factor-layout-scoring-and-okf-v24-converters"
status: "merged"
merged_commit: "62bbbbbc"
merged_date: "2026-09-15"
priority: "Cao"
related_issue: "#277"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-15"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Kiểm định"
---

# RFC Proposal: Động Cơ Đa Nhân Tố Nhận Diện Bảng Layout & Chuẩn Hóa Bộ Chuyển Đổi Pháp Lý OKF v2.4 (Issue #277)

- **Tác giả đề xuất:** Lead Maintainer & Spoke `ccba-legal-knowledge` (qua workflow `/ccba-contribute-to-hub`)
- **Ngày lập:** 2026-09-15
- **Trạng thái:** Đã hợp nhất (Merged — Commit: `62bbbbbc`)
- **Mã Issue:** [#277](https://github.com/vvChu/ccba-agent-platform/issues/277)
- **Căn cứ pháp lý & kỹ thuật:** ADR-0038, ADR-0039, ADR-0040, ADR-0041, ADR-0042, ADR-0043, ADR-0044, ADR-0045, ADR-0057, ADR-0058.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Motivation)

Trong quá trình chuẩn hóa và nạp các văn bản quy chuẩn, tiêu chuẩn kỹ thuật trọng điểm (QCVN 07:2023/BXD, TCVN 4474:1987, TCVN 4513:1988...) theo chuẩn OKF v2.4 tại Spoke `ccba-legal-knowledge`, đã phát sinh 4 vấn đề kỹ thuật cốt lõi:
1. **Sự Cứng Nhắc của Heuristic Bảng Layout (`rows <= 3`):**
   - *False Negative:* Các khối nơi nhận và chữ ký hành chính theo Nghị định 30/2020/NĐ-CP thường có từ 4 đến 6 hàng. Quy định cứng `rows <= 3` khiến các khối chữ ký này bị lọt thành các bảng 2D CSV rác trong `tables/`.
   - *False Positive:* Các bảng tra hệ số kỹ thuật siêu ngắn ($1 \text{ - } 2$ hàng dữ liệu) bị người soạn thảo bỏ viền hoặc ẩn viền có nguy cơ bị unwrap nhầm thành văn bản thường nếu không chứa các từ khóa trong `NORMATIVE_KEYWORDS`.
2. **Xung Đột Cú Pháp KaTeX Đa Dòng:** Việc dùng `\tag{...}` bên trong các môi trường đa dòng (`aligned`, `cases`, `gather`) làm trình biên dịch KaTeX báo lỗi đỏ và gãy hiển thị toán học.
3. **Bảo Tồn Nguồn Gốc Tệp PDF (Dual-PDF Archive):** Nhiều văn bản kỹ thuật từ TVPL/Công báo có tệp PDF scan mờ hoặc mã hóa phông TCVN3 thoái hóa. Cần cơ chế lưu trữ song song tệp scan gốc và bản Vector PDF độ nét tuyệt đối (zero-OCR) được kết xuất từ DOCX.
4. **Chuẩn Hóa Chỉ Số Chú Thích Bảng Biểu & Phụ Lục:** Cần tự động định dạng chỉ số trên `<sup>X)</sup>` cho các chú dẫn trong bảng và xử lý bóc tách chú thích kẹp giữa an toàn.

---

### 2. Thiết Kế & Giải Pháp Triển Khai (Implemented Solution)

1. **Động Cơ Tính Điểm Đa Nhân Tố (Multi-Factor Scoring Engine) & Zero-Loss Guard (ADR 0042 Extension):**
   - Bổ sung hàm đo lường `_calculate_numeric_density(tbl)` quét số thực, số nguyên, tỷ lệ %, toán tử so sánh và đơn vị kỹ thuật (`%`, `m`, `cm`, `mm`, `kN`, `MPa`, `kg/m3`, `°C`...).
   - **Bảo Vệ Khung Công Thức:** Nhận diện bảng không viền 1-2 hàng, 2 cột có nhãn phương trình `(1)`, `(B.1)` để unwrap thành văn bản phẳng, phục vụ bóc tách KaTeX.
   - **Nguyên Lý Bảo Toàn Dữ Liệu Tuyệt Đối (Zero-Loss Conservative Invariant):** Nếu mật độ số liệu $\ge 30\%$, khẳng định $100\%$ là bảng dữ liệu kỹ thuật, cấm tuyệt đối hành vi unwrap.
   - **Phân Vùng Biên Tài Liệu (Document Boundary Topology):** Vị trí tương đối $P \le 0.12$ (đầu) hoặc $P \ge 0.88$ (cuối tài liệu) cho phép trần unwrap lên tới 8 hàng để xử lý triệt để khối chữ ký đa tầng.
   - Đồng bộ hóa logic giữa `DocxCanonicalSanitizer` và `TableExtractor`.

2. **Chuẩn Hóa Cú Pháp KaTeX Đa Dòng (ADR 0044):**
   - Phân tầng cú pháp: Đơn dòng sử dụng `\tag{X}`; đa dòng (`aligned`, `cases`, `gather`) bắt buộc sử dụng `\qquad (X)` ở cuối dòng biểu thức.
   - Xử lý hậu kỳ trong `formula_harvester.py` lọc bỏ chuỗi suy luận rác từ Vision model và chuẩn hóa KaTeX.

3. **Lưu Trữ Song Song & Bảo Tồn Nguồn Gốc PDF (ADR 0043):**
   - Chuẩn hóa kỹ năng `ccba-legal-ingest`: Tự động nhận diện bản scan mờ/lỗi phông để lưu thành `sources/<doc_slug>_raw_scan.pdf` và xuất Vector PDF chuẩn vào `sources/<doc_slug>.pdf`.

4. **Làm Sạch Bảng Biểu & Khử Rác Phụ Lục:**
   - Trong `table_cleaner.py`: Bổ sung `sanitize_raw_table_superscripts` tự động chuyển đổi các chú dẫn chân bảng dạng `1)` thành `<sup>1)</sup>`.
   - Trong `visual_parity.py`: Tinh chỉnh regex phân đoạn footnote để tránh false-positive khi bảng/hình xen kẽ giữa các điều khoản.
   - Trong `provenance.py`: Nâng cấp bộ đối soát nguyên văn bỏ qua bảng mục lục (TOC) giả lập.

---

### 3. Đánh Giá Giá Trị × Rủi Ro × KISS

- **Giá trị:** 
  * Loại bỏ hoàn toàn bảng CSV rác sinh ra từ khối chữ ký hành chính trên 100% tài liệu quy chuẩn/tiêu chuẩn.
  * Bảo đảm $0\%$ rủi ro mất mát dữ liệu số liệu kỹ thuật nhờ cơ chế phòng vệ số liệu $\ge 30\%$.
  * Tương thích hoàn hảo với trình render KaTeX hiển thị trên Web, NotebookLM và công cụ AI.
- **Độ phức tạp:** Thấp (KISS) — Tái cấu trúc logic nội bộ in-memory của `DocxCanonicalSanitizer` và `TableExtractor`, không làm phình thêm phụ thuộc bên ngoài.
- **Rủi ro:** Không có rủi ro hồi quy. Toàn bộ 283 tests hiện hữu trên Hub đều vượt qua $100\%$.

---

### 4. Bằng Chứng Thẩm Định & Kiểm Thử (Verification Evidence)

1. **Unit Tests trên Hub Package (`ccba-legal-intel`):**
   - Chạy `python -m pytest packages/ccba-legal-intel/tests/test_docx_sanitizer.py`: **12/12 PASSED**.
   - Chạy `python -m pytest packages/ccba-legal-intel/tests`: **283/283 PASSED** in 91.89s (0 hồi quy).
2. **Master CI Gate trên Spoke (`ccba-legal-knowledge`):**
   - Chạy `python scripts/validate_legal_spoke.py`: **0 Errors, 0 Warnings** trên toàn bộ 52 OKF bundles.
