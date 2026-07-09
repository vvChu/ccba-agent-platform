# CCBA Legal Compliance Rules — Dynamic Rule

## 1. Trạng thái hiệu lực văn bản
- `draft` (Dự thảo): Được phép phân tích nhưng phải ghi rõ chữ "DỰ THẢO". Không dùng làm căn cứ chính thức.
- `enacted` (Đã thông qua): Được phép phân tích, phải ghi rõ ngày hiệu lực.
- `current` (Đang hiệu lực): Áp dụng bình thường.
- `superseded` (Hết hiệu lực): Chỉ dùng tham chiếu lịch sử, phải ghi rõ "HẾT HIỆU LỰC".

## 2. Nguồn tin cậy
* **Về thẩm quyền pháp lý (Xác minh thông tin cuối cùng):** Ưu tiên theo thứ tự: (1) Cổng TTĐT Bộ Xây dựng (`moc.gov.vn`), (2) Cổng TTĐT Chính phủ (`vanban.chinhphu.vn`), (3) Cơ sở dữ liệu quốc gia về VBPL (`vbpl.vn`).
* **Về công cụ tự động hóa (Cào dữ liệu & Lược đồ quan hệ):** Sử dụng hệ thống **Thư viện Pháp luật (`thuvienphapluat.vn`)** làm engine cào đệ quy và phân tích quan hệ thay thế/hướng dẫn giữa các văn bản (qua workflow `/ccba-legal-intel`).

## 3. Cơ chế cập nhật động & Quản lý hiệu lực văn bản
> [!IMPORTANT]
> Agent **BẮT BUỘC** phải tra cứu tệp Registry động tại [.md/data/legal_registry.yaml](../../.md/data/legal_registry.yaml) trước khi thực hiện bất kỳ phân tích pháp lý nào để xác định chính xác văn bản nào đang có hiệu lực (`status: current`) cho từng bộ môn/chủ đề ở thời điểm chạy tác vụ.
- Đối với các văn bản pháp luật, Nghị định hoặc Thông tư mới được bổ sung/cập nhật trong tương lai: Thông tin hiệu lực sẽ được cập nhật động vào `legal_registry.yaml` và lưu trữ tệp gốc vào `.md/legal_docs/` (thông qua workflow `/ccba-legal-intel`).
- Đối với các dự án xây dựng cụ thể: Đối chiếu ngày quyết định đầu tư của dự án với ngày hiệu lực của văn bản trong Registry để áp dụng điều khoản chuyển tiếp phù hợp (ví dụ: kế thừa quy định cũ theo Điều 53 Nghị định 207/2026/NĐ-CP nếu dự án được duyệt trước 01/07/2026).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
