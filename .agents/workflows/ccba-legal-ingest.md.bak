---
description: Workflow tự động hóa toàn trình nạp văn bản pháp lý OKF v2.4 Universal Agent-Centric
disable-model-invocation: true
bundle: _consulting
command: /ccba-legal-ingest
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
---
# Workflow: Nạp Văn Bản Pháp Lý Toàn Trình (/ccba-legal-ingest)

> **Mô tả:** Workflow tự động hóa tuần tự quy trình nạp văn bản pháp lý mới từ Thư Viện Pháp Luật (TVPL VIP Pro) vào Kho Tri Thức Chuẩn **OKF v2.4 Universal Agent-Centric (ADR 0034 – ADR 0037)**, bao gồm: Thu thập 3 tầng (Google Drive Vault) -> Trích xuất nguyên văn DOCX AST 100% -> Hợp nhất VBHN -> Nghiệm thu Master CI 11 Gates Spoke.

---

## 🚀 Các Bước Thực Hiện Của Agent

```
[Bước 0: Thu thập & Xác thực] ──► [Bước 1: OKF v2.4 Convert] ──► [Bước 2: VBHN Consolidation] ──► [Bước 3: 1-Command Master CI]
 (ingest --upload-drive)          (Zero-LLM Verbatim AST)         (Nếu có văn bản sửa đổi)          (validate_legal_spoke.py)
```

---

### Bước 0: Thu Thập & Xác Thực Nguồn Gốc (Giao thức "Một Cửa `tab=7`" - ADR 0035, ADR 0036)

* **Kịch bản 1 — Nạp tự động 1 lệnh toàn trình (Happy Path):**
  ```powershell
  python -m ccba_legal ingest "<URL_HOAC_SO_HIEU>" --category <01_vbpl|02_qcvn|03_tcvn> --upload-drive
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
2. Chạy bộ kiểm định 11 Cổng Master Spoke CI Validator:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
3. **Tiêu chuẩn nghiệm thu:** `0 Errors, 0 Warnings, 100% Visual Parity, 100% Verbatim Match (Gate 11 >= 98.0%), 100% PDF SHA-256 Match`.
