---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance
  checklists from Vietnamese legal documents.
bundle: _consulting
tier: kernel
command: /ccba-legal-intel
layer: _consulting
package_path: packages/ccba-legal-intel
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 4.0
  a: 4.0
  p: 1.0
triggers:
- ccba-legal-intel
- crawl law
- diff law
- legal checklist
- thuvienphapluat
- TVPL
conforms_to:
- "ADR-0021"
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
- "ADR-0050"
---
# Skill: CCBA Legal Intelligence Crawler & Packager (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent tự động thực hiện quy trình cào dữ liệu từ Thư viện Pháp luật (TVPL) qua Deep Seam **`TVPLCrawler`** ([`packages/ccba-legal-intel`](../../../packages/ccba-legal-intel)), phân tích đóng gói thành cấu trúc OKF Bundle lồng nhau, phân rã phụ lục, vá liên kết tương đối và đăng ký văn bản mới vào cơ sở tri thức cục bộ.

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

### 1.5. Đặc Tả Gói Tri Thức Hợp Nhất OKF Bundle v2.4 Universal (ADR 0021, ADR 0034, ADR 0036, ADR 0037, ADR 0041, ADR 0042)
Mỗi văn bản quy phạm pháp luật khi đóng gói thành công **bắt buộc** phải tuân thủ cấu trúc bundle độc lập với 4 ngăn kéo và Universal `sources/`:
```text
legal_docs/<category_prefix>/<document_slug>/
├── metadata.yaml               # Metadata độc lập (SSOT cấp bundle, lưu pdf_sha256 và source_assets)
├── <document_slug>.md          # Nội dung Markdown thuần sạch 100% nguyên văn (ADR 0037)
├── clauses.json                # Cây điều khoản AST & severity rating
├── index.md                    # Mục lục điều hướng nội bộ 2D
├── sources/                    # Universal sources invariant: chứa bản gốc .docx và .pdf
│   ├── <document_slug>.docx
│   └── <document_slug>.pdf
├── templates/                  # Thư mục biểu mẫu nguyên tử (Atomic Form Templates)
│   └── phu_luc_xx/mau_yy_...md
├── tables/                     # Thư mục chứa bảng dữ liệu tra cứu 2D
│   ├── json/                   # JSON ma trận 2D
│   └── csv/                    # CSV UTF-8 with BOM
├── figures/                    # Thẻ thị giác tính toán tham số hóa (cards/)
└── annexes/                    # Phụ lục kỹ thuật quy phạm (Technical Normative Annexes)
```
* **Quy chuẩn `metadata.yaml`:** Chứa `id`, `document_number`, `type`, `issued_date`, `effective_date`, `pdf_sha256`, `pdf_status: verified`, khối `source_assets`.
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

## 3. Hướng dẫn Vận hành Quy trình Chuẩn Hóa Văn Bản

1. **Khởi Tạo Phiên TVPL VIP (Persistent Session - ADR 0031)**:
   ```bash
   python -m ccba_legal login
   ```
   Đăng nhập tài khoản VIP 1 lần duy nhất để lưu cookie phiên tại `~/.gemini/antigravity/chrome_vip`.
   * **Tiêu chí hoàn thành:** Chrome DevTools Protocol khởi chạy thành công và lưu cookie phiên xác thực hợp lệ.

2. **Nạp Tự Động 1 Lệnh Toàn Trình (Happy Path - ADR 0035)**:
   ```bash
   python -m ccba_legal ingest "<TVPL_URL>" --category <01_vbpl|02_qcvn|03_tcvn> --upload-drive
   ```
   Tự động tải bản PDF số hóa VIP (`part=-100`) và bản Word `.docx`, chuyển đổi sang OKF v2.4 Bundle, đồng bộ lên Google Drive Vault `CCBA_Legal_Vault` và Google NotebookLM.
   * **Tiêu chí hoàn thành:** Bundle OKF v2.4 được sinh tự động và đồng bộ lên Google Drive Vault cùng NotebookLM.

   *Hoặc tải riêng lẻ từng văn bản:*
   ```bash
   python -m ccba_legal fetch "<TVPL_URL>" --category <01_vbpl|02_qcvn|03_tcvn>
   ```

3. **Chuyển đổi Thủ công sang OKF v2.4 Bundle (DocxCanonicalSanitizer & Zero-LLM Deterministic AST — ADR 0042)**:
   ```bash
   python -m ccba_legal convert --docx-path "legal_docs/<category>/<doc_slug>/sources/<doc_slug>.docx" --target-bundle-dir "legal_docs/<category>/<doc_slug>"
   ```
   *(Thực thi tiền xử lý chuẩn hóa DOM in-memory qua `DocxCanonicalSanitizer`: gọt thuộc tính `w:rsid*`, gộp run phân mảnh Unicode NFC, tiêm `xml:space="preserve"`, unwrap bảng layout và thăng cấp heading trước khi bóc tách AST đa phương thức)*.
   * **Tiêu chí hoàn thành:** Tạo thành công thân văn bản `.md`, 4 ngăn kéo chuyên biệt (`tables/`, `figures/`, `annexes/`, `templates/`), `clauses.json` và `metadata.yaml`.

4. **Hợp nhất Văn bản Sửa đổi (VBHN Engine - nếu có)**:
   ```bash
   python -m ccba_legal consolidate -m "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" -b "legal_docs/<category>/<doc_slug>/sources/<doc_slug>_goc.md" -o "legal_docs/<category>/<doc_slug>"
   ```
   * **Tiêu chí hoàn thành:** Sinh tệp văn bản hợp nhất và ma trận so sánh đồng vị `bang_so_sanh_thay_doi.md`.

5. **Đồng Bộ Dữ Liệu Pháp Lý Về Spoke (1-Click Legal Sync - ADR 0050)**:
   ```bash
   python -m ccba_legal sync --pull-latest [-o legal_docs] [--doc <doc_id>]
   ```
   Tự động kéo các OKF v2.4 bundles đạt chuẩn từ kho tri thức gốc `ccba-legal-knowledge` (hoặc Cloud Legal Vault) và thực hiện Non-Destructive Additive Merge cho `legal_registry.yaml` tại Spoke.
   * **Tiêu chí hoàn thành:** Toàn bộ gói văn bản OKF v2.4 chuẩn được sao chép về Spoke và `legal_registry.yaml` được cập nhật bảo toàn.

6. **Tra Cứu & Trích Xuất Tri Thức Pháp Lý (LegalKnowledgeEngine CLI & API — ADR 0035, ADR 0050)**:
   * **Tra cứu văn bản và cảnh báo vòng đời:**
     ```bash
     python -m ccba_legal query "Luật Xây dựng"
     ```
   * **Trích xuất nguyên vẹn Điều/Khoản với Tier-Aware Semantic Slicing & Alias Parser:**
     ```bash
     python -m ccba_legal get-clause --doc Luat-Xay-dung-2025-135-2025-QH15 --clause d1
     python -m ccba_legal get-clause --doc Luat-Xay-dung-2025-135-2025-QH15 --clause d15k2
     ```
   * **Trích xuất bảng ma trận số liệu chuẩn Markdown/CSV:**
     ```bash
     python -m ccba_legal get-table --doc qcvn_06_2022_bxd --table bang_01 --format markdown
     ```
   * **Lập trình Python Facade qua `LegalKnowledgeEngine`:**
     ```python
     from ccba_legal import LegalKnowledgeEngine, query
     engine = LegalKnowledgeEngine()
     docs = engine.search("nghị định 105")
     clause = engine.get_clause("Luat-Xay-dung-2025-135-2025-QH15", "d1")
     table = engine.get_table("qcvn_06_2022_bxd", "bang_01", format="markdown")
     ```
   * **Tiêu chí hoàn thành:** Truy xuất thành công dữ liệu điều khoản/bảng biểu kèm cảnh báo pháp lý và bảo vệ hai tầng chống CWE-22 Path Traversal.

7. **Kiểm Định Master CI Gates Spoke (1-Command Automation)**:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
   * **Tiêu chí hoàn thành:** Vượt qua toàn bộ 15 Cổng Master CI Validator với 0 Errors và 0 Warnings (Gate 11 Verbatim Parity $\ge 98.0\%$, Gate 13 Table Regularity, Gate 14 KaTeX Syntax).
