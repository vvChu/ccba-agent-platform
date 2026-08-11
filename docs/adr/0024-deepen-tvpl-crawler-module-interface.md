# ADR 0024: Tái cấu trúc Sâu (Deep Module) cho Phân hệ TVPL VIP Crawler

## Bối cảnh (Context)
Trong quá trình đánh giá kiến trúc codebase `ccba-agent-platform` thông qua kỹ năng `/improve-codebase-architecture`, chúng tôi phát hiện phân hệ `TVPL VIP Crawler` (`packages/ccba-legal-intel/ccba_legal/crawler.py`) có giao diện mỏng (shallow interface). Người dùng khi gọi cào tài liệu phải tự quản lý thủ công `TVPLSessionMutex` (file-based locking), xử lý kết nối Chrome CDP WebSocket, và kích hoạt quy trình `Three-Tier Fallback` (Cache -> Cloud -> CDP). Điều này dẫn đến sự phân tán logic (thiếu locality), nguy cơ kẹt file lock (deadlock), và khó khăn khi viết unit tests mà không mở Chrome thật.

## Quyết định (Decisions)

### 1. Đóng gói Deep Module Seam: `TVPLCrawlerEngine`
* **Quyết định**: Đóng gói toàn bộ độ phức tạp của `TVPLSessionMutex`, Chrome CDP controller và `Three-Tier Fallback` đằng sau một API đơn nhất:
  ```python
  engine = TVPLCrawlerEngine()
  doc = engine.fetch_doc(doc_id_or_url)
  ```
* **Lý do**: Tăng tối đa tính **Leverage** (1 dòng code thay thế 35 dòng boilerplate) và đảm bảo tính **Locality** (tập trung 100% logic quản lý phiên cào tại một nơi).

### 2. Tách lớp Adapter Seam cho Kiểm thử (`LegalDocProvider`)
* **Quyết định**: Áp dụng nguyên lý `/codebase-design`, tách interface `LegalDocProvider` với 2 adapters:
  1. `LiveTVPLProvider`: Sử dụng Chrome CDP thật + 3-Tier Fallback.
  2. `MockLegalDocProvider`: Đọc dữ liệu từ file fixture JSON cục bộ cho các bộ test đơn vị.
* **Lý do**: Giúp unit test suite chạy tức thì dưới 100ms mà không cần phụ thuộc vào trình duyệt Chrome thật hay tài khoản TVPL VIP.

### 3. Tự động Giải phóng Mutex Lock & An toàn Ngoại lệ
* **Quyết định**: Bọc toàn bộ quy trình cào trong `try...finally` để tự động giải phóng `.md/data/tvpl_vip_session.lock` và thu hồi kết nối WebSocket kể cả khi xảy ra sự cố mạng, sau đó ném ra domain exception chuẩn `TVPLCrawlFailedException`.

## Hệ quả (Consequences)
* Bổ sung thuật ngữ `TVPLCrawlerEngine (Deep Seam)` vào `CONTEXT.md`.
* Đơn giản hóa việc gọi cào tài liệu trong các module cấp cao (`coordinator.py`, `intake.py`).
* Đảm bảo 100% an toàn chống lỗi dơ file lock khi cào tài liệu quy mô lớn.
