---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance
  checklists from Vietnamese legal documents.
bundle: _consulting
layer: _consulting
---
# Skill: CCBA Legal Intelligence Crawler & Packager (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent tự động thực hiện quy trình cào dữ liệu từ Thư viện Pháp luật (TVPL) qua Deep Seam **`TVPLCrawler`** ([`packages/ccba-legal-intel`](../../packages/ccba-legal-intel)), phân tích đóng gói thành cấu trúc OKF Bundle lồng nhau, phân rã phụ lục, vá liên kết tương đối và đăng ký văn bản mới vào cơ sở tri thức cục bộ.

---

## 1. Quy chuẩn & Rào cản Kỹ thuật (Technical Guardrails)

### 1.1. Rào cản Bảo mật & Quản lý Thông tin xác thực
*   **Không hardcode credentials**: Đọc thông tin tài khoản TVPL thông qua biến môi trường hệ thống hoặc file `.env` (`TVPL_USERNAME`, `TVPL_PASSWORD`). Báo lỗi nếu thiếu.

### 1.2. Rào cản Đường dẫn Hệ thống (Windows MAX_PATH Prevention)
*   **Giới hạn độ dài Slug**: Để tránh lỗi `FileNotFoundError` khi ghi các tệp phụ lục nằm sâu trên Windows, hàm `sanitize_slug` **bắt buộc** phải giới hạn độ dài slug tối đa là **60 ký tự**.

### 1.3. Quy chuẩn Tích hợp OKF Bundle Lồng nhau (Parent-Child Flat Architecture)
*   **Luật gốc (Parent Law)**: Lưu tại `\.md\legal_docs\<law_slug>\`
*   **Văn bản hướng dẫn (Guiding Decrees/Circulars)**: Lưu phẳng bên trong:
    *   Tệp gốc và markdown: `\.md\legal_docs\<law_slug>\guiding_docs\<guiding_slug>.docx` (và `.md`)
    *   Tệp phụ lục phân tách: `\.md\legal_docs\<law_slug>\guiding_docs\appendices\<guiding_slug>-phu_luc_xx.md`
*   **Đăng ký Registry**: Cập nhật `file_path` và `markdown_path` trong `legal_registry.yaml`.

---

## 2. Ánh xạ Đồ thị Quan hệ Lược đồ (11 nhóm quan hệ)

Khi cào trang Lược đồ (`Tab=LuocDo`), so khớp các tiêu đề mối quan hệ của TVPL:
- `amends_docs`: Văn bản bị sửa đổi bổ sung
- `replaced_docs`: Văn bản bị thay thế
- `referenced_docs`: Văn bản được dẫn chiếu
- `basis_docs`: Văn bản được căn cứ
- `guided_docs`: Văn bản được hướng dẫn
- `consolidated_docs`: Văn bản được hợp nhất
- `guiding_docs`: Văn bản hướng dẫn
- `consolidations`: Văn bản hợp nhất (VBHN)
- `amended_by_docs`: Văn bản sửa đổi bổ sung
- `replaced_by_docs`: Văn bản thay thế
- `related_docs`: Văn bản liên quan cùng nội dung

---

## 3. Hướng dẫn Vận hành Quy trình 5 Bước

1. **Kiểm tra Cấu hình & Môi trường**:
   - Đảm bảo biến môi trường `TVPL_USERNAME` và `TVPL_PASSWORD` đã sẵn sàng trong file `.env`.
   - **Tiêu chí hoàn thành:** Xác nhận tài khoản VIP TVPL sẵn sàng trước khi thực thi cào.

2. **Thu thập Dữ liệu qua Deep Seam (`TVPLCrawler`)**:
   - Kích hoạt Facade `TVPLCrawler` để tải nội dung văn bản và tệp tin đính kèm `.docx` tự động dưới sự bảo vệ của Mutex Lock:
     ```python
     from ccba_legal import TVPLCrawler

     crawler = TVPLCrawler()
     doc = crawler.fetch_document(url_or_id)
     ```
     Hoặc qua CLI:
     ```bash
     python scripts/legal/tvpl_vip_crawler.py "<TVPL_URL>"
     ```
   - **Tiêu chí hoàn thành:** Văn bản HTML/Markdown và tệp đính kèm được tải về thành công vào thư mục đích.

3. **Phân rã Phụ lục & Chuẩn hóa Liên kết**:
   - Kích hoạt module phân tách biểu mẫu phụ lục và gọi `relative-link-patcher` để tự động chuẩn hóa liên kết phụ lục trỏ về `./appendices/`, đồng thời cập nhật mục lục `index.md`.
   - **Tiêu chí hoàn thành:** Toàn bộ phụ lục được phân rã thành tệp riêng và liên kết tương đối trong văn bản chính hoạt động chính xác.

4. **Đăng ký Cục bộ (Local Registry) & Dọn dẹp**:
   - Thêm bản ghi metadata vào `.md/data/legal_registry.yaml`.
   - Cập nhật trạng thái `superseded` cho các văn bản cũ bị thay thế dựa trên quan hệ `replaced_docs`.
   - Ghi nhận đường dẫn tệp gốc vào `.md/data/sources_registry.yaml`.
   - **Tiêu chí hoàn thành:** Các tệp registry được cập nhật đồng bộ và chính xác.

5. **Báo cáo Kết quả**:
   - In ra sơ đồ cây thư mục OKF Bundle đã được tạo và hiển thị tóm tắt metadata văn bản vừa nạp.
   - **Tiêu chí hoàn thành:** Hiển thị cấu trúc OKF Bundle hoàn chỉnh trong tin nhắn phản hồi cho người dùng.
