# CCBA Internet Knowledge Research & Provenance Protocol

> **Tài liệu Quy chuẩn Tra cứu Tri thức & Xác thực Xuất xứ Trực tuyến (Layer 2)**  
> **Tiêu chuẩn Tuân thủ:** ADR-0058 (Deterministic Hard Completion Lock), ADR-0059 (Legal Verbatim Grounding & Cryptographic Provenance Stamping).  
> **Phạm vi:** Toàn bộ AI Agents, Pipelines và Scripts thực thi tác vụ nghiên cứu, thu thập và tra cứu tài liệu từ Internet.

---

## 1. Nguyên Tắc Cốt Lõi (Core Invariants)

Theo quy định tại **HUB-ADR-0059**, mọi tri thức và văn bản thu thập từ Internet (văn bản quy phạm pháp luật, tiêu chuẩn kỹ thuật xây dựng, tài liệu thẩm định) đều phải tuân thủ nghiêm ngặt 3 nguyên tắc bất biến:

1. **Bất biến Không Bịa đặt (Zero-Hallucination & Strict Verbatim Grounding):**  
   Nghiêm cấm Agent tự suy diễn, biên soạn tóm lược giả định hoặc tạo mock text thay thế cho tài liệu gốc. Mọi nội dung trích dẫn phải đối soát nguyên văn 100% với tệp tài liệu được ban hành chính thức.

2. **Chính sách Thu thập Bắt buộc Trước tiên (Mandatory Acquisition-First Policy):**  
   Khi cần dữ liệu từ văn bản chưa có bản số hóa cục bộ, Agent bắt buộc phải thực thi công cụ thu thập để tải tệp gốc (PDF/DOCX) trước khi tiến hành phân tích. Nếu không thể tải tự động hoặc tệp không khả dụng trực tuyến, Agent **bắt buộc phải dừng lại** và yêu cầu người dùng cung cấp tệp gốc.

3. **Đóng dấu Xác thực Mật mã (Cryptographic Provenance Stamping):**  
   Mọi tài liệu thu thập từ Internet khi lưu trữ vào hệ thống bắt buộc phải tính toán và lưu kèm mã băm an toàn **SHA-256** của tệp gốc.

---

## 2. Lược Đồ Xuất Xứ (Provenance Metadata Schema)

Mọi tệp tài liệu thu thập từ Internet phải được ghi nhận siêu dữ liệu xuất xứ (Provenance Metadata) vào tệp sidecar `.meta.yaml` hoặc registry tập trung (`.md/extracted_docs/provenance_registry.yaml`):

```yaml
# Provenance Metadata YAML Specification (OKF v2.4 / ADR-0059)
source_url: "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Nghi-dinh-217-2026-ND-CP-quan-ly-hoat-dong-dau-tu-xay-dung-654321.aspx"
retrieved_at: "2026-09-22T03:30:00Z"
sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
acquisition_tool: "TVPLCrawler"  # [read_url_content | TVPLCrawler | chrome_devtools | drive_ingestor]
local_path: ".md/extracted_docs/internet/nghi_dinh_217_2026_nd_cp.pdf"
document_id: "217/2026/NĐ-CP"
title: "Nghị định 217/2026/NĐ-CP về quản lý hoạt động đầu tư xây dựng"
mime_type: "application/pdf"
size_bytes: 1048576
verification_status: "verified"  # [verified | pending_audit | deprecated]
```

### Giải Thích Trường Dữ Liệu:
- `source_url`: URL tuyệt đối trỏ đến trang nguồn chính thức (Công báo, Cổng thông tin Chính phủ, TVPL).
- `retrieved_at`: Thời điểm thu thập theo định dạng chuẩn ISO 8601 UTC.
- `sha256`: Mã băm SHA-256 được tính toán trực tiếp trên luồng nhị phân của tệp đã tải về máy.
- `acquisition_tool`: Tên định danh công cụ đã sử dụng để tải (đáp ứng truy xuất nguồn gốc).
- `local_path`: Đường dẫn tương đối từ gốc repository đến tệp cục bộ lưu trữ bản số hóa gốc.
- `verification_status`: Trạng thái đối soát SHA-256 (`verified` khi mã băm khớp 100% với tệp đĩa).

---

## 3. Phân Tầng & Định Tuyến Công Cụ Thu Thập (Tool Routing Hierarchy)

Để tối ưu hóa hiệu năng, giảm chi phí token và thích ứng với môi trường máy chủ Linux Headless, Agent phải tuân thủ định tuyến ưu tiên:

```
                  ┌────────────────────────────────────────────────┐
                  │          Yêu Cầu Thu Thập Tri Thức             │
                  └───────────────────────┬────────────────────────┘
                                          │
                  ┌───────────────────────▼────────────────────────┐
                  │  Tầng 1: HTTP Direct Stream / Specialized SDK  │
                  │  (TVPLCrawler, read_url_content, DriveIngestor)│
                  └───────────────────────┬────────────────────────┘
                                          │ (Thất bại hoặc bị chặn JS/WAF)
                  ┌───────────────────────▼────────────────────────┐
                  │  Tầng 2: Chromium CDP WebSocket Target         │
                  │  (Port 9222, Persistent Profile, Cloudflare)   │
                  └───────────────────────┬────────────────────────┘
                                          │ (Không thể tự động tải)
                  ┌───────────────────────▼────────────────────────┐
                  │  Tầng 3: Hard Stop & Yêu Cầu Người Dùng        │
                  │  (Yêu cầu cung cấp PDF/DOCX có dấu kiểm định)  │
                  └────────────────────────────────────────────────┘
```

1. **Tầng 1 (Ưu tiên Cao nhất - Headless First):**
   - Sử dụng `read_url_content` cho các trang tài liệu công khai dạng văn bản HTML/Markdown.
   - Sử dụng `TVPLCrawler` (từ package `ccba-legal-intel`) cho các văn bản pháp quy trên Thư Viện Pháp Luật (tự động lấy bản PDF/DOCX có dấu số hóa).
   - Sử dụng `GoogleDriveIngestor` cho tài nguyên nằm trên Google Drive chia sẻ nội bộ.

2. **Tầng 2 (Dự phòng Trực quan - Headless Chrome CDP):**
   - Chỉ kích hoạt `chrome_devtools` hoặc CDP WebSocket target (`http://127.0.0.1:9222`) khi tài liệu nằm sau tường lửa chống bot (Cloudflare Turnstile, ReCAPTCHA) hoặc yêu cầu render JavaScript phức tạp.

3. **Tầng 3 (Dừng An toàn - Hard Completion Safeguard):**
   - Khi cả 2 tầng trên đều không tải được tệp gốc, Agent **nghiêm cấm** tự sinh nội dung giả tạo. Agent phải xuất thông báo rõ ràng:
     `"Không thể tải tài liệu gốc từ Internet. Theo quy chuẩn ADR-0059, vui lòng cung cấp tệp PDF/DOCX chính thức trước khi tiếp tục."`

---

## 4. Cấu Trúc Thư Mục Lưu Trữ Tri Thức Internet

Tất cả tài nguyên thu thập từ Internet bắt buộc phải lưu vào thư mục được phân định rõ ràng trong `.md/extracted_docs/`:

```
.md/extracted_docs/
├── gdrive/                       # Tài nguyên đồng bộ từ Google Drive (GoogleDriveIngestor)
│   ├── gdrive_registry.yaml      # Bảng băm SHA-256 và trạng thái đồng bộ Drive
│   └── *.pdf, *.docx
├── tvpl_downloads/               # Bản gốc DOCX/PDF từ TVPL VIP (TVPLCrawler)
│   ├── *.docx
│   └── *.pdf
└── internet/                     # Tài liệu thu thập từ các nguồn web khác
    ├── provenance_registry.yaml  # Registry xuất xứ tập trung
    └── [slug]/
        ├── document.pdf
        └── metadata.yaml
```

---

## 5. Quy Chuẩn Kiểm Tra Tự Động (Automated Verification Gate)

Trước khi nghiệm thu bất kỳ gói tri thức hoặc bundle nào xuất phát từ nghiên cứu Internet:
1. Chạy lệnh đối soát xuất xứ mật mã:
   ```bash
   python -m ccba_harness verify-patch --preset code
   ```
2. Mọi tệp `.meta.yaml` hoặc `provenance_registry.yaml` phải pass qua kiểm định băm SHA-256 thực tế với hàm `calculate_sha256(local_path)`.
