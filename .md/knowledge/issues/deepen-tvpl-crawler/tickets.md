# Danh sách Tickets: Tái cấu trúc Sâu TVPL VIP Crawler Module

Spec tham chiếu: [spec-deepen-tvpl-crawler.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/specs/spec-deepen-tvpl-crawler.md)

👉 Nguyên tắc: Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) — là những ticket không bị chặn hoặc tất cả blockers của nó đã hoàn thành.

---

## Ticket 01: Thiết lập Seam Interface `LegalDocProvider` & `MockLegalDocProvider`

**Nghiệp vụ cần làm:** Định nghĩa giao diện trừu tượng `LegalDocProvider` và lớp giả lập `MockLegalDocProvider` đọc dữ liệu từ fixture JSON cục bộ. Giúp toàn bộ unit test suite chạy offline độc lập với tốc độ <100ms mà không cần trình duyệt Chrome hay kết nối mạng.

**Bị chặn bởi:** Không có — [x] Đã hoàn thành (Frontier).

- [x] Định nghĩa `LegalDocProvider` abstract interface.
- [x] Triển khai `MockLegalDocProvider` hỗ trợ nạp dữ liệu fixture văn bản pháp lý.
- [x] Viết unit test kiểm chứng `MockLegalDocProvider` trả về `LegalDocument` đúng cấu trúc.

---

## Ticket 02: Triển khai Deep Module `TVPLCrawlerEngine` & Tích hợp `LiveTVPLProvider`

**Nghiệp vụ cần làm:** Xây dựng module `TVPLCrawlerEngine` tự động điều phối `TVPLSessionMutex` (file lock `.md/data/tvpl_vip_session.lock`), kết nối Chrome CDP WebSocket và quy trình 3-tier fallback đằng sau hàm công khai `fetch_doc()`. Bọc toàn bộ quy trình trong `try...finally` để đảm bảo không bao giờ bị dính dơ lock file khi xảy ra ngoại lệ `TVPLCrawlFailedException`.

**Bị chặn bởi:** Ticket 01 — [x] Đã hoàn thành.

- [x] Đóng gói `TVPLSessionMutex` và Chrome CDP WebSocket controller vào `LiveTVPLProvider`.
- [x] Triển khai class `TVPLCrawlerEngine` với hàm duy nhất `fetch_doc(doc_id_or_url)`.
- [x] Xử lý thu hồi kết nối và tự động gọi `mutex.release()` trong khối `finally`.
- [x] Chuẩn hóa ngoại lệ miền `TVPLCrawlFailedException`.

---

## Ticket 03: Chuyển đổi các Call Sites & Viết Integration Tests cho Lock Safety

**Nghiệp vụ cần làm:** Chuyển đổi các điểm gọi cũ (`coordinator.py`, `intake.py`) sang sử dụng `TVPLCrawlerEngine`, đồng thời bổ sung integration tests kiểm chứng tính an toàn thu hồi mutex lock khi bị ngắt kết nối mạng ngẫu nhiên.

**Bị chặn bởi:** Ticket 02.

- [ ] Cập nhật các call sites trong `ccba_legal` sang gọi `engine.fetch_doc()`.
- [ ] Bổ sung test case kiểm chứng tệp `.lock` luôn được giải phóng sau khi cào lỗi hoặc thành công.
- [ ] Chạy lại toàn bộ test suite để đảm bảo không có regression bugs.
