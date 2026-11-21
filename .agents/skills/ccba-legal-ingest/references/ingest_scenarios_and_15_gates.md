# Legal Ingest — Scenarios, Smart Fallbacks & 15-Gate Master CI Reference

Tài liệu tham chiếu Level 3 cho `ccba-legal-ingest`, lưu trữ chi tiết 4 kịch bản thu thập nguồn, các fallback chuẩn hóa DOM/AST và bảng đặc tả đầy đủ 15 Cổng Master Spoke CI.

## 1. Chi Tiết Kịch Bản Thu Thập Nguồn (Bước 0)

- **Kịch bản 1 (Auto Hub Central CLI):**
  ```bash
  python scripts/ccba_platform_cli.py ingest-legal "<tvpl_url>" --category <01_vbpl|02_qcvn|03_tcvn> [--sync-cloud]
  ```
  Chu trình tự động: Chiếm `TVPLSessionMutex` -> tải DOCX + PDF -> ghi `metadata_handoff.json` -> `spoke_cli.py ingest` -> lưu `sources/` -> cập nhật `legal_registry.yaml` (`pdf_status`) -> convert OKF v2.4 -> Scoped 15-Gate CI (`validate --bundle <slug>`, `CI=true`) -> giải phóng sandbox.
- **Kịch bản 1b (Offline Local Files):**
  ```bash
  python scripts/ccba_platform_cli.py ingest-legal "<slug_or_id>" --category <01_vbpl|02_qcvn|03_tcvn> --docx <path/to/file.docx> --pdf <path/to/file.pdf>
  ```
- **Kịch bản 2 (Acquisition Barrier — ADR-0059):** Nếu Cloudflare/Captcha chặn cào tự động, **BẮT BUỘC DỪNG LẠI** và yêu cầu người dùng cung cấp `.docx` và `.pdf` vào `legal_docs/<category>/<doc_slug>/sources/`, sau đó chạy `python -m ccba_legal convert` (cấm LLM viết Markdown thay thế).
- **Kịch bản 3 (Force Refresh bản scan mờ):**
  ```powershell
  python -m ccba_legal fetch "<tvpl_url>" -o "legal_docs/<category>/<doc_slug>/sources"
  ```
- **Kịch bản 4 (Dual-PDF Archive Protocol — ADR 0049):** Với TCVN cũ (1987–2014) bị scan mờ hoặc lỗi font TCVN3/VNI, giữ bản gốc tại `sources/<doc_slug>_raw_scan.pdf`, xuất Vector PDF qua `from ccba_ooxml import convert_to_pdf` thành `sources/<doc_slug>.pdf`, gắn `pdf_origin: docx_vector_rendered` trong `metadata.yaml` và đồng bộ cả hai lên Drive Vault.

## 2. Smart Fallbacks (Pha 3 — ADR 0044) & Reconciliation Matrix (Bước 1.5)

- **Clause-Referenced Uncaptioned Tables:** Tự động gắn nhãn bảng số liệu không có heading khi câu trước dẫn chiếu (`"theo bảng X"`).
- **Single-Annex Normalization:** Nhận diện phụ lục đơn mang tên trần `Phụ lục` với định danh `"1"`.
- **Multi-Part Table Disambiguation:** Gắn tiền tố phần (`bang_p01_01.csv`) và `part_id` trong `tables_catalog.json` cho quy chuẩn đa phần (QCVN 07:2023).
- **KaTeX Multiline Tag Hierarchy:** Dùng `\tag{X}` ở công thức đơn dòng; dùng `\qquad (X)` cuối dòng trong môi trường đa dòng (`aligned`, `cases`, `gather`).
- **Ground Truth Reconciliation (Bước 1.5):**

| Tiêu chí | Yêu cầu kiểm tra |
| :--- | :--- |
| Zero-Prune Invariant | Không xóa bảng/hình mồ côi (`clean_orphan_tables.py`) khi chưa đối soát `len(doc.tables)` gốc |
| Table Count Match | Số bảng `tables_catalog.json` khớp 100% bảng kỹ thuật gốc (sau unwrap borderless tables) |
| Annex Count Match | Số file trong `annexes/` khớp 100% phụ lục ban hành |
| Multimodal Check | Đủ 100% sơ đồ đồ họa (`>= 300 DPI`) từ PDF/DOCX |

## 3. Danh Mục 15 Cổng Master CI Gates (Bước 3)

| Cổng | Tên Kiểm Định | Tiêu Chuẩn Nghiệm Thu |
| :--- | :--- | :--- |
| Gate 1 | Registry Schema & Path Existence | `legal_registry.yaml` hợp lệ, bundle path tồn tại |
| Gate 2 | OKF Bundle Structure & Compartments | Đủ `index.md`, `metadata.yaml`, 4 ngăn kéo + `sources/` |
| Gate 3 | Attachment Integrity (`tables/`) | CSV/JSON khớp 100% `tables_catalog.json` (Sub-Gate 3.2: Multi-Part Disambiguation) |
| Gate 4 | Anchor Link Integrity | Không gãy liên kết anchor `#dieu-X`, `#khoan-Y` |
| Gate 5 | AST Jurisdiction & PDF Metadata | `clauses.json` đầy đủ cây điều khoản, SHA-256 (Sub-Gate 5.2: Dual-PDF Invariant) |
| Gate 6 | Pure Normative Body & Noise Eradication | Loại sạch văn bản rác, căn lề hành chính |
| Gate 7 | Spoke Cleanliness & Script Count | Thư mục sạch, không để script rác tại root |
| Gate 8 | Atomic Form Templates Integrity | `templates/` nguyên tử, không rỗng, đúng cấu trúc |
| Gate 9 | 100% Visual Parity | Thoát ký tự `\- ` và `&nbsp;&nbsp;+ `, tách chú thích |
| Gate 10 | ADR Living Traceability & Self-Healing | Ma trận ADR đồng bộ 100% với kiến trúc hiện hành |
| Gate 11 | DOCX-to-Markdown Verbatim Parity | Tỷ lệ khớp nguyên văn quy phạm >= 98.0% |
| Gate 12 | Multimodal Decoupled Asset & SVG/Cards | Zero stray WMF/EMF, đủ SVG/PNG >= 300 DPI và cards |
| Gate 13 | Table Knowledge Extraction & 2D Regularity | Zero ragged rows, phẳng hóa đa tầng, tách chú thích CSV |
| Gate 14 | KaTeX Math Syntax & Rendering Integrity | Công thức chuẩn KaTeX, không lỗi bôi đỏ (Sub-Gate 14.2) |
| Gate 15 | OKF Provenance & Version Attestation | Cấp tem bảo chứng OKF v2.4 Universal chuẩn phân tầng |
