---
name: ccba-legal-ingest
description: Autonomous legal document acquisition, OKF v2.4 conversion, VBHN consolidation, and 11-Gate CI verification workflow.
bundle: _consulting
layer: _consulting
version: 1.2.0
triggers:
- ccba-legal-ingest
- nap van ban
- thu thap van ban
- harvest legal doc
- ingest law
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
---
# Skill: CCBA Legal Ingest Workflow (`ccba-legal-ingest`)

Quy trình tự động hóa thu thập, chuyển đổi sang tiêu chuẩn **OKF v2.4 Universal Agent-Centric (ADR 0034 - ADR 0041)**, hợp nhất VBHN và kiểm định qua **15 Cổng Master CI Gate** không dung thứ cho bất kỳ Luật, Nghị định, Thông tư, QCVN hoặc TCVN mới.

---

## 🏛️ Quy Trình Chuẩn Hóa Văn Bản Mới (Universal OKF v2.4 Pipeline)

Bất kỳ khi nào tiếp nhận một văn bản mới, Agent thực hiện theo quy trình chuẩn:

```
[Bước 0: Thu thập & Xác thực] ──► [Bước 1: OKF v2.4 Convert] ──► [Bước 1.5: Đối Soát Ground Truth] ──► [Bước 2: VBHN Consolidation] ──► [Bước 3: 1-Command Master CI]
 (ingest --upload-drive)          (Zero-LLM Verbatim AST)         (Zero-Prune Invariant)             (Nếu có văn bản sửa đổi)          (validate_legal_spoke.py)
```

---

### Bước 0: Thu Thập & Xác Thực Nguồn Gốc (Giao thức "Một Cửa `tab=7`" - ADR 0035, ADR 0036)

* **Kịch bản 1 — Nạp tự động 1 lệnh toàn trình (Happy Path):**
  ```powershell
  python -m ccba_legal ingest "<tvpl_url>" --category <01_vbpl|02_qcvn|03_tcvn> --upload-drive
  ```
  *(Tự động tải DOCX Gold Source + PDF Công báo số hóa vào `sources/`, chuyển đổi sang OKF v2.4 Bundle, đồng bộ lên Google Drive Vault `CCBA_Legal_Vault` và sinh Native Google Docs cho NotebookLM)*.

* **Kịch bản 2 — Tiếp nhận thủ công / Fallback khi cào bị lỗi:**
  Nếu việc cào tự động gặp trở ngại (Cloudflare/Captcha), Agent giải quyết cục bộ bằng script CDP/thủ công để đưa đúng 2 tệp `.docx` và `.pdf` vào `legal_docs/<category>/<doc_slug>/sources/`. **Sau khi có file, BẮT BUỘC thực thi Bước 1 bằng lệnh `convert` — TUYỆT ĐỐI CẤM tự viết file Markdown bằng LLM.**

* **Kịch bản 3 — Làm mới / Thay thế file scan mờ bằng bản nét (Force Refresh):**
  Chạy lệnh tải đè bản đẹp vào `sources/` rồi chuyển sang Bước 1:
  ```powershell
  python -m ccba_legal fetch "<tvpl_url>" -o "legal_docs/<category>/<doc_slug>/sources"
  ```

---

### Bước 1: Chuyển Đổi Sang OKF v2.4 Bundle (Zero-LLM Deterministic AST - ADR 0037)

* Thực thi lệnh chuyển đổi trích xuất nguyên văn $100\%$ từ DOCX gốc:
  ```powershell
  python -m ccba_legal convert --docx-path "legal_docs/<category>/<doc_slug>/sources/<doc_slug>.docx" --target-bundle-dir "legal_docs/<category>/<doc_slug>"
  ```
* **Quy chuẩn bất biến (Core Invariants):**
  - Thân văn bản Markdown trích xuất xác định $1:1$ từ DOCX (cấm LLM rewrite).
  - Phân tách rạch ròi 4 ngăn kéo: `tables/`, `figures/`, `annexes/`, `templates/`.
  - Toàn bộ file gốc DOCX + PDF nằm trong `sources/`.
  - Tự động sinh cây điều khoản AST `clauses.json` và bộ câu hỏi `qa_benchmark.json`.

---

### Bước 1.5: Đối Soát Toàn Vẹn Số Lượng Đối Tượng (Ground Truth Reconciliation & Zero-Prune Invariant)

Trước khi chuyển sang bước kiểm định hoặc kết luận hoàn thành, Agent **bắt buộc** thực hiện:

1. **Đối soát số lượng Bảng (Table Reconciliation):**
   * Đếm tổng số bảng thực tế trong tệp DOCX gốc: `total_doc_tables = len(doc.tables)`.
   * So sánh với số lượng bảng trong `tables/csv/` và `tables_catalog.json`.
   * Nếu có sự chênh lệch: **Nghiêm cấm** Agent tự ý xóa các tệp CSV/JSON bị coi là "mồ côi" (`clean_orphan_tables.py`). Agent bắt buộc phải tìm nguyên nhân (do bảng bị ngắt trang hay parser bỏ sót) để trích xuất đầy đủ 100%.
2. **Đối soát số lượng Phụ lục (Annex Reconciliation):**
   * Đối chiếu danh mục Phụ lục trong mục lục văn bản gốc (PDF/DOCX) với số lượng tệp `.md` trong `annexes/`.
   * Tuyệt đối không để xảy ra trường hợp Phụ lục bị dồn vào thân văn bản chính.
3. **Đối soát Sơ đồ Đồ họa (Multimodal Figure Fallback):**
   * Nếu `figures/` ghi nhận 0 hình nhưng văn bản quy chuẩn có sơ đồ (như Hình H.1, Hình H.2 trong QCVN 10:2025/BCA), bắt buộc kiểm tra các trang PDF để trích xuất vector raster $\ge 300\text{ DPI}$.
4. **Tiêu chí hoàn thành (Exit Criteria):**
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

---

### Bước 3: Đăng Ký Sổ Bộ & Nghiệm Thu Master CI Gate (1-Command Automation)

1. Cập nhật `bundle_path`, `pdf_path`, `pdf_sha256`, `pdf_status: verified` và khối `source_assets` vào `legal_registry.yaml`.
2. Chạy bộ kiểm định 15 Cổng Master Spoke CI Validator:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
3. **Tiêu chuẩn nghiệm thu:** `0 Errors, 0 Warnings, 100% Visual Parity, 100% Verbatim Match (Gate 11 >= 98.0%), 100% PDF SHA-256 Match`.
