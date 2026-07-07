# Đặc tả Kiến trúc Thiết kế: Tự động đồng bộ pháp lý (Legal Auto-Sync Pipeline)

Tài liệu này lưu trữ các quyết định thiết kế kỹ thuật đã được thống nhất thông qua phiên phản biện (`grilling`) ngày 02/07/2026. Thiết kế này hướng tới việc tự động hóa hoàn toàn quy trình đồng bộ hóa kho tri thức pháp luật xây dựng (VBPL) Việt Nam cục bộ lên Google NotebookLM Cloud RAG.

---

## 1. Điểm kích hoạt & Tổ chức mã nguồn (Trigger & Structure)

1.  **Cầu nối tích hợp (scripts/legal_sync.py):**
    *   Tạo mới một file script chuyên trách tại `scripts/legal_sync.py` đóng vai trò là một **Adapter (Bộ điều hợp)** liên kết:
        *   `ccba_legal.crawler` (tải file tự động bypass captcha/login qua Chrome CDP).
        *   `notebooklm_helper` (gọi API nạp/xóa nguồn trên Cloud).
        *   Tệp registry cục bộ `legal_registry.yaml` và `sources_registry.yaml`.
2.  **Điểm kích hoạt (Trigger Point):**
    *   Tích hợp trực tiếp vào lệnh `/ccba-update-legal-registry` (file workflow tương ứng tại `.agents/workflows/ccba-update-legal-registry.md` sẽ gọi chạy script `scripts/legal_sync.py` qua terminal).

---

## 2. Chiến lược đồng bộ & Đối chiếu trạng thái (State Sync Strategy)

Quá trình đồng bộ sử dụng thuật toán đối chiếu trực tiếp với Cloud tại thời điểm chạy (Real-time Cloud State Check) để tự động phát hiện và sửa chữa lỗi lệch dữ liệu (Self-healing):

1.  **Đối chiếu danh sách nguồn:**
    *   Script gọi API `client.sources.list` để lấy danh sách thực tế của các nguồn đang nằm trên NotebookLM Cloud.
    *   So sánh trực tiếp với danh sách các văn bản có trạng thái `enacted` hoặc `current` trong tệp `legal_registry.yaml` (sau khi tra cứu qua tệp Registry trung gian `sources_registry.yaml`).
2.  **Rẽ nhánh xử lý:**
    *   **Nạp mới (Upload):** Văn bản nào có hiệu lực cục bộ nhưng chưa xuất hiện trên Cloud ➔ Tiến hành nạp mới.
    *   **Xóa bỏ (Superseded):** Văn bản nào đã bị chuyển trạng thái thành `superseded` (hết hiệu lực) hoặc không còn trong registry cục bộ nhưng vẫn đang nằm trên Cloud ➔ Gọi ngay API `delete-source` để xóa khỏi Cloud nhằm tránh nhiễu thông tin RAG và tiết kiệm quota.

---

## 3. Quy trình Tải file & Xử lý Định dạng (Download & Formatting Gate)

1.  **Tải file thông minh:**
    *   Script tự động kiểm tra sự tồn tại của file cục bộ. Nếu thiếu và metadata có thuộc tính `download_url`, script tự động gọi module `ccba_legal.crawler` của package `ccba-legal-intel` để điều khiển Chrome CDP tự động đăng nhập và tải file.
    *   **Fallback:** Nếu lỗi kết nối CDP hoặc gặp tường lửa phức tạp, in ra cảnh báo vàng (Warning) kèm direct link để người dùng tự click tải thủ công bằng tay. Tiến trình lưu trữ metadata khác vẫn được tiếp tục.
2.  **Xử lý định dạng:**
    *   Nếu file tải về có định dạng `.docx`, hệ thống sẽ nạp trực tiếp file `.docx` này lên NotebookLM (Google đọc rất tốt native docx).
    *   Tại local, hệ thống tự động chạy lệnh `/ccba-convert-markdown` để chuyển đổi file sang bản `.md` sạch lưu tại `.md/extracted_docs/` cho con người đọc.

---

## 4. Tùy chọn Nâng cao: Đồng bộ qua Google Drive chung

Hệ thống hỗ trợ luồng nạp gián tiếp qua Google Drive (khi kích hoạt flag `--use-drive`) để quản lý tài liệu tập trung và duy trì liên kết trực tiếp giữa NotebookLM Cloud và kho tài liệu Google Drive của trung tâm CCBA:

1.  **Cấu hình Google Drive đích:**
    *   Thư mục lưu trữ chung của CCBA: `https://drive.google.com/drive/u/0/folders/1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2` (Folder ID: `1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2`).
2.  **Xác thực API bằng Application Default Credentials (ADC):**
    *   Sử dụng thư viện `google-api-python-client` (`googleapiclient.discovery`).
    *   Xác thực thông qua tài khoản Google cá nhân của kỹ sư đã chạy lệnh:
        `gcloud auth application-default login --scopes="https://www.googleapis.com/auth/drive"`
    *   **Bắt lỗi quyền (Insufficient Permission):** Nếu gặp lỗi thiếu scope (lỗi 403), hệ thống in ra cảnh báo đỏ hướng dẫn kỹ sư chạy đúng lệnh cấp quyền trên, đồng thời tự động kích hoạt luồng **Fallback** (nạp file cục bộ trực tiếp lên NotebookLM) để không làm gián đoạn công việc.
3.  **Chuẩn hóa đặt tên tệp tin (Naming Convention):**
    *   Trước khi tải lên Google Drive, tệp tin PDF/DOCX bắt buộc phải được đổi tên tự động theo đúng quy chuẩn đặt tên của CCBA (quy định tại hiến pháp `AGENTS.md`):
        `CCBA_RD_VBPL_NNN_RevXX-ShortName.{ext}`
        *(ví dụ: `CCBA_RD_VBPL_003_Rev00-ND_15_2021.pdf`)*
    *   Định danh này giúp đồng bộ hóa trực quan giữa Registry, Google Drive và NotebookLM.
4.  **Thuật toán chống trùng lặp (Drive Deduplication):**
    *   Trước khi tải lên, script quét thư mục Drive chung để tìm file trùng tên chuẩn hóa:
        *   Nếu file **đã có và không thay đổi**: Bỏ qua upload, lấy luôn `file_id` hiện tại trên Drive để nạp vào NotebookLM.
        *   Nếu file **đã có nhưng thay đổi nội dung (SHA-256 mismatch)**: Gọi API cập nhật đè nội dung lên file cũ (Drive file update) để giữ nguyên `file_id` hoặc xóa file cũ trên Drive rồi upload file mới.
        *   Nếu **chưa có**: Tiến hành upload bình thường và ghi nhận `file_id`.
5.  **Kéo nguồn vào NotebookLM:**
    *   Gọi API của connector:
        `await client.sources.add_drive(notebook_id, file_id=file_id, title=filename, mime_type="application/pdf", wait=True)`
        (đối với DOCX, mime_type sẽ được tự động đổi sang định dạng phù hợp).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
