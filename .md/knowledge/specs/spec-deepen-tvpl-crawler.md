# Spec: Deepen TVPL VIP Crawler Module Interface

Status: ready-for-agent

## Problem Statement

Hiện tại, các caller trong hệ thống CCBA Agent Services Platform khi cần tải văn bản quy phạm pháp luật TVPL VIP phải tự phối hợp thủ công giữa `TVPLSessionMutex` (file-based locking), kết nối Chrome CDP WebSocket, và kích hoạt `Three-Tier Fallback`. Việc để lộ chi tiết triển khai này tạo ra giao diện mỏng (shallow interface), gây phân tán logic (thiếu locality), nguy cơ đứt gãy kết nối làm kẹt file lock (deadlock), và gây khó khăn lớn khi viết Unit Tests vì luôn yêu cầu môi trường Chrome CDP thực tế.

## Solution

Đóng gói toàn bộ độ phức tạp quản lý phiên cào, mutex lock, thu hồi kết nối CDP và 3-tier fallback đằng sau một **Deep Module Seam** duy nhất: `TVPLCrawlerEngine`. Client chỉ cần tương tác qua một hàm giao diện đơn nhất `fetch_doc(doc_id_or_url)`. Tách biệt tầng cung cấp dữ liệu qua seam `LegalDocProvider` hỗ trợ cả môi trường live (`LiveTVPLProvider`) và môi trường test mock (`MockLegalDocProvider`).

## User Stories

1. As a downstream agent developer, I want to call a single method `engine.fetch_doc("VBHN-105-2025")` without worrying about Chrome CDP connection setup, so that I can focus on building business workflows.
2. As a system maintainer, I want `TVPLCrawlerEngine` to automatically handle session mutex locking and unlocking via `try...finally`, so that background crawling jobs never leave orphan `.lock` files that cause deadlocks.
3. As a test suite engineer, I want to inject a `MockLegalDocProvider` into `TVPLCrawlerEngine`, so that unit tests run in less than 100ms without opening Chrome browsers or requiring active TVPL VIP subscriptions.
4. As an error monitor, I want the crawler to catch raw WebSocket and CDP connection errors and raise a clean `TVPLCrawlFailedException`, so that error reporting and retry alerts are consistent.

## Implementation Decisions

- **Single Entry Point Module**: Tạo class `TVPLCrawlerEngine` đóng gói toàn bộ logic khởi tạo `ChromeCDP`, quản lý `TVPLSessionMutex` và thực thi quy trình 3-tier fallback.
- **Seam Abstraction (`LegalDocProvider`)**: Đỉnh nghĩa giao diện trừu tượng `LegalDocProvider` với 2 triển khai:
  - `LiveTVPLProvider`: Chạy cào thật qua Chrome CDP & S3/Cache fallback.
  - `MockLegalDocProvider`: Trả về dữ liệu từ fixture JSON phục vụ kiểm thử.
- **Mutex Auto-Release Guarantee**: Bọc toàn bộ quy trình cào trong khối `try...finally` để đảm bảo `TVPLSessionMutex.release()` luôn được gọi trước khi kết thúc tiến trình.
- **Domain Exception Handling**: Chuẩn hóa toàn bộ ngoại lệ cấp thấp (WebSocket, HTTP 5xx, CDP timeout) thành `TVPLCrawlFailedException`.
- **Tham chiếu Kiến trúc**: Tuân thủ quy định ghi nhận tại `CONTEXT.md` và `docs/adr/0024-deepen-tvpl-crawler-module-interface.md`.

## Testing Decisions

- **Test Surface**: Chỉ kiểm thử thông qua giao diện công khai `TVPLCrawlerEngine.fetch_doc()`, không kiểm thử trực tiếp các hàm nội bộ bên dưới.
- **Mock Provider Integration**: Sử dụng `MockLegalDocProvider` trong toàn bộ unit test suite để kiểm tra tính đúng đắn của logic mà không có side-effects lên trình duyệt hay mạng.
- **Locking Safety Verification**: Viết integration test mô phỏng trường hợp cào bị ném exception ngẫu nhiên để xác minh tệp lock `.md/data/tvpl_vip_session.lock` luôn được giải phóng hoàn tất.
- **Prior Art**: Tham khảo mẫu test seam tại `tests/test_link_patcher.py` và `tests/test_seo_auditor.py`.

## Out of Scope

- Thay đổi cấu trúc dữ liệu schema của `LegalDocument`.
- Tối ưu hóa lại thuật toán bóc tách HTML của TVPL parser.
- Sửa đổi cơ chế đăng nhập tài khoản VIP trên giao diện Web TVPL.

## Further Notes

- Spec này chuyển giao trực tiếp cho `/to-tickets` để sinh danh sách các tracer-bullet tickets cho `/implement`.
