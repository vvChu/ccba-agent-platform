---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance
  checklists from Vietnamese legal documents.
bundle: _consulting
layer: _consulting
triggers:
- ccba-legal-intel
- crawl law
- diff law
- legal checklist
- thuvienphapluat
- TVPL
---
# Skill: CCBA Legal Intelligence Crawler & Packager (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent tự động thực hiện quy trình cào dữ liệu từ Thư viện Pháp luật (TVPL) qua Deep Seam **`TVPLCrawler`** ([`packages/ccba-legal-intel`](../../packages/ccba-legal-intel)), phân tích đóng gói thành cấu trúc OKF Bundle lồng nhau, phân rã phụ lục, vá liên kết tương đối và đăng ký văn bản mới vào cơ sở tri thức cục bộ.

---

## 1. Quy chuẩn & Rào cản Kỹ thuật (Technical Guardrails)

### 1.1. Rào cản Bảo mật & Quản lý Thông tin xác thực
*   **Không hardcode credentials**: Đọc thông tin tài khoản TVPL thông qua biến môi trường hệ thống hoặc file `.env` (`TVPL_USERNAME`, `TVPL_PASSWORD`). Báo lỗi nếu thiếu.
*   **Persistent Chromium VIP Profile (ADR 0031)**: Sử dụng hồ sơ trình duyệt chuyên dụng độc lập tại `~/.gemini/antigravity/chrome_vip`. Khi bắt đầu phiên làm việc hoặc khi session hết hạn, chạy lệnh tương tác:
    ```bash
    python -m ccba_legal login
    ```
    Đăng nhập tài khoản TVPL Pro 1 lần duy nhất để lưu cookie phiên bền vững cho toàn bộ các lệnh cào tự động sau đó.

### 1.2. Ma Trận Ưu Tiên Tải Dữ Liệu TVPL VIP (ADR 0031)
1. **Tier 1 — VIP Digital Vector Searchable PDF (`part=-100` / `#ctl00_Content_ThongTinVB_filePDFHyperLink`)**: Mỏ neo Pháp lý Tối thượng Cấp 1 (100% thân văn bản + toàn bộ phụ lục số hóa & bảng tra cứu).
2. **Tier 2 — VIP OpenXML Word Document (`part=-1&docx=1` / `#ctl00_Content_ThongTinVB_vietnameseHyperLink_Docx`)**: Nguồn Dữ Liệu Gốc Vàng (Gold Source Input) để nạp vào `docx_converter.py` chuyển đổi sang OKF v2.2.
3. **Tier 3 — Gazette Scan PDF (`part=0` / `#ctl00_Content_ThongTinVB_pdfHyperLink`)**: Fallback dự phòng khi văn bản chưa có bản PDF số hóa riêng.

### 1.3. Rào cản Đường dẫn Hệ thống (Windows MAX_PATH Prevention)
*   **Giới hạn độ dài Slug**: Để tránh lỗi `FileNotFoundError` khi ghi các tệp phụ lục nằm sâu trên Windows, hàm `sanitize_slug` **bắt buộc** phải giới hạn độ dài slug tối đa là **60 ký tự**.

### 1.4. Quy chuẩn Tích hợp OKF Bundle Lồng nhau (Parent-Child Flat Architecture)
*   **Luật gốc (Parent Law)**: Lưu tại `legal_docs/01_vbpl/<law_slug>/`
*   **Văn bản hướng dẫn (Guiding Decrees/Circulars)**: Lưu phẳng bên trong `legal_docs/01_vbpl/<doc_slug>/`
*   **Đăng ký Registry**: Cập nhật `bundle_path`, `pdf_path`, `pdf_sha256` và `sha256` trong `legal_registry.yaml`.

### 1.5. Đặc Tả Gói Tri Thức Hợp Nhất OKF Bundle v2.2 (ADR 0021 & ADR 0031)
Mỗi văn bản quy phạm pháp luật khi đóng gói thành công **bắt buộc** phải tuân thủ cấu trúc bundle độc lập qua Deep Seam `OKFBundlePackager`:
```text
legal_docs/<category_prefix>/<document_slug>/
├── metadata.yaml               # Metadata độc lập (SSOT cấp bundle, lưu pdf_sha256 và legal_basis)
├── <document_slug>.md          # Nội dung Markdown thuần sạch 100% (Pure Normative Body)
├── <document_slug>.pdf         # Mỏ neo PDF Công báo / PDF số hóa toàn văn (Anchor of Trust)
├── templates/                  # Thư mục biểu mẫu nguyên tử (Atomic Form Templates)
│   └── phu_luc_xx/mau_yy_...md
├── tables/                     # Thư mục chứa bảng dữ liệu tra cứu
│   ├── json/                   # JSON ma trận 2D
│   └── csv/                    # CSV UTF-8 with BOM
└── index.md                    # Mục lục điều hướng nội bộ
```
* **Quy chuẩn `metadata.yaml`:** Chứa `id`, `document_number`, `type`, `issued_date`, `effective_date`, `pdf_sha256`, `pdf_status: verified`.
* **Cơ chế Khớp nối Hub-Spoke:** Tương thích 100% hai chiều giữa Hub (`packages/ccba-legal-intel`) và Spoke (`legal_registry.yaml`).

---


## 2. Ánh xạ Đồ thị Quan hệ Lược đồ (11 nhóm quan hệ)

Khi cào trang Lược đồ (`Tab=LuocDo`), so khớp các tiêu đề mối quan hệ của TVPL:
- `amends_docs`: Văn bản bị sửa đổi bổ sung
- `replaced_docs`: Văn bản bị thay thế
- `referenced_docs`: Văn bản được dẫn chiếu
- `basis_docs`: Văn bản được căn cứ
- `guided_docs`: Văn bản được hướng dẫn
- `consolidated_docs`: Văn bản được hợp nhất
- `guiding_docs`: Văn bản hướng dẫn
- `consolidations`: Văn bản hợp nhất (VBHN)
- `amended_by_docs`: Văn bản sửa đổi bổ sung
- `replaced_by_docs`: Văn bản thay thế
- `related_docs`: Văn bản liên quan cùng nội dung

---

## 3. Hướng dẫn Vận hành Quy trình 5 Bước

1. **Khởi Tạo Phiên TVPL VIP (Persistent Session)**:
   ```bash
   python -m ccba_legal login
   ```
   Đăng nhập tài khoản VIP 1 lần duy nhất để lưu cookie phiên.

2. **Thu thập Dữ liệu qua CLI (`fetch` / `batch-fetch`)**:
   ```bash
   python -m ccba_legal fetch "<TVPL_URL_OR_ID>"
   ```
   Tự động tải về bản PDF số hóa VIP (`part=-100`) và bản Word `.docx` (`part=-1&docx=1`).

3. **Chuyển đổi sang OKF v2.2 Bundle**:
   ```bash
   python -m ccba_legal convert ".md/extracted_docs/<doc_slug>/<doc_slug>.docx" "legal_docs/<category>/<doc_slug>"
   ```

4. **Hợp nhất Văn bản Sửa đổi (VBHN Engine - nếu có)**:
   ```bash
   python -m ccba_legal consolidate -m "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" -b "legal_docs/<category>/<doc_slug>/<doc_slug>.md" -o "legal_docs/<category>/<doc_slug>"
   ```

5. **Kiểm Định Định Dạng & Liên Kết (Visual Parity & Cross-Link Linter)**:
   ```bash
   python -m ccba_legal lint "legal_docs/<category>/<doc_slug>"
   ```

6. **Trích xuất AST & Tập Dữ Liệu Đối Chuẩn (QA Benchmark)**:
   ```bash
   python -m ccba_legal process "legal_docs/<category>/<doc_slug>"
   ```

7. **Đăng ký Sổ Bộ & Kiểm Định CI Gates Spoke (Zero-Tolerance)**:
   ```powershell
   python scripts/lint_visual_parity.py
   python scripts/validate_legal_spoke.py
   python scripts/verify_all_docs_against_pdf.py
   ```
