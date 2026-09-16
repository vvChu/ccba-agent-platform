# 0059. Legal Verbatim Grounding, Zero-Hallucination Invariant, and Cryptographic Provenance Stamping

* **Status:** Accepted
* **Date:** 2026-09-16
* **Deciders:** CCBA Platform Core Team & Lead Engineer
* **Consulted:** ADR 0031 (TVPL Priority), ADR 0035 (Deep Modules), ADR 0038 (OKF v2 Bundle), ADR 0049 (OKF v2.4 Universal Spec), ADR 0050 (Automated Legal Sync), ADR 0058 (Deterministic Hard Completion Lock)

---

## Context & Problem Statement

Trong hệ sinh thái tư vấn xây dựng CCBA, dữ liệu pháp lý (Văn bản Quy phạm Pháp luật - VBPL) là nền tảng tối thượng định đoạt tính hợp pháp của mọi kết quả tư vấn, thẩm tra thiết kế, cấp phép xây dựng và quản lý chi phí đầu tư. Khi mở rộng nền tảng sang quản lý phân cấp hành chính địa phương (Issue #276), hệ thống đã phát hiện và phải giải quyết 3 rủi ro cốt tử:

1. **Rủi Ro Ảo Giác Pháp Lý & Tự Bịa Đặt Dữ Liệu Thử Nghiệm (Legal Hallucination & Synthetic Bias):**
   - Trong quá trình lập trình hoặc tạo dữ liệu kiểm thử (mock fixtures), Agent có xu hướng tự biên soạn các điều khoản pháp lý tóm lược, suy diễn hoặc giả định ngôn từ khi chưa có văn bản nguồn trong tay.
   - Các mock fixtures sai lệch này sau đó vô tình được đưa vào cơ sở dữ liệu học tập hoặc RAG search, khiến Agent đưa ra các trích dẫn pháp lý không có thật trên thực tế (false citation).
2. **Thiếu Cơ Chế Cưỡng Chế Thu Thập Tệp Gốc (Missing Acquisition-First Enforcement):**
   - Khi một văn bản chưa có tệp số hóa cục bộ, quy trình trước đây cho phép Agent tiếp tục phân tích dựa trên phỏng đoán ngữ cảnh thay vì dừng lại để thực hiện tải hoặc yêu cầu người dùng cung cấp tài liệu nguồn chính thức.
3. **Thiếu Bằng Chứng Xác Thực Mật Mã Về Xuất Xứ (Lack of Cryptographic Provenance):**
   - Các bundle tri thức pháp luật không gắn chặt với bản quét số (scan PDF có dấu đỏ hoặc bản số hóa chính thức từ Công báo / Thư Viện Pháp Luật), khiến hệ thống không thể đối soát ngược (traceability) xem từng câu chữ trong Markdown có khớp 100% với văn bản được ban hành hay không.

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành **HUB-ADR-0059** thiết lập các quy tắc bất biến thuộc Hiến pháp Layer 1 của nền tảng:

### 1. Bất Biến Không Bịa Đặt (Zero-Hallucination & Strict Verbatim Grounding Invariant)
- **Quy tắc tuyệt đối:** Nghiêm cấm Agent tự suy diễn, phỏng đoán, sáng tác câu chữ, hoặc tạo mock data giả định cho bất kỳ điều khoản VBPL nào trong toàn bộ mã nguồn, kiểm thử, fixtures và tài liệu.
- Mọi nội dung điều khoản trích dẫn bắt buộc phải phản ánh **nguyên văn 100%** từ văn bản ban hành chính thức.

### 2. Chính Sách Thu Thập Bắt Buộc Trước Tiên (Mandatory Acquisition First Policy)
Khi hệ thống hoặc Agent cần xử lý một văn bản pháp lý mà chưa có tệp gốc cục bộ:
1. **Bước 1:** Bắt buộc sử dụng công cụ hiện có (`TVPLCrawler` từ gói `ccba_legal` hoặc các cổng thông tin điện tử chính thống) để tải văn bản gốc chính thức (PDF/DOCX).
2. **Bước 2 (Chốt chặn dừng bắt buộc):** Nếu không thể tự động tải hoặc văn bản không khả dụng trực tuyến, Agent **BẮT BUỘC PHẢI DỪNG LẠI** và yêu cầu người dùng cung cấp tệp gốc. Tuyệt đối không được "vượt rào" bằng cách tự biên soạn mock bundle tạm thời.

### 3. Đóng Dấu Xác Thực Mật Mã (Cryptographic Provenance Stamping)
- Mọi bundle pháp lý (kể cả test fixtures hay production bundles) bắt buộc phải khai báo trường `source_assets` trong `metadata.yaml` ghi nhận:
  - Tên tệp nguồn (ví dụ: `702686.pdf`).
  - Mã băm an toàn **SHA-256** của tệp gốc (`pdf_sha256`).
  - Phương thức thu thập (`acquisition_method: manual_upload` hoặc `tvpl_crawler_vip`).
- Hàm thẩm định `validate_bundle_provenance()` trong package `ccba-legal-intel` tự động đối soát mã băm của tệp nguồn với khai báo trong metadata trước khi cho phép bundle nạp vào Registry hoặc chỉ mục RAG.

### 4. Quản Trị Biến Động Địa Phương & Đồ Thị Hành Chính Theo Trục Thời Gian (Temporal Local Jurisdictions)
- Tích hợp chuẩn **ISO 3166-2:VN** vào tiêu chuẩn OKF v2.4 (Open Knowledge Format) để phân vùng tri thức: `jurisdiction: VN-HN`, `VN-HCM`, `VN-DN`...
- Xây dựng đồ thị hành chính thời gian (`administrative_ontology.yaml`) mô hình hóa các đợt sáp nhập/chia tách tỉnh (như Hà Tây $\rightarrow$ Hà Nội 2008), bãi bỏ cấp huyện từ 01/07/2025, và cơ chế chuyển giao cơ quan kế thừa pháp lý (`LEGAL_SUCCESSOR`).
- Cưỡng chế cơ chế RAG Geofencing: Chỉ tìm kiếm trong vùng giao thoa giữa `National Core (VN)` và `Target Local Jurisdiction`, ngăn chặn ô nhiễm tri thức giữa các tỉnh thành.

---

## Consequences

### Tích Cực (Positive)
- **Độ tin cậy pháp lý tuyệt đối (100% Grounded):** Triệt tiêu hoàn toàn nguy cơ Agent đưa ra ý kiến tư vấn pháp lý sai lệch hoặc căn cứ vào điều khoản không có thật.
- **Minh bạch xuất xứ (End-to-End Cryptographic Auditability):** Mọi bundle pháp lý đều có thể chứng minh nguồn gốc xuất xứ thông qua mã băm SHA-256 đối soát trực tiếp với bản gốc có dấu đỏ.
- **Khả năng mở rộng cho 63 tỉnh thành:** Cho phép hệ sinh thái mở rộng kho tri thức địa phương một cách an toàn mà không làm loãng hoặc xung đột với kho tri thức cấp Trung ương.

### Tiêu Cực & Thách Thức (Trade-offs & Mitigations)
- **Tăng chi phí chuẩn bị dữ liệu:** Việc bắt buộc phải có tệp gốc có thể làm chậm quá trình tạo test fixture ban đầu. *Giải pháp:* Thiết lập cơ chế tải tự động qua VIP TVPL Crawler và bộ fixture chuẩn mực được tái sử dụng qua các bài test.
