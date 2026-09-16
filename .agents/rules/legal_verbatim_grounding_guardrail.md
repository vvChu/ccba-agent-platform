# CCBA Legal Verbatim Grounding Guardrail — Cưỡng Chế Nguyên Văn & Chống Ảo Giác Pháp Lý

> **Mã quy tắc**: `RULE_LEGAL_VERBATIM_GROUNDING`  
> **Cấp độ cưỡng chế**: BẮT BUỘC TOÀN CỤC (HARD INVARIANT) — Vi phạm đồng nghĩa với FAILED nhiệm vụ  
> **Phạm vi**: Tất cả AI Agents hoạt động trên CCBA Platform (Hub & Spokes), bao gồm code, fixtures, mock data, tài liệu và tư vấn pháp lý.

---

## 1. Nguyên Tắc Bất Biến Về Tính Nguyên Văn (Strict Verbatim Invariant)

1. **Tuyệt đối cấm tự sáng tác, bịa đặt điều khoản:**  
   AI Agent tuyệt đối không được phép tự phỏng đoán, suy diễn ngữ nghĩa, hay sáng tác câu chữ "giả lập" để gán vào bất kỳ điều khoản, khoản mục nào của văn bản quy phạm pháp luật (VBPL).
2. **Cấm dùng mock data tưởng tượng cho VBPL:**  
   Mọi dữ liệu phục vụ kiểm thử (test fixtures, mock bundles, schemas) khi mang danh một văn bản pháp lý có thật (như Nghị định, Quyết định, Luật, Thông tư, Quy chuẩn) **BẮT BUỘC** phải trích xuất chính xác 100% nguyên văn từ văn bản chính thức của cơ quan nhà nước ban hành, không được tự ý viết nội dung đại khái để "làm mẫu".

---

## 2. Quy Trình Bắt Buộc Thu Thập Văn Bản Gốc (Mandatory Acquisition First Policy)

Khi thực hiện nhiệm vụ liên quan đến một văn bản pháp lý mà tài liệu gốc chưa có sẵn trong thư mục cục bộ (`.md/extracted_docs/` hoặc `legal_docs/`):

1. **Bước 1 — Tự động kích hoạt công cụ tải chính thống:**  
   Agent **BẮT BUỘC** phải gọi công cụ crawler có sẵn trên platform:
   - Module: `ccba_legal.TVPLCrawler` (từ gói `packages/ccba-legal-intel`) hoặc workflow `/ccba-tvpl-vip-crawler`
   - Nguồn dữ liệu: Thư Viện Pháp Luật (`thuvienphapluat.vn`), Cổng TTĐT Chính phủ (`vanban.chinhphu.vn`), hoặc Cổng TTĐT Bộ Xây dựng (`moc.gov.vn`).
   - Tải về tệp DOCX hoặc PDF số chính thức và lưu vào `.md/extracted_docs/`.
2. **Bước 2 — Trích xuất nguyên văn có kiểm chứng:**  
   Sử dụng công cụ bóc tách (`fitz`, `pdfplumber`, `easyocr`, OCR hoặc Multimodal Vision) để chuyển toàn văn sang Markdown chuẩn OKF v2.4 trước khi đưa vào codebase hay cấu hình RAG.
3. **Bước 3 — Thủ tục Dừng khẩn cấp khi thiếu nguồn (Hard Stop on Missing Source):**  
   Nếu hệ thống không thể tự tải văn bản (không có mạng, tài liệu mật, hoặc nguồn không khả dụng), Agent **BẮT BUỘC PHẢI DỪNG LẠI VÀ BÁO CÁO NGƯỜI DÙNG**:
   - Nêu rõ tên và số hiệu văn bản còn thiếu.
   - Yêu cầu người dùng cung cấp tệp văn bản gốc (PDF/DOCX).
   - **CẤM TUYỆT ĐỐI**: Không được vượt rào bằng cách tự bịa ra nội dung giả định để tiếp tục chạy code.

---

## 3. Tiêu Chuẩn Xuất Xứ Mật Mã (Cryptographic Provenance Stamping)

Mọi gói tri thức pháp lý (OKF Bundle) dù là mock test hay dữ liệu sản xuất đều bắt buộc phải được đóng dấu xuất xứ trong `metadata.yaml`:

```yaml
source_assets:
  docx_present: false
  pdf_present: true
  source_file: "702686.pdf" # Tên file gốc tải từ TVPL hoặc do user cung cấp
  pdf_sha256: "d826eaf192b238acd1b465854babc8a884d8e12e2d330ecc4c262ed64eb8767b" # SHA-256 thực tế
  provenance_verified: true
  acquisition_method: "official_gazette_pdf" # "tvpl_crawler" | "official_gazette_pdf" | "manual_upload"
```

---

## 4. Cưỡng Chế Kiểm Định Tự Động (Deterministic Lock & Verification)

1. **Harness CI Gate:** `python -m ccba_harness verify-patch` sẽ xác thực tính hợp lệ của mọi bundle pháp lý mới/sửa đổi.
2. **Grounding Verifier:** Hàm `verify_legal_grounding()` trong `ccba_legal.grounding` sẽ chặn và gắn cờ vi phạm nếu phát hiện nội dung trích dẫn không khớp với `clauses.json` và tệp nguồn đã đóng dấu mật mã.
