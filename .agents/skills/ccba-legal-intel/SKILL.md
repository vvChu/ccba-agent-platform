---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance checklists from Vietnamese legal documents.
---

# Skill: CCBA Legal Intelligence Crawler & Packager (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent tự động thực hiện quy trình kết nối CDP, cào dữ liệu từ Thư viện Pháp luật (TVPL), phân tích đóng gói thành cấu trúc OKF Bundle, phân rã phụ lục, vá đường dẫn tương đối và đăng ký tài liệu mới vào cơ sở tri thức cục bộ.

## Triggers

Kích hoạt kỹ năng này khi:
- Người dùng yêu cầu cào hoặc tải một luật, nghị định, thông tư mới từ Thư viện Pháp luật (TVPL).
- Người dùng sử dụng các từ khóa: `crawl law`, `cào luật`, `đóng gói luật`, `thuvienphapluat`, `TVPL`, `legal checklist`.
- Kích hoạt gián tiếp từ Slash Command `/ccba-legal-intel <URL>`.

---

## Hướng dẫn Vận hành Quy trình 5 Bước

### Bước 1: Tự động khởi chạy & Kiểm tra kết nối Chrome CDP (Cổng 9222)
Trước khi chạy script cào dữ liệu, Agent hoặc script `legal_intelligence.py` sẽ tự động phát hiện và mở trình duyệt Google Chrome ở chế độ debug port 9222:
1. Script tự động chạy Chrome ở port 9222 sử dụng profile `chrome-debug-profile`.
2. Nếu khởi chạy tự động thất bại hoặc không kết nối được (Connection Refused):
   - Hướng dẫn người dùng khởi động Google Chrome thủ công bằng dòng lệnh sau:
     ```bash
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_dev"
     ```
   - Dừng lại và yêu cầu người dùng xác nhận sau khi đã bật trình duyệt trước khi tiếp tục.

### Bước 2: Chạy Script Cào & Đóng gói (Cơ chế Tối ưu hóa Delta-only)
Trước khi chạy lệnh cào, Agent **bắt buộc** phải kiểm tra xem tệp tin và thư mục Luật gốc đã tồn tại cục bộ chưa (được định vị qua cấu hình trong `legal_registry.yaml` hoặc thư mục `.md/legal_docs/<bundle_slug>/<bundle_slug>.md`):

1. **Trường hợp đã tồn tại văn bản gốc**:
   - **Bỏ qua cào Luật chính**: Trừ khi người dùng truyền cờ `--force` hoặc yêu cầu rõ ràng việc ép buộc ghi đè, Agent **không** tải lại và ghi đè văn bản Luật chính để bảo toàn các chỉnh sửa thủ công và chú thích dự án hiện có.
   - **Chỉ cào chênh lệch (Delta guiding docs)**: Agent kiểm duyệt TVPL để tìm kiếm các văn bản hướng dẫn (Nghị định/Thông tư) mới xuất hiện. Chỉ tiến hành cào bổ sung các văn bản hướng dẫn mới chưa tồn tại trong thư mục `guiding_docs/` cục bộ.
2. **Trường hợp chưa tồn tại văn bản gốc hoặc có cờ `--force`**:
   - Thực thi đầy đủ script Python ở gốc thư mục với URL được cung cấp:
     ```bash
     python scripts/legal_intelligence.py --url "<TVPL_URL>" --extract-related --download-source
     ```
   - Chờ script hoàn thành thành công (`Exit Code 0`). Xác nhận thư mục bundle mới đã được sinh ra dưới dạng chữ thường không dấu tại `.md/legal_docs/<bundle_slug>/`.

### Bước 3: Phân rã phụ lục & Hậu xử lý Markdown
1. Thực hiện chạy script phân rã các phụ lục biểu mẫu dài thành từng tệp riêng biệt:
   ```bash
   python scripts/split_appendices.py
   ```
2. Gọi Kỹ năng `relative-link-patcher` để tự động dò tìm và sửa lại toàn bộ liên kết phụ lục lỗi trong văn bản gốc trỏ về thư mục `appendices/`, đồng thời tự động cập nhật tệp mục lục `index.md`.

### Bước 4: Đăng ký cục bộ (Local Registry Registration)
Agent tự động đọc tệp tin `index.md` của bundle mới để lấy metadata và ghi nhận vào hai tệp tin registry:
1. Mở [legal_registry.yaml](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/legal_registry.yaml) và thêm một mục mới ghi nhận thông tin văn bản vừa cào (ID, tiêu đề, trạng thái hiệu lực, danh sách tệp cục bộ).
2. Mở [sources_registry.yaml](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/sources_registry.yaml) và thêm đường dẫn của tệp tin gốc `.docx`/`.pdf` kèm ID Google Drive rỗng (sẽ được cập nhật khi đồng bộ đám mây).

### Bước 5: Báo cáo Kết quả & Cảnh báo pháp lý
Khi kết thúc quy trình, Agent in ra:
- Sơ đồ cấu trúc thư mục của OKF Bundle mới được tạo.
- Dòng Attribution và Disclaimer bắt buộc của CCBA ở cuối phản hồi.

---

## Tiêu chí Hoàn thành (Completion Criteria)
- **Kiểm chứng**: Bundle thư mục mới xuất hiện đầy đủ trong `.md/legal_docs/`, không chứa tệp tin lỗi định dạng.
- **Tính nhất quán**: Tệp chỉ mục `index.md` chứa đầy đủ liên kết và pass qua lệnh kiểm định `validate_docs.py` không có lỗi liên kết.
- **Lưu trữ**: Thông tin tệp tin đã được cập nhật đầy đủ vào `legal_registry.yaml` và `sources_registry.yaml`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
