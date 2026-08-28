# ADR 0049: OKF v2.4 Universal Agent-Centric Specification & Multi-Asset Cloud Vault

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-08-27)

## 2. Bối Cảnh (Context)
Trong các phiên bản trước (OKF v2.2 và v2.3), cấu trúc Bundle tri thức pháp lý vẫn còn một số điểm bất định (non-deterministic):
1. **Vị trí file PDF không đồng nhất:** Một số văn bản lưu PDF ở thư mục gốc (`<doc>.pdf`), một số lưu trong `sources/`. Điều này làm AI Agents phải tốn token quét tìm và gây phình dung lượng kho Git khi vô tình theo dõi các file nhị phân nặng (>100MB).
2. **Lẫn lộn các loại phụ lục:** Chưa có ranh giới rạch ròi giữa bảng tra cứu 2D (`tables/`), hình vẽ tham số hóa (`figures/`), phụ lục kỹ thuật quy phạm (`annexes/`), và biểu mẫu hành chính (`templates/`), dẫn đến việc xuất hiện các thư mục rỗng.
3. **Bảng so sánh đối chiếu VBHN bị phân tán:** Bảng so sánh thay đổi của các văn bản sửa đổi bổ sung bị đặt rải rác ngoài `04_appendices/` thay vì đặt đồng vị bên trong chính bundle.
4. **Thiếu liên kết Native Google Docs:** Chưa có cơ chế đồng bộ tự động tài sản nhị phân lên Cloud Vault và tự động chuyển đổi file DOCX sang Native Google Docs phục vụ Google NotebookLM (Audio Overview & AI QA).

## 3. Quyết Định Thiết Kế (Decision)

Hệ thống nâng cấp và ban hành tiêu chuẩn **OKF v2.4 (Universal Agent-Centric Standard)** với **5 Quy Tắc Bất Biến**:

### A. Quy Tắc "Ngăn Kéo Gốc Bắt Buộc" (Mandatory Universal `sources/`)
- $100\%$ mọi Bundle tri thức bắt buộc phải có thư mục `sources/`.
- Toàn bộ file `.pdf` Công báo gốc, file `.docx`, và các tài liệu nguồn Markdown cấu thành (`_goc.md`, `sua_doi_XX.md`) bắt buộc phải nằm trong `sources/`.
- Thư mục gốc chỉ chứa giao diện Agent tinh gọn (`.md`, `metadata.yaml`, `clauses.json`, `index.md`, `qa_benchmark.json`).
- Thư mục `sources/` được `.gitignore` bao phủ các file nhị phân (`sources/*.pdf`, `sources/*.docx`) để giữ Git Spoke siêu nhẹ (<50MB).

### B. Phân Tách Rạch Ròi Bốn (04) Ngăn Kéo Dữ Liệu
Mọi thành phần phụ lục và tra cứu được phân loại chặt chẽ:
1. **`tables/`** $\rightarrow$ Dành riêng cho **Bảng số liệu tra cứu 2D** (CSV, JSON, `tables_catalog.json`).
2. **`figures/`** $\rightarrow$ Dành riêng cho **Hình vẽ & Thẻ thị giác tính toán tham số hóa** (`cards/`, `figures_catalog.yaml`).
3. **`annexes/`** $\rightarrow$ Dành riêng cho **Phụ lục kỹ thuật quy phạm** (Technical Normative Annexes - VD: Phụ lục PCCC, Tải trọng).
4. **`templates/`** $\rightarrow$ Dành riêng cho **Biểu mẫu hành chính nguyên tử** (Atomic Form Templates theo ADR 0021). Cấm tạo thư mục `templates/` rỗng nếu văn bản không có biểu mẫu.

### C. Đồng Vị Ma Trận So Sánh VBHN (In-Bundle Colocated Comparative Matrix)
- Đối với các văn bản hợp nhất (VBHN có sửa đổi bổ sung), file `bang_so_sanh_thay_doi.md` bắt buộc phải đặt trực tiếp ngay tại gốc của Bundle.
- Giúp AI Agent kiểm toán (QC Agent) đọc ngay ma trận thay đổi kỹ thuật với chi phí $0\text{ token}$ tìm kiếm.

### D. Khai Báo Đa Tài Sản Đám Mây (`source_assets` Schema — ADR 0035)
- File `metadata.yaml` và `legal_registry.yaml` bắt buộc phải có khối `source_assets`:
  ```yaml
  source_assets:
    docx:
      sha256: <hash>
      vault_path: CCBA_Legal_Vault/02_qcvn/<slug>/<file>.docx
      gdrive_file_id: <gdoc_id>
      gdrive_view_url: https://docs.google.com/document/d/<gdoc_id>/edit
      status: synced
    pdf:
      sha256: <hash>
      vault_path: CCBA_Legal_Vault/02_qcvn/<slug>/<file>.pdf
      gdrive_file_id: <pdf_id>
      gdrive_view_url: https://drive.google.com/file/d/<pdf_id>/view
      status: verified
  ```

### E. Giao Thức Thu Thập "Một Cửa `tab=7`" (Single-Door Harvesting Protocol)
- Trình cào nạp tự động `ccba-legal-intel` truy cập thẳng `tab=7` của Thư Viện Pháp Luật VIP để tải trọn gói DOCX + PDF Công báo + Biểu mẫu đính kèm trong 1 lượt mở trang duy nhất.
- Bổ sung cơ chế **Silent Auto-Verification** (tự động thông qua ngầm Cloudflare trong 5–7 giây) kết hợp `Page.bringToFront`.

## 4. Hệ Quả & Lợi Ích (Consequences)
- **Định vị tất định 100% (Deterministic Navigation):** AI Agents truy cập tài nguyên với cấu trúc đường dẫn bất biến.
- **Tiết kiệm Token & Tốc độ cao:** Giảm $80\%$ overhead gọi tool dò tìm đường dẫn.
- **Sẵn sàng cho Google NotebookLM:** Đồng bộ hóa Native Google Docs tức thì cho hệ thống Podcast & QA pháp lý đa phương thức.
- **Tuân thủ CI Tuyệt đối:** Bộ kiểm định `validate_legal_spoke.py` cưỡng chế tự động 10 Cổng kiểm tra trên 100% văn bản.
