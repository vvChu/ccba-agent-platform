---
description: Workflow tự động hóa toàn trình 7 bước nạp văn bản pháp lý OKF v2.2
disable-model-invocation: true
bundle: _consulting
command: /ccba-legal-ingest
triggers:
- ccba-legal-ingest
- nap van ban
- thu thap van ban
- harvest legal doc
- ingest law
---
# Workflow: Nạp Văn Bản Pháp Lý Toàn Trình 7 Bước (/ccba-legal-ingest)

> **Mô tả:** Workflow tự động hóa tuần tự 7 bước nạp văn bản pháp lý mới từ Thư Viện Pháp Luật (TVPL VIP Pro) vào Kho Tri Thức Chuẩn OKF v2.2 Native-First, bao gồm: Kiểm tra phiên VIP -> Thu thập 3 tầng -> Phân rã Biểu mẫu nguyên tử -> Hợp nhất VBHN -> Linting định dạng -> AST QA Benchmark -> Kiểm định nghiệm thu CI Gates Spoke.

---

## 🚀 Các Bước Thực Hiện Của Agent

### 1. Kiểm tra Phiên Đăng Nhập VIP (Pre-flight VIP Guard)
* Kiểm tra trạng thái đăng nhập qua `python -m ccba_legal login --check` hoặc gọi `verify_tvpl_vip_status()`.
* Nếu chưa đăng nhập, kích hoạt lệnh:
  ```powershell
  python -m ccba_legal login
  ```
  *(Hướng dẫn người dùng đăng nhập tài khoản VIP Pro trên cửa sổ trình duyệt mở ra)*.

---

### 2. Thu thập Văn bản 3 Tầng (3-Tier Acquisition)
* Thực thi lệnh tải tệp:
  ```powershell
  python -m ccba_legal fetch "<URL_HOAC_SO_HIEU>"
  ```
* Xác nhận đã tải đủ bản VIP Digital PDF (`part=-100`) và bản Word gốc (`.docx`).

---

### 3. Chuyển đổi sang Gói Tri Thức OKF v2.2 (OKF Conversion)
* Thực thi lệnh chuyển đổi:
  ```powershell
  python -m ccba_legal convert ".md/extracted_docs/<slug>/<slug>.docx" "legal_docs/<category>/<slug>"
  ```

---

### 4. Hợp nhất Văn bản Sửa đổi (VBHN Consolidation — nếu có)
* Nếu có văn bản sửa đổi bổ sung:
  ```powershell
  python -m ccba_legal consolidate `
    --manifest "legal_docs/<category>/<slug>/patch_manifest.yaml" `
    --base "legal_docs/<category>/<slug>/<slug>.md" `
    --output "legal_docs/<category>/<slug>"
  ```

---

### 5. Kiểm định Định dạng & Liên kết (OKF Linting Gate)
* Thực thi linter kiểm tra Visual Parity và liên kết tương đối:
  ```powershell
  python -m ccba_legal lint "legal_docs/<category>/<slug>"
  ```

---

### 6. Trích xuất AST & Sinh Dữ Liệu Đối Chuẩn (AST QA Benchmark)
* Trích xuất cây cú pháp điều khoản và bộ benchmark QA:
  ```powershell
  python -m ccba_legal process "legal_docs/<category>/<slug>"
  ```

---

### 7. Đăng Ký Sổ Bộ & Nghiệm Thu CI Gates (Enactment & Registry Sync)
* Ghi nhận `bundle_path`, `pdf_path`, `pdf_sha256` và `pdf_status: verified` vào `legal_registry.yaml`.
* Chạy bộ cổng kiểm thử tự động của Spoke:
  ```powershell
  # 1. Đối soát xuất xứ nguồn gốc Gate 0
  python scripts/verify_docx_against_pdf.py
  # 2. Kiểm định toàn diện 10 Cổng Master Spoke CI Validator
  python scripts/validate_legal_spoke.py
  ```
* Báo cáo kết quả nghiệm thu cho người dùng.
