---
name: ccba-legal-ingest
description: Autonomous 7-step legal document acquisition, OKF v2.2 conversion, VBHN consolidation, and zero-tolerance CI verification workflow.
bundle: _consulting
layer: _consulting
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
---
# Skill: CCBA Legal Ingest Workflow (`ccba-legal-ingest`)

Quy trình tự động hóa 7 bước thu thập, chuyển đổi sang tiêu chuẩn OKF v2.2 Native-First, hợp nhất VBHN và kiểm định CI không dung thứ cho bất kỳ Luật, Nghị định, Thông tư, QCVN hoặc TCVN mới.

---

## 🏛️ Quy Trình 7 Bước Tự Động Hóa Toàn Trình (The Universal Ingest Loop)

Khi tiếp nhận yêu cầu nạp hoặc cập nhật một văn bản pháp lý mới, Agent **bắt buộc** thực hiện tuần tự 7 bước:

```
[1. Pre-flight Check] ──► [2. 3-Tier Crawl] ──► [3. OKF v2.2 Convert] ──► [4. VBHN Consolidate]
                                                                                  │
[7. CI Gate Enactment] ◄── [6. AST Indexing] ◄── [5. OKF Linting Gate] ◄──────────┘
```

---

### Bước 1: Kiểm Tra Phiên Đăng Nhập VIP (Pre-flight VIP Guard)
* Kiểm tra phiên VIP Pro bằng `python -m ccba_legal login --check` hoặc micro-probe.
* Nếu chưa đăng nhập, kích hoạt lệnh:
  ```powershell
  python -m ccba_legal login
  ```
  *(Đăng nhập 1 lần duy nhất tại cửa sổ Chromium mở ra trên cổng 9222)*.

---

### Bước 2: Thu Thập Văn Bản 3 Tầng (3-Tier Acquisition)
* Thực thi lệnh thu thập trực tiếp qua CLI Hub:
  ```powershell
  python -m ccba_legal fetch "<url_hoac_so_hieu_van_ban>"
  ```
* **Mục tiêu đạt được:** Tự động lưu bản VIP Digital Vector PDF (`part=-100`) và bản Word gốc (`part=-1&docx=1`) vào `.md/extracted_docs/<slug>/`.

---

### Bước 3: Chuyển Đổi Sang OKF v2.2 Bundle (Universal Conversion)
* Thực thi lệnh chuyển đổi phân rã thân văn bản và biểu mẫu nguyên tử:
  ```powershell
  python -m ccba_legal convert ".md/extracted_docs/<doc_slug>/<doc_slug>.docx" "legal_docs/<category>/<doc_slug>"
  ```
* **Tiêu chuẩn cấu trúc:**
  - Thân văn bản thuần khiết $100\%$ không chứa rác layout hành chính.
  - Phụ lục biểu mẫu tách thành `templates/phu_luc_xx/mau_yy_...md`.
  - Bảng tra cứu tách vào `tables/`.

---

### Bước 4: Hợp Nhất Văn Bản Sửa Đổi (VBHN Engine — nếu có)
* Nếu văn bản có sửa đổi/bổ sung, thực thi lệnh hợp nhất AST:
  ```powershell
  python -m ccba_legal consolidate `
    --manifest "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" `
    --base "legal_docs/<category>/<doc_slug>/<doc_slug>.md" `
    --output "legal_docs/<category>/<doc_slug>"
  ```

---

### Bước 5: Kiểm Định Định Dạng & Liên Kết (OKF Linting Gate)
* Kiểm tra thoát ký tự `\- `, `&nbsp;&nbsp;\+ ` và $100\%$ tính toàn vẹn liên kết:
  ```powershell
  python -m ccba_legal lint "legal_docs/<category>/<doc_slug>"
  ```

---

### Bước 6: Trích Xuất AST & Tập Dữ Liệu Đối Chuẩn (AST & QA Benchmark)
* Trích xuất cây cú pháp và sinh tập kiểm thử QA RAG:
  ```powershell
  python -m ccba_legal process "legal_docs/<category>/<doc_slug>"
  ```

---

### Bước 7: Đăng Ký Sổ Bộ & Nghiệm Thu CI Gates (Enactment & Registry Sync)
* Cập nhật `bundle_path`, `pdf_path`, `pdf_sha256` vào `legal_registry.yaml`.
* Chạy bộ cổng kiểm thử không dung thứ của Spoke:
  ```powershell
  python scripts/lint_visual_parity.py
  python scripts/validate_legal_spoke.py
  python scripts/verify_all_docs_against_pdf.py
  python scripts/validate_adr_parity.py
  ```
* **Tiêu chuẩn hoàn thành:** `0 Errors, 0 Warnings, 100% PDF SHA-256 Match`.
