---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance checklists from Vietnamese legal documents.
---

# Skill: CCBA Legal Intelligence Crawler & Packager (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent tự động thực hiện quy trình kết nối Chrome CDP, cào dữ liệu từ Thư viện Pháp luật (TVPL), phân tích đóng gói thành cấu trúc OKF Bundle lồng nhau, phân rã phụ lục, vá liên kết tương đối và đăng ký văn bản mới vào cơ sở tri thức cục bộ.

---

## 1. Quy chuẩn & Rào cản Kỹ thuật (Technical Guardrails)

Để đảm bảo crawler chạy ổn định, bảo mật và tương thích tốt trên môi trường Windows/Linux, Agent bắt buộc phải tuân thủ nghiêm ngặt các quy tắc sau:

### 1.1. Rào cản Bảo mật & Quản lý Thông tin xác thực
*   **Không hardcode credentials**: Tuyệt đối không lưu tài khoản và mật khẩu trực tiếp trong mã nguồn.
*   **Cơ chế đọc cấu hình**: Đọc thông tin tài khoản TVPL thông qua biến môi trường hệ thống hoặc file `.env`:
    *   `TVPL_USERNAME`: Tài khoản đăng nhập TVPL.
    *   `TVPL_PASSWORD`: Mật khẩu đăng nhập TVPL.
    *   *Fallback*: Chỉ sử dụng tài khoản mặc định hệ thống (`vuvanchu119` / `ccba@ibst`) khi các biến môi trường trên không được khai báo.

### 1.2. Rào cản Đường dẫn Hệ thống (Windows MAX_PATH Prevention)
*   **Giới hạn độ dài Slug**: Để tránh lỗi `FileNotFoundError` khi ghi các tệp phụ lục nằm sâu trên hệ thống Windows (giới hạn 260 ký tự), hàm `sanitize_slug` của packager **bắt buộc** phải giới hạn độ dài slug tối đa là **60 ký tự**.
*   **Cắt chuỗi an toàn**:
    ```python
    if len(text) > 60:
        text = text[:60].rstrip("_")
    ```

### 1.3. Quy chuẩn Tích hợp OKF Bundle Lồng nhau (Parent-Child Flat Architecture)
Văn bản pháp lý xây dựng Việt Nam được tổ chức theo mối quan hệ Phân cấp (Luật $\rightarrow$ Nghị định $\rightarrow$ Thông tư).
*   **Luật gốc (Parent Law)**: Được đóng gói thành thư mục OKF độc lập tại gốc thư mục:
    `\.md\legal_docs\<law_slug>\`
*   **Văn bản hướng dẫn (Guiding Decrees/Circulars)**: Không tạo thư mục bundle cấp cao nhất riêng biệt. Tất cả các văn bản hướng dẫn ban hành kèm theo Luật **bắt buộc** phải được lưu trữ phẳng bên trong:
    *   Tệp tin gốc và markdown: `\.md\legal_docs\<law_slug>\guiding_docs\<guiding_slug>.docx` (và `.md`)
    *   Tệp phụ lục phân tách: `\.md\legal_docs\<law_slug>\guiding_docs\appendices\<guiding_slug>-phu_luc_xx.md`
*   **Đăng ký Registry**: Cập nhật chính xác `file_path` và `markdown_path` trong `legal_registry.yaml` và `sources_registry.yaml` trỏ về đúng thư mục lồng này.

---

## 2. Cấu trúc DOM & Thuật toán Trích xuất Lược đồ TVPL

Khi thực hiện cào dữ liệu, Agent cần áp dụng các selector và thuật toán chuẩn hóa sau:

### 2.1. Cấu trúc DOM Nội dung Văn bản
*   **Tiêu đề**: `document.title`
*   **Nội dung chính**: `#divContentDoc` (ưu tiên hàng đầu), `.content1`, `.contentDoc` (fallback).
*   **Khử nhiễu**: Luôn gọi `cdp.handle_login()` và `cdp.close_popup()` trước khi trích xuất text để tránh bị các popup che khuất hoặc giới hạn toàn văn văn bản trực tuyến.
*   **Sửa lỗi Race Condition**: Sau lệnh `Page.navigate`, bắt buộc phải đợi `1.5 giây` để trình duyệt thực sự chuyển trạng thái tải trang trước khi gọi lệnh `wait_ready()`.

### 2.2. Ánh xạ Đồ thị Quan hệ Lược đồ (11 nhóm quan hệ)
Khi cào trang Lược đồ (`Tab=LuocDo` hoặc `#tab4`), so khớp các tiêu đề mối quan hệ của TVPL theo bảng sau:

| Tiêu đề tiếng Việt trên TVPL | Khóa ánh xạ của CCBA | Ý nghĩa |
| :--- | :--- | :--- |
| Văn bản bị sửa đổi bổ sung | `amends_docs` | Văn bản hiện tại bổ sung/sửa đổi cho các văn bản này |
| Văn bản bị thay thế | `replaced_docs` | Văn bản hiện tại thay thế cho các văn bản cũ này |
| Văn bản được dẫn chiếu | `referenced_docs` | Các văn bản được trích dẫn nội dung bên trong |
| Văn bản được căn cứ | `basis_docs` | Căn cứ pháp lý để ban hành văn bản hiện tại |
| Văn bản được hướng dẫn | `guided_docs` | Các văn bản cấp trên được văn bản này hướng dẫn |
| Văn bản được hợp nhất | `consolidated_docs` | Các văn bản thành phần tạo nên văn bản hợp nhất này |
| Văn bản hướng dẫn | `guiding_docs` | Các Nghị định, Thông tư chi tiết hóa văn bản này |
| Văn bản hợp nhất | `consolidations` | Bản Văn bản Hợp nhất (VBHN) chính thức chứa văn bản này |
| Văn bản sửa đổi bổ sung | `amended_by_docs` | Các văn bản mới sửa đổi/bổ sung một phần văn bản này |
| Văn bản thay thế | `replaced_by_docs` | Văn bản mới thay thế hoàn toàn văn bản này |
| Văn bản liên quan cùng nội dung | `related_docs` | Các văn bản liên quan cùng nội dung |

*   **Chuẩn hóa so khớp**: Do TVPL có thể dùng tiêu đề có hoặc không có dấu phẩy (ví dụ: *Văn bản bị sửa đổi, bổ sung*), JavaScript kiểm tra **bắt buộc** phải loại bỏ toàn bộ dấu phẩy và khoảng trắng thừa trước khi so khớp:
    ```javascript
    let txt = (el.innerText || "").replace(/,/g, '').replace(/\s+/g, ' ').trim();
    return txt.startsWith(key);
    ```

---

## 3. Hướng dẫn Vận hành Quy trình 5 Bước

### Bước 1: Kiểm tra kết nối Chrome CDP (Cổng 9222)
1. Tự động kiểm tra và mở trình duyệt Google Chrome ở chế độ debug port 9222.
2. Nếu thất bại, yêu cầu người dùng khởi động thủ công:
   ```bash
   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"
   ```

### Bước 2: Chạy Quy trình Cào dữ liệu chênh lệch (Delta-only)
-  **Tra cứu trước (Pre-crawl scoping)**: Đối chiếu URL hoặc số hiệu văn bản cần cào với `legal_registry.yaml`.
-  **Rẽ nhánh thực thi**:
    *   **Trường hợp đã tồn tại văn bản gốc**: Bỏ qua cào văn bản chính. Chỉ cào bổ sung các văn bản hướng dẫn/sửa đổi mới ban hành xuất hiện trên trang Lược đồ chưa có trong `guiding_docs/`.
    *   **Trường hợp cào mới hoàn toàn**: Chạy lệnh cào đầy đủ:
        ```bash
        python scripts/legal_intelligence.py --url "<TVPL_URL>" --extract-related --download-source
        ```
-  **Tải tệp Docx**: Chạy ngầm tiến trình giám sát thư mục `Downloads` để bắt file `.crdownload` và tự động di dời về đúng thư mục bundle đích.

### Bước 3: Phân rã phụ lục & Vá liên kết
1. Chạy script phân rã các biểu mẫu đính kèm:
   ```bash
   python scripts/split_appendices.py
   ```
2. Gọi Kỹ năng `relative-link-patcher` để tự động dò tìm và chuẩn hóa liên kết phụ lục lỗi trong tệp Markdown chính trỏ về thư mục `appendices/`, đồng thời tự động cập nhật tệp mục lục `index.md`.

### Bước 4: Đăng ký cục bộ (Local Registry) & Dọn dẹp
-  Thêm bản ghi metadata (ID, tiêu đề, ngày ban hành/hiệu lực, trạng thái...) vào [legal_registry.yaml](../../../.md/knowledge/legal_registry.yaml).
-  Đồng bộ hóa file `legal_registry.yaml` sang thư mục tài nguyên của kỹ năng [.agents/skills/legal-document-tracker/resources/](../legal-document-tracker/resources/).
-  Tính toán SHA-256 của tệp gốc `.docx` và đăng ký đường dẫn vật lý vào [sources_registry.yaml](../../../.md/knowledge/sources_registry.yaml).
-  **Dọn dẹp rác lồng nhau**: Xóa bỏ các thư mục rác tạm thời phát sinh do lỗi cào hoặc redirect lồng dưới `guiding_docs/` (ví dụ: `guiding_docs/extracted_docs` hoặc `guiding_docs/legal_docs`).

### Bước 5: Báo cáo kết quả
In ra sơ đồ cấu trúc OKF Bundle đã được tích hợp phẳng và các registry được cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
