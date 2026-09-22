---
name: ccba-legal-ingest
description: Autonomous legal document acquisition, OKF v2.4 conversion, VBHN consolidation, and 15-Gate CI verification workflow.
bundle: _consulting
tier: kernel
command: /ccba-legal-ingest
layer: _consulting
metadata:
  version: "1.3.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 4.0
  a: 4.0
  p: 1.0
triggers:
- ccba-legal-ingest
- nap van ban
- thu thap van ban
- harvest legal doc
- ingest law
- DocxCanonicalSanitizer
- openxml-sanitizer
- hybrid-dual-engine
- adr-0042
- chuan hoa docx
- docx sanitizer
conforms_to:
- "ADR-0016"
- "ADR-0021"
- "ADR-0029"
- "ADR-0030"
- "ADR-0031"
- "ADR-0034"
- "ADR-0035"
- "ADR-0036"
- "ADR-0037"
- "ADR-0038"
- "ADR-0039"
- "ADR-0040"
- "ADR-0041"
- "ADR-0042"
- "ADR-0043"
- "ADR-0044"
- "ADR-0049"
---

# Skill: CCBA Legal Ingest Workflow (`ccba-legal-ingest`)

Quy trình tự động hóa thu thập, chuyển đổi sang tiêu chuẩn **OKF v2.4 Universal Agent-Centric (ADR 0034 - ADR 0042)**, hợp nhất VBHN và kiểm định qua **15 Cổng Master CI Gate** không dung thứ cho bất kỳ Luật, Nghị định, Thông tư, QCVN hoặc TCVN mới.

---

## 🏛️ Quy Trình Chuẩn Hóa Văn Bản Mới (Universal OKF v2.4 Pipeline)

Bất kỳ khi nào tiếp nhận một văn bản mới, Agent thực hiện theo quy trình chuẩn:

```
[Bước 0: Thu thập & Xác thực] ──► [Bước 1: OKF v2.4 Convert] ──► [Bước 1.5: Đối Soát Ground Truth] ──► [Bước 2: VBHN Consolidation] ──► [Bước 3: Scoped Master CI]
 (ccba-platform ingest-legal)     (Zero-LLM Verbatim AST)         (Zero-Prune Invariant)             (Nếu có văn bản sửa đổi)          (validate --bundle <slug>)
```

---

### Bước 0: Thu Thập & Xác Thực Nguồn Gốc (Giao thức "Một Cửa `tab=7`" - ADR 0035, ADR 0036, ADR 0039)

* **Kịch bản 1 — Nạp tự động 1 lệnh toàn trình qua Hub Central Platform CLI (Unified Flywheel):**
  ```bash
  python scripts/ccba_platform_cli.py ingest-legal "<tvpl_url>" --category <01_vbpl|02_qcvn|03_tcvn> [--sync-cloud] [--mock]
  ```
  *(Chu trình khép kín tự động: Chiếm `TVPLSessionMutex` ➔ Tải DOCX + PDF vào sandbox tạm ➔ Ghi `metadata_handoff.json` ➔ Chuyển giao sang `spoke_cli.py ingest` ➔ Sao chép đủ 2 tệp nhị phân vào `sources/` ➔ Cập nhật `legal_registry.yaml` bảo toàn `pdf_status` ➔ Chuyển đổi OKF v2.4 Bundle ➔ Kiểm định khoanh vùng Scoped 15-Gate CI `validate --bundle <slug>` với `CI=true` ➔ Tự động giải phóng sandbox SSOT)*.

* **Kịch bản 1b — Nạp offline từ tệp có sẵn (Offline Local Files Ingestion):**
  ```bash
  python scripts/ccba_platform_cli.py ingest-legal "<slug_or_id>" --category <01_vbpl|02_qcvn|03_tcvn> --docx <path/to/file.docx> --pdf <path/to/file.pdf>
  ```

* **Kịch bản 2 — Tiếp nhận thủ công / Fallback khi cào bị lỗi:**
  Nếu việc cào tự động gặp trở ngại (Cloudflare/Captcha), Agent giải quyết cục bộ bằng script CDP/thủ công để đưa đúng 2 tệp `.docx` và `.pdf` vào `legal_docs/<category>/<doc_slug>/sources/`. **Sau khi có file, BẮT BUỘC thực thi Bước 1 bằng lệnh `convert` — TUYỆT ĐỐI CẤM tự viết file Markdown bằng LLM.**

* **Kịch bản 3 — Làm mới / Thay thế file scan mờ bằng bản nét (Force Refresh):**
  Chạy lệnh tải đè bản đẹp vào `sources/` rồi chuyển sang Bước 1:
  ```powershell
  python -m ccba_legal fetch "<tvpl_url>" -o "legal_docs/<category>/<doc_slug>/sources"
  ```

* **Kịch bản 4 — Lưu trữ kép khi PDF TVPL scan mờ / lỗi phông chữ (Dual-PDF Archive & Provenance Protocol - ADR 0049):**
  Đối với các tiêu chuẩn cũ (như TCVN 4474:1987, TCVN 4513:1988, TCVN 9362:2012, TCVN 10304:2014) mà tệp PDF từ TVPL là bản photocopy scan mờ hoặc lỗi phông mã hóa chữ TCVN3/VNI:
  - Lưu giữ nguyên vẹn bản scan gốc dưới tên `sources/<doc_slug>_raw_scan.pdf` để bảo toàn vết truy xuất nguồn gốc pháp lý.
  - Sử dụng API xuất Vector PDF đa nền tảng `from ccba_ooxml import convert_to_pdf` (tự động ưu tiên Word COM trên Windows nếu có, hoặc headless LibreOffice `soffice` trên Linux/WSL/CI) xuất Vector PDF độ nét tuyệt đối (zero-OCR) từ tệp DOCX chính quy, lưu làm `sources/<doc_slug>.pdf` và khai báo cờ `pdf_origin: docx_vector_rendered` trong `metadata.yaml`. Cả 2 tệp đều được đồng bộ lên Google Drive Vault.

* **Kịch bản 5 — Tự động giải phóng xung đột phiên TVPL & Định tuyến Tab TCVN (Session Takeover & Safe Landing):**
  - **Chiếm lại phiên TVPL Pro (Eviction):** Khi gặp hộp thoại cảnh báo đăng nhập đa phiên `#logintfrom_w`, tự động bấm `'Đồng ý'` (hoặc gọi CheckFullLogin / gửi `action=Login` tới `ajaxcontroler.aspx`) để hủy phiên từ xa và chiếm lại đặc quyền Pro cho tác vụ nạp.
  - **Định tuyến Tab Tiêu chuẩn TCVN:** Tiêu chuẩn TCVN sử dụng chuyển tab JavaScript phía client (`#aTabTaiVe` $\rightarrow$ `#tab8`). Tránh reload URL tham số `?tab=7` (gây redirect loop), thay vào đó click `#aTabTaiVe` và trích xuất liên kết endpoint trực tiếp:
    * File Word: `/documents/download.aspx?id=...&part=-1&docx=1`
    * File PDF: `/documents/download.aspx?id=...&part=0&docx=`
  - **Mô hình Safe Landing Download:** Không bao giờ trỏ download path trực tiếp vào `sources/`. Luôn tải qua thư mục đệm ngoài workspace (như `Downloads/`), quan sát đến khi tệp `stat().st_size > 0` và sạch đuôi `.crdownload`, sau đó mới dùng `shutil.move()` chuyển vào `sources/<doc_slug>.<ext>`. Quy tắc này bảo vệ tuyệt đối Gate 11 không bị crash bởi tệp rác 0-byte.
- **Tiêu chí hoàn thành:** Thu thập đầy đủ tệp DOCX gốc và PDF công báo số hóa vào thư mục `sources/`.

---

### Bước 1: Chuyển Đổi Sang OKF v2.4 Bundle & Tiền Xử Lý Chuẩn Hóa DOM (DocxCanonicalSanitizer & Zero-LLM Deterministic AST - ADR 0037, ADR 0042)

* Thực thi lệnh chuyển đổi trích xuất nguyên văn $100\%$ từ DOCX gốc qua Động cơ Lai ghép DOCX-PDF Hai Tầng kết hợp `DocxCanonicalSanitizer` tiền xử lý 100% in-memory:
  ```powershell
  python -m ccba_legal convert --docx-path "legal_docs/<category>/<doc_slug>/sources/<doc_slug>.docx" --target-bundle-dir "legal_docs/<category>/<doc_slug>"
  ```
* **Quy chuẩn bất biến (Core Invariants):**
  - **Pha 1 (In-Memory Canonical DOM Sanitization - ADR 0042):** `DocxCanonicalSanitizer` tự động gọt bỏ thuộc tính `w:rsid*`, thẻ `<w:proofErr>`, gộp các run `<w:r>` phân mảnh (Unicode NFC), tiêm `xml:space="preserve"`, thăng cấp heading và unwrap các bảng bố cục dàn trang (Borderless Layout Tables) thành văn xuôi phẳng.
  - **Pha 2 (Multimodal Verbatim AST Extraction - ADR 0037):** Thân văn bản Markdown trích xuất xác định $1:1$ từ DOCX (cấm LLM rewrite).
  - **Pha 3 (Smart Fallbacks & Multi-Part Disambiguation - ADR 0044):**
    * *Clause-Referenced Uncaptioned Tables:* Khi bảng số liệu không có heading `Bảng X` mà được dẫn chiếu trong câu trước (`blocks[i-1]` chứa `"theo bảng X"`), converter tự động gán nhãn bảng và xuất 2D CSV/JSON đầy đủ.
    * *Single-Annex Normalization:* Nhận diện phụ lục đơn lẻ mang tên trần `Phụ lục` (không kèm chữ cái/số) với định danh `"1"`, tránh dồn phụ lục vào thân chính.
    * *Multi-Part Table Disambiguation:* Đối với quy chuẩn đa phần (như QCVN 07:2023), tự động gắn tiền tố phần cho bảng (`bang_p01_01.csv`...) và đăng ký trường `part_id` trong `tables_catalog.json`.
    * *KaTeX Multiline Tag Hierarchy:* Cho phép `\tag{X}` trong khối toán đơn dòng; cưỡng chế dùng `\qquad (X)` ở cuối dòng trong các môi trường đa dòng (`aligned`, `cases`, `gather`) để triệt tiêu lỗi bôi đỏ.
  - Phân tách rạch ròi 4 ngăn kéo: `tables/`, `figures/`, `annexes/`, `templates/`.
  - Toàn bộ file gốc DOCX + PDF nằm trong `sources/`.
  - Tự động sinh cây điều khoản AST `clauses.json` và bộ câu hỏi `qa_benchmark.json`.
- **Tiêu chí hoàn thành:** Tạo thành công bundle OKF v2.4 xác định nguyên văn 100% kèm đầy đủ các ngăn kéo và cây AST clauses.json.

---

### Bước 1.5: Đối Soát Toàn Vẹn Số Lượng Đối Tượng (Ground Truth Reconciliation & Zero-Prune Invariant)

Trước khi chuyển sang bước kiểm định hoặc kết luận hoàn thành, Agent **bắt buộc** thực hiện:

1. **Đối soát số lượng Bảng (Table Reconciliation):**
   * Đếm tổng số bảng thực tế trong tệp DOCX gốc: `total_doc_tables = len(doc.tables)`.
   * Lưu ý: Các Bảng bố cục dàn trang (Borderless Layout Tables, như bảng quốc hiệu, tiêu ngữ, chữ ký, bảng khung công thức) đã được `DocxCanonicalSanitizer` unwrap thành văn bản phẳng ở Pha 1. Do đó, số lượng bảng trong `tables/csv/` và `tables_catalog.json` phản ánh chính xác số lượng bảng kỹ thuật quy phạm thực tế.
   * Nếu có sự chênh lệch bất thường: **Nghiêm cấm** Agent tự ý chạy script xóa các tệp CSV/JSON bị coi là "mồ côi" (`clean_orphan_tables.py`). Agent bắt buộc phải đối soát cấu trúc gốc để đảm bảo không bỏ sót bảng số liệu quy phạm thực tế.
2. **Đối soát số lượng Phụ lục (Annex Reconciliation):**
   * Đối chiếu danh mục Phụ lục trong mục lục văn bản gốc (PDF/DOCX) với số lượng tệp `.md` trong `annexes/`.
   * Tuyệt đối không để xảy ra trường hợp Phụ lục bị dồn vào thân văn bản chính.
3. **Đối soát Sơ đồ Đồ họa (Multimodal Figure Fallback):**
   * Nếu `figures/` ghi nhận 0 hình nhưng văn bản quy chuẩn có sơ đồ (như Hình H.1, Hình H.2 trong QCVN 10:2025/BCA), bắt buộc kiểm tra các trang PDF để trích xuất vector raster $\ge 300\text{ DPI}$.

- **Tiêu chí hoàn thành:**
   | Tiêu chí | Trạng thái | Yêu cầu kiểm tra |
   | :--- | :---: | :--- |
   | Zero-Prune Invariant | ✅/❌ | Không xóa bảng/hình mồ côi khi chưa đối soát gốc |
   | Table Count Match | ✅/❌ | Số bảng `tables_catalog.json` khớp 100% bảng kỹ thuật gốc |
   | Annex Count Match | ✅/❌ | Số file trong `annexes/` khớp 100% phụ lục ban hành |
   | Multimodal Check | ✅/❌ | Đủ 100% sơ đồ đồ họa từ PDF/DOCX |

---

### Bước 2: Hợp Nhất Văn Bản Sửa Đổi (VBHN Engine — nếu có)

* Nếu văn bản có sửa đổi/bổ sung, thực thi lệnh hợp nhất AST:
  ```powershell
  python -m ccba_legal consolidate `
    --manifest "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" `
    --base "legal_docs/<category>/<doc_slug>/sources/<doc_slug>_goc.md" `
    --output "legal_docs/<category>/<doc_slug>"
  ```
* Bắt buộc sinh ma trận so sánh đồng vị `bang_so_sanh_thay_doi.md` tại gốc bundle (ADR 0036).
- **Tiêu chí hoàn thành:** Hợp nhất thành công các sửa đổi bổ sung và sinh ma trận so sánh thay đổi bang_so_sanh_thay_doi.md.

---

### Bước 3: Đăng Ký Sổ Bộ & Nghiệm Thu Master CI Gate (1-Command Automation)

1. Cập nhật `bundle_path`, `pdf_path`, `pdf_sha256`, `pdf_status: verified` và khối `source_assets` vào `legal_registry.yaml` (hoàn toàn tự động khi dùng `spoke_cli.py ingest` hoặc `ccba-platform ingest-legal`).
2. Chạy bộ kiểm định 15 Cổng Master Spoke CI Validator:
   ```bash
   # Kiểm định khoanh vùng gói văn bản mới (Khuyến nghị):
   python scripts/validate_legal_spoke.py --bundle <slug>
   # Hoặc kiểm định toàn diện repo:
   python scripts/validate_legal_spoke.py
   ```
3. **Tiêu chuẩn nghiệm thu:** `0 Errors, 0 Warnings, 100% Visual Parity, 100% Verbatim Match (Gate 11 >= 98.0%), 100% PDF SHA-256 Match`.

- **Danh mục 15 Cổng Master CI Gates:**
   | Cổng | Tên Kiểm Định | Tiêu Chuẩn Nghiệm Thu |
   | :--- | :--- | :--- |
   | Gate 1 | Registry Schema & Path Existence | `legal_registry.yaml` hợp lệ, bundle path tồn tại |
   | Gate 2 | OKF Bundle Structure & Compartments | Đủ `index.md`, `metadata.yaml`, 4 ngăn kéo + `sources/` |
   | Gate 3 | Attachment Integrity (tables/) | CSV/JSON khớp 100% `tables_catalog.json` (Sub-Gate 3.2: Table Reference & Multi-Part Disambiguation) |
   | Gate 4 | Anchor Link Integrity | Không gãy liên kết anchor `#dieu-X`, `#khoan-Y` |
   | Gate 5 | AST Jurisdiction & PDF Metadata | `clauses.json` đầy đủ cây điều khoản, SHA-256 (Sub-Gate 5.2: Dual-PDF Archive Invariant) |
   | Gate 6 | Pure Normative Body & Noise Eradication | Loại sạch văn bản rác, căn lề hành chính |
   | Gate 7 | Spoke Cleanliness & Script Count | Thư mục sạch, không để script rác tại root |
   | Gate 8 | Atomic Form Templates Integrity | `templates/` nguyên tử, không rỗng, đúng cấu trúc |
   | Gate 9 | 100% Visual Parity | Thoát ký tự `\- ` và `&nbsp;&nbsp;+ `, tách chú thích |
   | Gate 10 | ADR Living Traceability & Self-Healing | Ma trận ADR đồng bộ 100% với kiến trúc hiện hành |
   | Gate 11 | DOCX-to-Markdown Verbatim Parity | Tỷ lệ khớp nguyên văn quy phạm $\ge 98.0\%$ |
   | Gate 12 | Multimodal Decoupled Asset & SVG/Cards | Zero stray WMF/EMF, đủ SVG/PNG $\ge 300\text{ DPI}$ và cards |
   | Gate 13 | Table Knowledge Extraction & 2D Regularity | Zero ragged rows, phẳng hóa đa tầng, tách chú thích CSV |
   | Gate 14 | KaTeX Math Syntax & Rendering Integrity | Công thức chuẩn KaTeX, không lỗi bôi đỏ (Sub-Gate 14.2: Multiline Tag Hierarchy) |
   | Gate 15 | OKF Provenance & Version Attestation | Cấp tem bảo chứng OKF v2.4 Universal chuẩn phân tầng |

- **Tiêu chí hoàn thành:** Đăng ký sổ bộ thành công và toàn bộ 15 Cổng Master Spoke CI Validator đạt trạng thái PASSED (0 Errors, 0 Warnings).

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế:
  - Nghị định 10/2021/NĐ-CP -> Bắt buộc sử dụng **Nghị định 206/2026/NĐ-CP** (Quản lý Chi phí).
  - Nghị định 15/2021/NĐ-CP & Nghị định 175/2024/NĐ-CP (đã bị thay thế) -> Bắt buộc sử dụng **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng).
  - Nghị định 06/2021/NĐ-CP (đã bị thay thế) -> Bắt buộc sử dụng **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì).
  - Nghị định 136/2020/NĐ-CP -> Bắt buộc sử dụng **Nghị định 105/2025/NĐ-CP** (PCCC & CNCH).
  - QCVN 06:2020/BXD -> Bắt buộc sử dụng **QCVN 06:2022/BXD & Sửa đổi 1:2023** (An toàn cháy cho nhà và công trình).
  - Thông tư 149/2020/TT-BCA -> Bắt buộc tra cứu văn bản cập nhật mới nhất.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
