# ADR 0050: Automated Legal Sync Pipeline & Mock Data Isolation for Spokes

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-08-31)

## 2. Bối Cảnh (Context)
Tại các Spoke Triển khai Dự án (`vvc_working_space`, `2026-04 DH Viet Nhat`), khi AI Agent thực hiện các tác vụ tư vấn pháp lý và xây dựng tài liệu dự án theo Luật Xây dựng năm 2025 (Luật số 135/2025/QH15), Luật PCCC & CNCH năm 2024 (Luật số 55/2024/QH15) và các Nghị định hướng dẫn mới (NĐ 105/2025, NĐ 207/2026, NĐ 217/2026), xuất hiện 4 điểm nghẽn:
1. **Thiếu cơ chế phân phối dữ liệu tri thức 1-lệnh:** Spoke dự án không lưu trữ toàn bộ kho văn bản pháp luật OKF v2.4 (kho này thuộc về Spoke Tri thức Gốc `ccba-legal-knowledge` và Cloud Legal Vault) và thiếu công cụ đồng bộ tự động dữ liệu AST / OKF v2.4 về môi trường làm việc của Spoke.
2. **Nhiễm độc không gian tri thức do dữ liệu Mock/Demo:** Các script kiểm thử nền tảng (như `demo_vbhn_delta_patch.py`) ghi file trực tiếp vào `.md/` (ví dụ `VBHN_ND06_2026_demo.md`), khiến Agent tại Spoke quét trúng và hiểu nhầm là văn bản pháp luật hiện hành.
3. **Thiếu chuẩn hóa trạng thái hiệu lực động:** `legal_registry.yaml` chưa có hệ thống enum vòng đời tường minh (`ACTIVE`, `SUPERSEDED`, `PARTIALLY_AMENDED`, `PENDING_EFFECTIVE`), khiến Agent khó nhận biết văn bản đã hết hiệu lực (như Luật 50/2014, NĐ 15/2021) và không có cơ chế cảnh báo tự động khi tra cứu.
4. **Thiếu High-Level Python API:** Các Spoke phải phụ thuộc vào các đường dẫn file nội bộ thay vì gọi trực tiếp từ package `ccba_legal`.

## 3. Quyết Định Thiết Kế (Decisions)

Hệ thống thiết lập tiêu chuẩn phân phối và quản trị vòng đời pháp lý thông qua **4 Trụ Cột Thiết Kế**:

### A. Cơ Chế Phân Phối Dữ Liệu 2 Tầng (Hybrid Two-Tier Legal Sync)
- Mở rộng Deep Seam `LegalSyncEngine` và cung cấp lệnh CLI:
  ```bash
  python -m ccba_legal sync --pull-latest [-o legal_docs] [--doc <doc_id>]
  ```
- **Tier 1 (Ưu tiên):** Tự động quét tìm thư mục `ccba-legal-knowledge/legal_docs` cục bộ lân cận trên máy tính. Nếu có $\rightarrow$ Sao chép nguyên tử dữ liệu OKF v2.4 bundles đạt chuẩn vào Spoke (tốc độ miligiây, 100% Offline).
- **Tier 2 (Dự phòng):** Nếu không tìm thấy thư mục tri thức cục bộ $\rightarrow$ Tự động kéo bản phát hành chính thức từ Google Drive Legal Vault (`1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2`).

### B. Chiến Lược Hòa Trộn Danh Mục Bảo Toàn (Non-Destructive Additive Registry Merge)
- Khi đồng bộ về Spoke, hệ thống tự động sao lưu `.md/backups/legal_registry.yaml.bak_<timestamp>`.
- Giữ lại 100% các tài liệu nội bộ, ghi chú riêng (`notes`) và trường tùy biến mà Spoke tự định nghĩa.
- Cập nhật các trường vòng đời SSOT (`status`, `effective_date`, `supersedes`, `superseded_by`, `bundle_path`) cho các văn bản chuẩn quốc gia.

### C. Chuẩn Hóa Vòng Đời `LegalDocStatus` & Banner Cảnh Báo Tự Động
- Ban hành Enum vòng đời chuẩn hóa trong `ccba_legal.models`:
  - `ACTIVE`: Đang có hiệu lực đầy đủ.
  - `SUPERSEDED`: Đã hết hiệu lực toàn bộ (kèm `superseded_by`, `superseded_date`).
  - `PARTIALLY_AMENDED`: Đã bị sửa đổi, bổ sung một phần (kèm `amended_by`).
  - `PENDING_EFFECTIVE`: Đã ban hành nhưng chưa đến ngày có hiệu lực.
  - `DRAFT`: Bản dự thảo đang lấy ý kiến.
- Khi tra cứu (`ccba_legal.query()`, `ccba_legal.get_lifecycle()`):
  - Tự động gắn Banner Cảnh báo nổi bật `⚠️ [CẢNH BÁO PHÁP LÝ]` khi văn bản đã hết hiệu lực.
  - Tự động gợi ý văn bản thay thế hiện hành (`suggested_replacement`) vào payload kết quả.

### D. Rào Chắn Cách Ly Dữ Liệu Thử Nghiệm (Mock Data Isolation Guard)
- Toàn bộ dữ liệu demo/test của `demo_vbhn_delta_patch.py` và unit tests được chuyển vào thư mục riêng biệt: `packages/ccba-legal-intel/tests/fixtures/mock_vbhn/` và hỗ trợ cờ `--output`.
- Thiết lập bài kiểm thử tự động `test_mock_data_isolation.py` trong CI Gate: Quét và khẳng định $100\%$ không có tệp tin nào chứa tiền tố/hậu tố `demo`, `mock`, `fake` xuất hiện tại `.md/` hoặc `.md/legal_docs/`.

## 4. Hệ Quả & Lợi Ích (Consequences)
- **Bảo Vệ Ngữ Cảnh Tuyệt Đối (Zero Context Poisoning):** Loại bỏ hoàn toàn nguy cơ Agent nhầm lẫn văn bản giả định hay điều khoản đã hết hiệu lực.
- **Vận Hành 1-Lệnh Đơn Giản:** Kỹ sư tại mọi Spoke chỉ cần gõ 1 lệnh `python -m ccba_legal sync --pull-latest` để có trọn bộ tri thức pháp lý mới nhất.
- **Độc Lập & Sẵn Sàng Ngoại Tuyến:** Tận dụng tối đa kho `ccba-legal-knowledge` trên máy mà không tiêu tốn băng thông hay phụ thuộc mạng internet.
