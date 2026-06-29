> [!WARNING]
> Tài liệu này mang tính chất lịch sử/nghiên cứu cũ.
> Cấu trúc thư mục và các sự kiện (lifecycle events) mô tả trong tài liệu có thể đã thay đổi hoặc khác biệt so với phiên bản Python của CAP hiện tại.

---
# Kế hoạch Tích hợp Chọn lọc Tính năng ClaudeKit Marketing

Kế hoạch này phác thảo cách trích xuất và tích hợp chọn lọc các kỹ năng hữu ích từ `claudekit-marketing` vào dự án `ccba-agent-platform` theo chế độ `--compare`.

---

## 1. Các thành phần sẽ thay đổi (Proposed Changes)

### Thành phần Core & Hooks

#### [NEW] [brand_enforcement.py](file:///D:/GitHubProjects/ccba-agent-platform/scripts/hooks/brand_enforcement.py)
*   **Mục đích**: Một hook chạy ở sự kiện `pre-tool` hoặc `post-tool` kiểm tra các nội dung văn bản (markdown, txt) được tạo ra xem có tuân thủ các quy tắc thương hiệu cốt lõi (ví dụ: viết đúng tên dự án `ccba-agent-platform`, không dùng từ cấm, giữ tông giọng chuyên nghiệp).

#### [NEW] [seo_audit.py](file:///D:/GitHubProjects/ccba-agent-platform/scripts/seo_audit.py)
*   **Mục đích**: Công cụ CLI chạy độc lập hoặc tích hợp để phân tích kỹ thuật SEO của các tệp HTML/Markdown trong dự án (kiểm tra heading `<h1>`, độ dài tiêu đề, mô tả meta, thẻ `alt` của hình ảnh).

---

## 2. Kế hoạch Nghiệm thu (Verification Plan)

### Kiểm thử Tự động (Automated Tests)
*   Chạy thử nghiệm trực tiếp công cụ `seo_audit.py` trên một tệp markdown mẫu trong thư mục `.md/`.
*   Chạy thử nghiệm hook `brand_enforcement.py` với một chuỗi nội dung văn bản không tuân thủ để xác nhận cảnh báo được kích hoạt thành công.

### Kiểm thử Thủ công (Manual Verification)
*   Xác nhận các file mới được đăng ký chính xác trong hệ thống hook của dự án.
