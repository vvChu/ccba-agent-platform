---
proposal_id: "2026-08-23_tvpl_crawler_security_and_rate_limiting"
type: "tool"
name: "tvpl-crawler-security-and-rate-limiting"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-08-23"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Kiểm định"
---

# RFC: TVPLCrawler Security Guardrails & Adaptive Rate Limiter

## 1. Bối Cảnh & Vấn Đề (Context & Problem Statement)
Trong quá trình kiểm định mã nguồn hệ thống Spoke `ccba-legal-knowledge` và Hub package `packages/ccba-legal-intel`, chúng tôi phát hiện 2 vấn đề quan trọng liên quan đến việc kết nối và khai thác dữ liệu từ Thư Viện Pháp Luật (TVPL):
1. **Lỗ hổng Fallback Credentials Hardcode:** Hàm `get_tvpl_credentials()` trong `ccba_legal.crawler` chứa giá trị fallback tài khoản và mật khẩu mặc định dạng plaintext (`"vuvanchu119"`, `"ccba@ibst"`), vi phạm nghiêm trọng quy tắc bảo mật hệ sinh thái CCBA (Global Rule #3).
2. **Thiếu cơ chế Giới hạn Tần suất & Nhận diện Bot (Anti-Detection):** Toàn bộ các thao tác cào và điều khiển Chrome qua DevTools Protocol (CDP) sử dụng khoảng dừng cố định (`time.sleep(N)`), tạo ra nhịp điệu truy cập đều đặn bất thường dễ bị hệ thống Cloudflare WAF / Anti-Bot của TVPL phát hiện và hạn chế tài khoản VIP.

## 2. Giải Pháp Đề Xuất (Proposed Changes)

### 2.1. Triệt tiêu 100% Fallback Credentials Hardcode
- Nâng cấp hàm `get_tvpl_credentials()`: Chỉ đọc thông tin từ biến môi trường `TVPL_USERNAME` / `TVPL_PASSWORD` hoặc file `.env` cục bộ.
- Báo lỗi `OSError` rõ ràng khi không tìm thấy credentials, tuyệt đối không trả về chuỗi xác thực mặc định.

### 2.2. Bổ sung `sleep_with_jitter()`
- Triển khai hàm `sleep_with_jitter(base_sec, jitter_min, jitter_max)` áp dụng phân phối Uniform Jitter ngẫu nhiên vào các điểm navigate, login, wait readyState và download trigger.

### 2.3. Xây dựng Deep Seam `TVPLRateLimiter`
- Thiết lập ngưỡng bảo vệ phiên: `max_requests_per_session = 10`, `min_request_interval_sec = 3.0`.
- Tự động cưỡng chế giãn cách giữa các lượt request liên tiếp và chặn dừng kịp thời khi chạm ngưỡng phiên, ghi log chi tiết vào `.md/data/tvpl_session_audit.log`.

## 3. Bộ Kiểm Thử (Test Suite)
- Bổ sung `packages/ccba-legal-intel/tests/test_crawler_rate_limiting.py` kiểm thử 5 ca:
  - Ném `OSError` khi thiếu biến môi trường.
  - Lấy thành công credentials từ biến môi trường.
  - Tính ngẫu nhiên và biên độ của `sleep_with_jitter`.
  - Tự động điều chỉnh giãn cách `min_request_interval_sec`.
  - Ném `TVPLCrawlFailedException` khi vượt `max_requests_per_session`.

## 4. Kết Quả Nghiệm Thu (Verification)
- $13/13$ unit tests trên Hub (`test_crawler_rate_limiting.py`, `test_tvpl_crawler_facade.py`, `test_cleaners_packager.py`) đạt trạng thái **`PASSED`**.
- $100\%$ tuân thủ kiểm định tĩnh `ruff check` và định dạng `ruff format`.
